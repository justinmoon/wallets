import json

from os.path import isfile
from io import BytesIO
from random import randint

from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey
from bedrock.helper import sha256
from bedrock.hd import HDPublicKey
from bedrock.helper import encode_varstr

from rpc import WalletRPC, sat_to_btc

import ser

class Wallet:

    filename = "wallet.json"

    def __init__(self, accounts, export_size):
        self.accounts = accounts
        self.export_size = export_size

    @classmethod
    def create(cls, account_name, export_size=100):  # artificially low for testing
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        accounts = {}
        wallet = cls(accounts, export_size)
        wallet.register_account(account_name)
        return wallet

    def serialize(self):
        from copy import deepcopy
        accounts = deepcopy(self.accounts)
        for account in accounts.values():
            print(account)
            account['xpub'] = account['xpub'].xpub()
        dict = {
            'accounts': accounts,
            'export_size': self.export_size,
        }
        return json.dumps(dict, indent=4)

    def save(self):
        with open(self.filename, 'w') as f:
            data = self.serialize()
            f.write(data)

    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        for account_name in data['accounts'].keys():
            xpub_stream = BytesIO(data['accounts'][account_name]['xpub'].encode())
            data['accounts'][account_name]['xpub'] = HDPublicKey.parse(xpub_stream)
        return cls(**data)

    @classmethod
    def open(cls):
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            wallet = cls.deserialize(raw_json)
            # load associated Bitcoin Core watch-only wallets
            for account_name in wallet.accounts.keys():
                WalletRPC('').load_wallet(account_name)
            return wallet

    def register_account(self, account_name):
        assert account_name not in self.accounts, 'account already registered'
        account_number = len(self.accounts)
        xpub_str = ser.xpub(f"m/44'/1'/{account_number}'")
        xpub = HDPublicKey.parse(BytesIO(xpub_str.encode()))
        account = {
            'account_number': account_number,
            'xpub': xpub,
            # FIXME
            'receiving_index': 0,
            'change_index': 0,
        }
        self.accounts[account_name] = account
        # create watch-only Bitcoin Core wallet
        WalletRPC('').create_watchonly_wallet(account_name)
        # export first chunk of receiving & change addresses
        self.bitcoind_export(account_name, True)
        self.bitcoind_export(account_name, False)
        self.save()

    def descriptor(self, account_name, change):
        account_xpub = self.accounts[account_name]['xpub'].xpub()
        change = int(change)
        descriptor = f"pkh({account_xpub}/{change}/*)"
        print(descriptor)
        return descriptor

    def bitcoind_export(self, account_name, change):
        account = self.accounts[account_name]
        descriptor = self.descriptor(account_name, change)
        address_index = account['change_index'] if change else account['receiving_index']
        export_range = (address_index, address_index + self.export_size)
        WalletRPC(account_name).export(descriptor, export_range, change)

    def derive_pubkey(self, account_name, change, address_index):
        account = self.accounts[account_name]
        account_xpub = account['xpub']
        change_number = int(change)
        path = f"m/{change_number}/{address_index}"
        return account_xpub.traverse(path.encode()), path

    def pubkeys(self, account_name):
        keys = []
        account = self.accounts[account_name]
        # receiving addresses
        for address_index in range(account['receiving_index']):
            key, path = self.derive_pubkey(account_name, False, address_index)
            keys.append((key, path))
        # change addresses
        for address_index in range(account['change_index']):
            key, path = self.derive_pubkey(account_name, True, address_index)
            keys.append((key, path))
        return keys

    def lookup_pubkey(self, account_name, address):
        for pubkey, path in self.pubkeys(account_name):
            if pubkey.point.address(testnet=True) == address:
                return pubkey, path
        return None, None

    def addresses(self, account_name):
        return [pubkey.point.address(testnet=True) for key, path in self.pubkeys(account_name)]

    def consume_address(self, account_name, change):
        account = self.accounts[account_name]
        if change:
            address_index = account['change_index']
            if account['change_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
            account['change_index'] += 1
        else:
            address_index = account['receiving_index']
            if account['receiving_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
            account['receiving_index'] += 1
        pubkey, path = self.derive_pubkey(account_name, change, address_index)
        self.save()
        return pubkey.point.address(testnet=True)

    def balance(self, account_name):
        return WalletRPC(account_name).get_balance()

    def unspent(self, account_name):
        return WalletRPC(account_name).get_unspent()

    def transactions(self, account_name):
        return WalletRPC(account_name).get_transactions()

    def send(self, account_name, address, amount, fee):
        rpc = WalletRPC(account_name)

        # create unfunded transaction
        tx_ins = []
        tx_outs = [
            {address: sat_to_btc(amount)},
        ]
        rawtx = rpc.create_raw_transaction(tx_ins, tx_outs)
        
        # fund it
        change_address = self.consume_address(account_name, True)
        fundedtx = rpc.fund_raw_transaction(rawtx, change_address)

        # input metadata
        input_meta = []
        decoded = rpc.rpc().decoderawtransaction(fundedtx)
        for tx_in in decoded['vin']:
            print('iterate input')
            tx_id = tx_in['txid']
            tx_index = tx_in['vout']
            prev_tx = rpc.rpc().getrawtransaction(tx_id, True)
            script_pubkey = encode_varstr(bytes.fromhex(prev_tx['vout'][tx_index]['scriptPubKey']['hex'])).hex()
            input_address = prev_tx['vout'][tx_index]['scriptPubKey']['addresses'][0]
            pubkey, path = self.lookup_pubkey(account_name, input_address)
            account_number = self.accounts[account_name]['account_number']
            derivation_path = f"m/44'/1'/{account_number}'/{path[2:]}"
            print('PATH', derivation_path)
            input_meta = [{'script_pubkey': script_pubkey, 'derivation_path': derivation_path}]

        # output metadata
        output_meta = []
        for tx_out in decoded['vout']:
            print('iterate output')
            address = tx_out['scriptPubKey']['addresses'][0]
            pubkey, path = self.lookup_pubkey(account_name, address)
            if path is None:
                output_meta.append({'change': False})
            else:
                account_number = self.accounts[account_name]['account_number']
                derivation_path = f"m/44'/1'/{account_number}" + path[1:]  # skip "m"
                output_meta.append({'change': True, 'derivation_path': derivation_path})
                
        # send to device 
        # TODO: handle failure
        print('sending to device')
        signed = ser.sign(fundedtx, input_meta, output_meta)

        # broadcast
        return rpc.broadcast(signed)
