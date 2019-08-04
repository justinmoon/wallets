from os.path import isfile
from pickle import load, dump
from random import randint
from io import BytesIO

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.helper import decode_base58, sha256
from bedrock.script import p2pkh_script
from bedrock.hd import HDPrivateKey

from rpc import *  # FIXME

class HDWallet:

    filename = "hd_rpc.pickle"
    export_chunk = 100

    def __init__(self, master_key, accounts):
        self.master_key = master_key
        self.accounts = accounts

    @classmethod
    def create(cls):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        mnemonic, master_key = HDPrivateKey.generate(testnet=True)
        accounts = {
            'default': {
                'bip32_prefix': "m/84'/1'/0'",
                'next_index': 0,
            }
        }
        wallet = cls(master_key, accounts)
        wallet.save()
        load_watchonly() # FIXME
        export(master_key, 0, 0, wallet.export_chunk)
        return mnemonic, wallet

    @classmethod
    def open(self):
        load_watchonly()
        with open(self.filename, 'rb') as f:
            return load(f)

    def save(self):
        with open(self.filename, 'wb') as f:
            dump(self, f)

    def register_account(self, name):
        account_number = len(self.accounts)
        account = {
            'bip32_prefix': f"m/84'/1'/{account_number}'",
            'next_index': 0,
        }
        self.accounts[name] = account
        # FIXME: watchonly export
        self.save()

    def balance(self):
        return get_balance()

    def unspent(self, account):
        return get_unspent()

    def transactions(self, account):
        return get_transactions()

    def path(self, account, index):
        path = account['bip32_prefix'] + '/0/' + str(index)
        return path.encode()

    def consume_address(self, account):
        account = self.accounts[account]
        path = self.path(account, account['next_index'])
        key = self.master_key.traverse(path)
        account['next_index'] += 1
        # FIXME: watchonly export here if we're crossing a chunk
        self.save()
        return key.pub.point.address(testnet=True)

    def keys(self, account):
        keys = []
        for index in range(account['next_index']):
            keys.append(self.master_key.traverse(self.path(account, index)))
        return keys

    def lookup_key(self, account, address):
        keys = self.keys(account)
        for key in keys:
            if key.pub.point.address(testnet=True) == address:
                return key.private_key

    def send(self, address, amount, fee, account):
        # create unfunded transaction
        tx_ins = []
        tx_outs = [
            {address: "{0:.8f}".format(sat_to_btc(amount))},
        ]
        rawtx = create_raw_transaction(tx_ins, tx_outs)
        
        # fund it
        change_address = self.consume_address(account)
        fundedtx = fund_raw_transaction(rawtx, change_address)

        # sign
        tx = Tx.parse(BytesIO(bytes.fromhex(fundedtx)), testnet=True)
        for i, tx_in in enumerate(tx.tx_ins):
            address = get_address_for_outpoint(tx_in.prev_tx.hex(), tx_in.prev_index)
            _account = self.accounts[account]  # FIXME
            private_key = self.lookup_key(_account, address)
            assert tx.sign_input(i, private_key)
            print(f'signed {i}')
        
        # broadcast
        signedtx = tx.serialize().hex()
        return broadcast(signedtx)
