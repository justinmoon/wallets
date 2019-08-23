import json

from os.path import isfile
from io import BytesIO
from random import randint

from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey
from bedrock.helper import sha256
from bedrock.hd import HDPrivateKey

from rpc_final import WalletRPC, sat_to_btc

class Wallet:

    filename = "wallet.json"

    def __init__(self, master_key, accounts, export_size):
        self.master_key = master_key
        self.accounts = accounts
        self.export_size = export_size

    @classmethod
    def create(cls, account_name, export_size=10):  # artificially low for testing
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        mnemonic, master_key = HDPrivateKey.generate(testnet=True)
        accounts = {}
        wallet = cls(master_key, accounts, export_size)
        wallet.register_account(account_name)
        return mnemonic, wallet

    def serialize(self):
        dict = {
            'master_key': self.master_key.serialize().hex(),
            'accounts': self.accounts,
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
        master_key_stream = BytesIO(bytes.fromhex(data['master_key']))
        data['master_key'] = HDPrivateKey.parse(master_key_stream)
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
        account = {
            'account_number': account_number,
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
        account_number = self.accounts[account_name]['account_number']
        account_path = f"m/44'/1'/{account_number}'".encode()
        account_xpub = self.master_key.traverse(account_path).xpub()
        change = int(change)
        descriptor = f"pkh({account_xpub}/{change}/*)"
        return descriptor

    def bitcoind_export(self, account_name, change):
        account = self.accounts[account_name]
        descriptor = self.descriptor(account_name, change)
        address_index = account['change_index'] if change else account['receiving_index']
        export_range = (address_index, address_index + self.export_size)
        WalletRPC(account_name).export(descriptor, export_range, change)

    def derive_key(self, account_name, change, address_index):
        account = self.accounts[account_name]
        account_number = account['account_number']
        change_number = int(change)
        path_bytes = f"m/44'/1'/{account_number}'/{change_number}/{address_index}".encode()
        return self.master_key.traverse(path_bytes)

    def keys(self, account_name):
        keys = []
        account = self.accounts[account_name]
        # receiving addresses
        for address_index in range(account['receiving_index']):
            key = self.derive_key(account_name, False, address_index)
            keys.append(key)
        # change addresses
        for address_index in range(account['change_index']):
            key = self.derive_key(account_name, True, address_index)
            keys.append(key)
        return keys

    def lookup_key(self, account_name, address):
        for key in self.keys(account_name):
            if key.pub.point.address(testnet=True) == address:
                return key

    def addresses(self, account_name):
        return [key.pub.point.address(testnet=True) for key in self.keys(account_name)]

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
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)

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

        # sign
        tx = Tx.parse(BytesIO(bytes.fromhex(fundedtx)), testnet=True)
        for index, tx_in in enumerate(tx.tx_ins):
            output_address = rpc.get_address_for_outpoint(tx_in.prev_tx.hex(), tx_in.prev_index)
            hd_private_key = self.lookup_key(account_name, output_address)
            assert tx.sign_input(index, hd_private_key.private_key)
        
        # broadcast
        rawtx = tx.serialize().hex()
        return rpc.broadcast(rawtx)
