from os.path import isfile
from pickle import load, dump
from random import randint

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.helper import decode_base58
from bedrock.script import p2pkh_script

from bitpay import get_balance, get_unspent, broadcast, get_full_transactions

class KeyPool:

    def __init__(self, n, keys, index):
        self.n = n
        self.keys = keys
        self.index = index

    @classmethod
    def create(cls, n):
        keypool = cls(n, [], 0)
        keypool.fill()
        return keypool

    def fill(self):
        '''Generate N new private keys and add them to keypool'''
        for i in range(self.n):
            secret = randint(1, N)
            key = PrivateKey(secret)
            self.keys.append(key)

    def address(self):
        '''generate next address've run out'''
        # refill keypool if it's empty
        if self.index >= len(self.keys):
            self.fill()
        # fetch private key and increment index
        key = self.keys[self.index]
        self.index += 1
        # return testnet address
        return key.point.address(testnet=True)

    # FIXME: use or remove
    def lookup_key(self, address):
        for key in self.keys:
            if key.point.address(testnet=True) == address:
                return key

    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys]

class Wallet:

    filename = "wallet.pickle"

    def __init__(self, receiving_keypool, change_keypool):
        self.receiving_keypool = receiving_keypool
        self.change_keypool = change_keypool

    @classmethod
    def create(cls, n):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        receiving_keypool = KeyPool.create(n)
        change_keypool = KeyPool.create(n)
        return cls(receiving_keypool, change_keypool)

    @classmethod
    def load(self):
        with open(self.filename, 'rb') as f:
            return load(f)

    def save(self):
        with open(self.filename, 'wb') as f:
            dump(self, f)

    def balance(self):
        balance = 0
        for address in self.receiving_keypool.addresses():
            balance += get_balance(address)
        for address in self.change_keypool.addresses():
            balance += get_balance(address)
        return balance

    def unspent(self):
        unspent = []
        all_keys = self.receiving_keypool.keys + self.change_keypool.keys
        for key in all_keys:
            address = key.point.address(testnet=True)
            for u in get_unspent(address):
                unspent.append((u, key))
        return unspent

    def transactions(self):
        '''retrieves all transactions'''
        transactions = []
        for address in self.receiving_keypool.addresses():
            transactions.extend(get_full_transactions(address))
        for address in self.change_keypool.addresses():
            transactions.extend(get_full_transactions(address))
        return transactions

    def receiving_address(self):
        address = self.receiving_keypool.address()
        self.save()
        return address

    def change_address(self):
        address = self.change_keypool.address()
        self.save()
        return address

    def send(self, address, amount, fee):
        # collect inputs
        unspent_w_keys = self.unspent()
        tx_ins = []
        input_sum = 0
        for utxo, key in unspent_w_keys:
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
        change_output = construct_tx_out(self.change_address(), change_amount)
        tx_outs = [send_output, change_output]

        # construct transaction
        tx = Tx(1, tx_ins, tx_outs, 0, True)

        # sign
        for i in range(len(tx_ins)):
            utxo, private_key = unspent_w_keys[i]
            assert tx.sign_input(i, private_key, utxo.script_pubkey)
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

