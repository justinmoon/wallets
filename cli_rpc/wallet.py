import json
import logging

from os.path import isfile
from io import BytesIO
from random import randint

from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey
from bedrock.helper import sha256
from bedrock.hd import HDPrivateKey

from rpc import get_balance, get_unspent, get_transactions, broadcast, export, load_watchonly, get_address_for_outpoint, sat_to_btc, create_raw_transaction, fund_raw_transaction  # FIXME

logger = logging.getLogger(__name__)

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
        load_watchonly()
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            return cls.deserialize(raw_json)

    def register_account(self, account_name):
        assert account_name not in self.accounts, 'account already registered'
        account_number = len(self.accounts)
        account = {
            'account_number': account_number,
            'receiving_index': 0,
            'change_index': 0,
        }
        self.accounts[account_name] = account
        load_watchonly()
        self.bitcoind_export(account_name, True)
        self.bitcoind_export(account_name, False)
        self.save()

    def descriptor(self, account_name, change):
        account_number = self.accounts[account_name]['account_number']
        origin_path = f"m/44'/1'/{account_number}'"
        xpub = self.master_key.traverse(origin_path.encode()).xpub()
        change = int(change)
        path_suffix = f"/{change}/*"
        inner = f'{xpub}{path_suffix}'
        descriptor = f"pkh({inner})"
        return descriptor

    def bitcoind_export(self, account_name, change):
        account = self.accounts[account_name]
        descriptor = self.descriptor(account_name, change)
        index = account['change_index'] if change else account['receiving_index']
        export_range = (index, index + self.export_size)
        export(descriptor, export_range, change)

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
            account['change_index'] += 1
            # this is an off-by-one. we're exporting before we've actually generated this new index ...
            if account['change_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
        else:
            address_index = account['receiving_index']
            account['receiving_index'] += 1
            if account['receiving_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)

    def balance(self, account_name):
        return get_balance()  # FIXME: pass a 'wallet_name' / 'account_name' variable to rpc ...

    def unspent(self, account_name):
        return get_unspent()

    def transactions(self, account_name):
        return get_transactions()

    def send(self, account_name, address, amount, fee):
        # create unfunded transaction
        tx_ins = []
        tx_outs = [
            {address: sat_to_btc(amount)},
        ]
        rawtx = create_raw_transaction(tx_ins, tx_outs)
        
        # fund it
        change_address = self.consume_address(account_name, True)
        fundedtx = fund_raw_transaction(rawtx, change_address)

        # sign
        tx = Tx.parse(BytesIO(bytes.fromhex(fundedtx)), testnet=True)
        for index, tx_in in enumerate(tx.tx_ins):
            output_address = get_address_for_outpoint(tx_in.prev_tx.hex(), tx_in.prev_index)
            print(output_address)
            hd_private_key = self.lookup_key(account_name, output_address)
            assert tx.sign_input(index, hd_private_key.private_key)
        
        # broadcast
        rawtx = tx.serialize().hex()
        return broadcast(rawtx)
