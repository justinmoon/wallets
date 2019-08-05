'''
- Make a "simple wallet" which doesn't have a keypool
- We should print "private keys generated. backup now!"
- Perhaps bedrock needs a PrivateKey.generate() classmethod?
- Add more logging statements
'''
from os.path import isfile
from pickle import load, dump
from random import randint

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.helper import decode_base58
from bedrock.script import address_to_script_pubkey

from services import get_balance, get_unspent, get_transactions, broadcast

class KeyPool:

    def __init__(self, size, keys, index):
        self.size = size
        self.keys = keys
        self.index = index

    @classmethod
    def create(cls, size):
        keypool = cls(size, [], 0)
        keypool.fill()
        return keypool

    def fill(self):
        '''Generate N new private keys and add them to keypool'''
        for i in range(self.size):
            secret = randint(1, N)
            key = PrivateKey(secret)
            self.keys.append(key)

    def consume_address(self):
        '''generate next address've run out'''
        # refill keypool if it's empty
        if self.index >= len(self.keys):
            self.fill()
        # fetch private key and increment index
        key = self.keys[self.index]
        self.index += 1
        # return testnet address
        return key.point.address(testnet=True)

    def lookup_key(self, address):
        for key in self.keys:
            if key.point.address(testnet=True) == address:
                return key

    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys]

class KeyPoolWallet:  # FIXME

    filename = "keypool.pickle"  # FIXME

    def __init__(self, keypool):
        self.keypool = keypool

    @classmethod
    def create(cls, keypool_size):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        keypool = KeyPool.create(keypool_size)
        wallet = cls(keypool)
        wallet.save()
        return wallet

    @classmethod
    def open(self):
        with open(self.filename, 'rb') as f:
            return load(f)

    def save(self):
        with open(self.filename, 'wb') as f:
            dump(self, f)

    def addresses(self):
        return self.keypool.addresses()

    def consume_address(self):
        address = self.keypool.consume_address()
        self.save()
        return address

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
            private_key = self.keypool.lookup_key(utxo['address'])
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
