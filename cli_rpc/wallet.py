import json

from os.path import isfile
from io import BytesIO
from random import randint

from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey
from bedrock.helper import sha256
from bedrock.hd import HDPrivateKey

from services import get_balance, get_unspent, get_transactions, broadcast

class Wallet:

    filename = "wallet.json"

    def __init__(self, master_key, accounts):
        self.master_key = master_key
        self.accounts = accounts

    @classmethod
    def create(cls, account_name):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        mnemonic, master_key = HDPrivateKey.generate(testnet=True)
        accounts = {}
        wallet = cls(master_key, accounts)
        wallet.register_account(account_name)
        return mnemonic, wallet

    def serialize(self):
        dict = {
            'master_key': self.master_key.serialize().hex(),
            'accounts': self.accounts,
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
        self.save()

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
        # TODO
        account = self.accounts[account_name]
        if change:
            address_index = account['change_index']
            account['change_index'] += 1
        else:
            address_index = account['receiving_index']
            account['receiving_index'] += 1
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)

    def balance(self, account_name):
        return get_balance(self.addresses(account_name))

    def unspent(self, account_name):
        return get_unspent(self.addresses(account_name))

    def transactions(self, account_name):
        return get_transactions(self.addresses(account_name))

    def send(self, account_name, address, amount, fee):
        # collect inputs and private keys needed to sign these inputs
        unspent = self.unspent(account_name)
        tx_ins = []
        private_keys = []
        input_sum = 0
        for utxo in unspent:
            input_sum += utxo['amount']
            tx_in = TxIn(utxo['prev_tx'], utxo['prev_index'])
            tx_ins.append(tx_in)
            hd_private_key = self.lookup_key(account_name, utxo['address'])
            private_keys.append(hd_private_key.private_key)
            # stop once we have enough inputs to transfer "amount"
            if input_sum >= amount + fee:
                break

        # make sure we have enough
        assert input_sum >= amount + fee, 'Insufficient funds'

        # construct outputs
        send_script_pubkey = address_to_script_pubkey(address)
        send_output = TxOut(script_pubkey=send_script_pubkey, amount=amount)
        change_amount = input_sum - amount - fee
        change_script_pubkey = address_to_script_pubkey(self.consume_address(account_name, True))
        change_output = TxOut(script_pubkey=change_script_pubkey, amount=change_amount)
        tx_outs = [send_output, change_output]

        # construct transaction
        tx = Tx(1, tx_ins, tx_outs, 0, True)

        # sign
        for index, private_key in enumerate(private_keys):
            assert tx.sign_input(index, private_key)
        
        # broadcast
        rawtx = tx.serialize().hex()
        return broadcast(rawtx)
