'''
- We should print "private keys generated. backup now!"
- Perhaps bedrock needs a PrivateKey.generate() classmethod?
- Add more logging statements
'''
import json

from os.path import isfile
from random import randint

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey

from services import get_balance, get_unspent, get_transactions, broadcast

class Wallet:

    filename = "wallet.json"

    def __init__(self, keys):
        self.keys = keys

    @classmethod
    def create(cls):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        keys = []
        wallet = cls(keys)
        wallet.save()
        return wallet

    def serialize(self):
        dict = {
            'secrets': [key.secret for key in self.keys],
        }
        return json.dumps(dict, indent=4)

    def save(self):
        with open(self.filename, 'w') as f:
            data = self.serialize()
            f.write(data)

    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        return cls([PrivateKey(secret) for secret in data['secrets']])

    @classmethod
    def open(cls):
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            return cls.deserialize(raw_json)

    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys]

    def lookup_key(self, address):
        for key in self.keys:
            if key.point.address(testnet=True) == address:
                return key

    def generate_key(self):
        secret = randint(1, N)
        key = PrivateKey(secret)
        self.keys.append(key)
        self.save()
        return key

    def consume_address(self):
        key = self.generate_key()
        return key.point.address(testnet=True)

    def balance(self):
        return get_balance(self.addresses())

    def unspent(self):
        return get_unspent(self.addresses())

    def transactions(self):
        return get_transactions(self.addresses())

    def send(self, address, amount, fee):
        # collect inputs and private keys needed to sign these inputs
        unspent = self.unspent()
        tx_ins = []
        private_keys = []
        input_sum = 0
        for utxo in unspent:
            input_sum += utxo['amount']
            tx_in = TxIn(utxo['prev_tx'], utxo['prev_index'])
            tx_ins.append(tx_in)
            private_key = self.lookup_key(utxo['address'])
            private_keys.append(private_key)
            # stop once we have enough inputs to transfer "amount"
            if input_sum >= amount + fee:
                break

        # make sure we have enough
        assert input_sum >= amount + fee, 'Insufficient funds'

        # construct outputs
        send_script_pubkey = address_to_script_pubkey(address)
        send_output = TxOut(script_pubkey=send_script_pubkey, amount=amount)
        change_amount = input_sum - amount - fee
        change_script_pubkey = address_to_script_pubkey(self.consume_address())
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
