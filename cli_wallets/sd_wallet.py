from os.path import isfile
from pickle import load, dump
from random import randint

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.helper import decode_base58, sha256
from bedrock.script import p2pkh_script

from bitpay import get_balance, get_unspent, broadcast, get_transaction

class SDWallet:

    filename = "sd.pickle"

    def __init__(self, secret, index):
        self.secret = secret
        self.index = index

    @classmethod
    def create(cls):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        secret = randint(1, N)
        index = 0
        wallet = cls(secret, index)
        wallet.save()
        return wallet

    @classmethod
    def open(self):
        with open(self.filename, 'rb') as f:
            return load(f)

    def save(self):
        with open(self.filename, 'wb') as f:
            dump(self, f)

    def child_key(self, index):
        secret_bytes = self.secret.to_bytes(32, 'big')
        for _ in range(index):
            secret_bytes = sha256(secret_bytes)
        child_secret = int.from_bytes(secret_bytes, 'big')
        return PrivateKey(child_secret)

    def balance(self):
        balance = 0
        for address in self.addresses():
            balance += get_balance(address)
        return balance

    def unspent(self):
        unspent = []
        for address in self.addresses():
            unspent.extend(get_unspent(address))
        return unspent

    def transactions(self):
        transactions = []
        for address in self.addresses():
            transactions.extend(get_transaction(address))
        return transactions

    def keys(self):
        keys = []
        for index in range(self.index):
            keys.append(self.child_key(index))
        return keys

    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys()]

    def consume_address(self):
        next_key = self.child_key(self.index)
        self.index += 1
        self.save()
        return next_key.point.address(testnet=True)

    def send(self, address, amount, fee):
        # collect inputs
        unspent = self.unspent()
        tx_ins = []
        input_sum = 0
        for utxo, key in unspent:
            input_sum += utxo.amount
            tx_in = TxIn(utxo.tx_id, utxo.index)
            tx_ins.append(tx_in)
            # stop once we have enough inputs
            if input_sum >= amount + fee:
                break

        # make sure we have enough
        assert input_sum >= amount + fee, 'Insufficient funds'

        # construct outputs
        send_output = construct_tx_out(address, amount)
        change_amount = input_sum - amount - fee
        change_output = construct_tx_out(self.consume_address(), change_amount)
        tx_outs = [send_output, change_output]

        # construct transaction
        tx = Tx(1, tx_ins, tx_outs, 0, True)

        # sign
        for i in range(len(tx_ins)):
            utxo = unspent[i]
            address = utxo.script_pubkey.address(testnet=True)
            private_key = self.keypool.lookup_key(address)
            assert tx.sign_input(i, private_key)
            print(f'signed {i}')
        
        # broadcast
        rawtx = tx.serialize().hex()
        return broadcast(rawtx)

def construct_tx_out(address, amount):
    h160 = decode_base58(address)
    script = p2pkh_script(h160)
    return TxOut(amount=amount, script_pubkey=script)

def test_keypool():
    size = 2
    keypool = KeyPool.create(size)

    # there are 3 keys initially
    assert len(keypool.keys) == size

    # there are 3 keys after consuming first 3 addresses
    for i in range(size):
        address = keypool.address()
        assert len(keypool.keys) == size

    # there are 6 keys after consuming 4th address
    address = keypool.address()
    assert len(keypool.keys) == size * 2

# def test_wallet():
    # size = 2
    # # check that it saved when keypool grew
    # loaded_keypool = Wallet.load()
    # original_secrets = [key.secret for key in keypool]
    # loaded_secrets = [key.secret for key in loaded_keypool]
    # assert original_keypool == loaded_secrets

