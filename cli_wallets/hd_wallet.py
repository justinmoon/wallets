from os.path import isfile
from pickle import load, dump
from random import randint

from bedrock.ecc import N, PrivateKey
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.helper import decode_base58, sha256
from bedrock.script import p2pkh_script
from bedrock.hd import HDPrivateKey

from bitpay import get_balance, get_unspent, broadcast, get_transaction

class HDWallet:

    filename = "hd.pickle"

    def __init__(self, master_key, accounts):
        self.master_key = master_key
        self.accounts = accounts

    @classmethod
    def create(cls):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        # FIXME: do something with mnemonic ...
        mnemonic, master_key = HDPrivateKey.generate()
        accounts = {
            'default': {
                'bip32_prefix': "m/84'/1'/0'",
                'next_index': 0,
            }
        }
        wallet = cls(master_key, accounts)
        wallet.save()
        return wallet

    @classmethod
    def open(self):
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
        self.save()

    def balance(self):
        balance = 0
        for address in self.addresses():
            balance += get_balance(address)
        return balance

    def unspent(self, account):
        unspent = []
        for address in self.addresses(account):
            unspent.extend(get_unspent(address))
        return unspent

    def transactions(self, account):
        transactions = []
        for address in self.addresses(account):
            transactions.extend(get_transaction(address))
        return transactions

    def path(self, account, index):
        path = account['bip32_prefix'] + '/0/' + str(index)
        return path.encode()

    def keys(self, account):
        keys = []
        for index in range(account['next_index']):
            keys.append(self.master_key.traverse(self.path(account, index)))
        return keys

    def addresses(self, account):
        account = self.accounts[account]
        return [key.pub.point.address(testnet=True) for key in self.keys(account)]

    def consume_address(self, account):
        account = self.accounts[account]
        path = self.path(account, account['next_index'])
        key = self.master_key.traverse(path)
        account['next_index'] += 1
        self.save()
        return key.pub.point.address(testnet=True)

    def lookup_key(self, account, address):
        keys = self.keys(account)
        for key in keys:
            if key.pub.point.address(testnet=True) == address:
                return key.private_key

    def send(self, address, amount, fee, account):
        # collect inputs
        unspent = self.unspent(account)
        tx_ins = []
        input_sum = 0
        for utxo in unspent:
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
        change_output = construct_tx_out(self.consume_address(account), change_amount)
        tx_outs = [send_output, change_output]

        # construct transaction
        tx = Tx(1, tx_ins, tx_outs, 0, True)

        # sign
        for i in range(len(tx_ins)):
            utxo = unspent[i]
            address = utxo.script_pubkey.address(testnet=True)
            account = self.accounts[account]  # FIXME
            private_key = self.lookup_key(account, address)
            assert tx.sign_input(i, private_key)
            print(f'signed {i}')
        
        # broadcast
        rawtx = tx.serialize().hex()
        return broadcast(rawtx)

# FIXME: this is weird
def construct_tx_out(address, amount):
    h160 = decode_base58(address)
    script = p2pkh_script(h160)
    return TxOut(amount=amount, script_pubkey=script)
