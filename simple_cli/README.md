# Simple CLI Wallet

## Introduction

A few pieces go into building a bitcoin wallet:
1. Dealing with Private keys
2. Connecting to the Bitcoin network

We're going to build a series of wallets that explore a few different ways to accomplish both of these wallet engineering components. We'll start with the simplest approach for each part, then explore different private key strategies, and then explore a few bitcoin network strategies.

For these exercises, we will us my "bedrock" library, which is based on the library from Jimmy Song's Programming Bitcoin book.

## Setup

Create a virtual environment in the `wallets` directory:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Generating Private Keys

Private keys are 256 bit integers in the range (1, 115792089237316195423570985008687907852837564279074904382605163141518161494337). This upper bound can be imported from `bedrock.ecc.N`

To generate a private key we can use you computer's random number generator which can be accessed using Python's `random.randint` function:

```
>>> from random import randint
>>> from bedrock.ecc import N, PrivateKey
>>> secret = randint(1, N)
>>> print(secret)
>>> private_key = PrivateKey(secret)
>>> print(private_key)
```

## Generating Addresses

Once we have a private key, we're able to use it's associated public key (sometimes called a "point" because it's simply a pair of numbers like the (x, y) points you studied in algebra).

```
>>> address = private_key.point.address(testnet=True)
>>> print(address)
```

At this point we could fund this address and create a bitcoin UTXO controlled by `private_key`. But once we still need a way to store the private key so that it can be accessed after we close our REPL.

To do this, let's start building a `Wallet` class which knows how to save and load itself from disk.

## `Wallet` Class

### Constructor

To start with, our wallet class just contains a collection of `PrivateKey` instances. Put the following code in a file called `wallet.py`:

```python
class Wallet:

    def __init__(self, keys):
        self.keys = keys
```

### Serialization & IO

Now, let's write a few methods to save the wallet to disk. We'll save the state of the wallet as JSON. Since python's `json` module won't know how to serialize our custom `PrivateKey` class, we'll extract the list of `PrivateKey.secret` integers which the `json` module can serialize.

```python
import json

...

class Wallet:

    filename = 'wallet.json'

    ...
    
    def serialize(self):
        dict = {
            'secrets': [key.secret for key in self.keys],
        }
        return json.dumps(dict, indent=4)

    def save(self):
        with open(self.filename, 'w') as f:
            data = self.serialize()
            f.write(data)
```

Notes:
- The `indent` flag in `json.dumps` makes the output more readable by adding newlines and indentation (4 characters).
- We set a `Wallet.filename` class-level attribute. More on this in the next step.

At this point we'd be able to call `.save()` on any `Wallet` instance and the wallet state (only private keys so far) would be save to disk. But we wouldn't be able to load it from disk. For that, we need a few more methods:

```
class Wallet:

    ...
    
    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        return cls([PrivateKey(secret) for secret in data['secrets']])

    @classmethod
    def open(cls):
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            return cls.deserialize(raw_json)
```

Notes:
- In `Wallet.deserialize` we need to manually instantiate `PrivateKey` instances from the secret integers we load from our filesystem.
- `Wallet.open` opens `cls.filename` in order to read the contents of the wallet file. Now you see why we want a class-level `filename` attribute instead of an instance-level attribute: it is used to create instances and so must be defined before they are created. Another alternative would be to use a global variable but since the wallet `filename` is so intimately related to the `Wallet` class I think it makes more sense to tack it on.
- Both methods are `classmethod`s, which means they are called on the class itself and not on instances: `wallet = Wallet.open()` will read our wallet file and return a `Wallet` instance. `classmethod`s are useful in scenarios like this when you want to an instance without directly passing each parameter to the constructor.


Before we can test out our `Wallet` class we must add a methods to generate private keys and produce new addresses from newly generated private keys:

```python
from bedrock.ecc import N, PrivateKey
from random import randint

...

class Wallet:

    ...
    
    def generate_key(self):
        secret = randint(1, N)
        key = PrivateKey(secret)
        self.keys.append(key)
        self.save()
        return key
    
    def consume_address(self):
        key = self.generate_key()
        return key.point.address(testnet=True)
```

This is exactly what we covered in the REPL earlier. Every time you need a new address you will call `Wallet.consume_address()` which will generate a new private key, add it to the class key store, save the wallet state to disk, and return a testnet address.

Let try it out:

```
>>> from wallet_final import Wallet
>>> wallet = Wallet([])
>>> wallet.consume_address()
'msPxFt1yCNY2NNiiHRLRWcvDgehA6jkAFP'
>>> del wallet
>>> wallet = Wallet.open()
>>> wallet.keys[0].point.address(testnet=True)
'msPxFt1yCNY2NNiiHRLRWcvDgehA6jkAFP'
```

As you can see we're able to create a `Wallet` generate an address, delete the `Wallet` instance, and reload it from disk using `Wallet.open()` and produce the same address as was produced earlier.

One problem remains, however: if we create another `Wallet` instance and save it, our old wallet file will be deleted. Let's create a `Wallet.create()` method which will raise an error if any wallet file already exists. If we only ever create `Wallet` instances with this or `Wallet.open` we can avoid overwriting wallet files. This isn't a perfect approach -- perhaps it would be better to give identifiers to wallets and only allow updates to wallet files if identifiers in the JSON matched. But this is good enough for "hello, world". You can explore such ideas and I'll be happy to answer questions.

```
from os.path import isfile

...

class Wallet:

    ...

    @classmethod
    def create(cls):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        keys = []
        wallet = cls(keys)
        wallet.save()
        return wallet
```

If we try to create a new wallet while a wallet file already exists, we'll be greeted with an `OSError`. Restart your REPL and try this:

```
>>> from wallet import Wallet
>>> Wallet.create()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/justin/dev/teaching/wallets/simple_cli/wallet_final.py", line 29, in create
    raise OSError("wallet file already exists")
OSError: wallet file already exists
```

As an alternative to restarting your repl, you could try:

```
import sys, importlib
importlib.reload(sys.modules['wallet'])
from wallet import *
```

It's a little cumbersome so I'll just say "restart your REPL" from now on ...

## Funding Your Wallet

Grab a new address and head over to [a testnet faucet like this one](https://testnet-faucet.mempool.co/) and send yourself some bitcoins.

```
>>> wallet = Wallet.open()
>>> wallet.consume_address()
'msPxFt1yCNY2NNiiHRLRWcvDgehA6jkAFP'
```

For now we aren't able to check the status of the transaction using our wallet like we could on a [testnet block explorer](https://blockstream.info/testnet/).

Let's exercise a 3rd party API to help us fetch these balances.

You will find a [`services.py`](./services.py) file in this directory containing a library of function to fetch the balance, transactions, and unspent outputs associated with a list of addresses. As I mentioned at the top, this is the easiest way to query the bitcoin blockchain, but it has some serious drawback which we'll address later. Namely, you don't control which consensus rules the node follows and you give up a lot of privacy by telling them your addresses.

Since these methods all take a list of addresses as argument, it would be convenient to make a method on `Wallet` to generate all our addresses. We could also make a couple convenience methods to exercise the functions defined in `services`:

```
from services import get_balance, get_unspent, get_transactions

class Wallet:

    ...
    
    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys]

    def balance(self):
        return get_balance(self.addresses())

    def unspent(self):
        return get_unspent(self.addresses())

    def transactions(self):
        return get_transactions(self.addresses())
```

To test this out, restart your REPL and run the following:

```
>>> wallet.balance()
(0, 100000)
>>> wallet.transactions()
[]
>>> wallet.unspent()
[{'prev_tx': b'\t\xfe\x94\x96\x9b?\x93\x1c\xd9\xe8\x9a\x08\xc7n\x89a8e>\x89&\xb3\xb0\x0b4\xc5\x85\xe6\xdb\xdc\xa3m', 'prev_index': 0, 'amount': 1000000, 'address': 'msPxFt1yCNY2NNiiHRLRWcvDgehA6jkAFP'}]
```

Notes:
- `Wallet.balance()` returns a tuple of the ("unconfirmed balance", "confirmed balance") 
- calling `Wallet.transactions()` doesn't show unconfirmed transactions at the moment. This is a shortcoming of the API being used currently. Will hopefully sort that out soon.

We're just missing one piece before you can call this a (shitty) Bitcoin wallet: transaction signing.

```
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

```


Here's a `Wallet.send(address, amount, fee)` method which will prepare a bitcoin transaction, gather enough inputs or raise exception if we can't afford the transaction. Then it will construct an output 

```python
from bedrock.tx import Tx, TxIn, TxOut
from bedrock.script import address_to_script_pubkey
from services import get_balance, get_unspent, get_transactions, broadcast

class Wallet:

    ...
    
    def lookup_key(self, address):
        for key in self.keys:
            if key.point.address(testnet=True) == address:
                return key
    
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
```

Notes:
- First we gather unspent transaction outputs that can be used as inputs to this transaction
- Then we look over the unspents, and build up a list of `TxIn` transaction input instances which will go into our bitcoin transaction as well as the private keys that will be used to sign those inputs (which requires definition of a `Wallet.lookup_key` address that looks up the private key associated with a given address). We also sum up the amounts of the inputs as we go (`input_sum`).
- Transaction inputs have 2 required parameters: `prev_tx` (bytes) and `prev_index` (int) which specify transaction output we're spending.
- Once we have enough inputs to send `amount` plus `fee`, we break from the loop.
- Check that we `input_sum` covers the `amount` plus `fee`. This check could fail if there weren't any unspents, for instance.
- Next we construct outputs. For both the output we're "sending" and our "change" output we must provide the `amount` and the `script_pubkey` -- which is the bitcoin script that was used to lock the unspent output we're spending. During the signing phase we'll need to provide a solution to this `script_pubkey` locking script.
- Next we construct a `Tx` instance.
- Then, we sign every input using the correspond private key we grabbed in the first loop.
- Finally, we serialize the transaction as hex and broadcast to the network using a 3rd party API.

Let's try it out:

```
>>> wallet.balance()
(0, 1000000)
>>> wallet.send('mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt', 5000, 500)
'6d04b778af3172c3db8b305f2ed06aa6578bd7be503622b994c241fc3be1edcf'
>>> wallet.balance()
(-5500, 1000000)
>>> wallet.transactions()
[{'txid': '6d04b778af3172c3db8b305f2ed06aa6578bd7be503622b994c241fc3be1edcf', ...
```

It prints out the ID of the transaction we just created. You can see how our unconfirmed balance changed from 0 to -5500 (amount sent plus fees) but unconfirmed balance was unchanged. Once the transaction confirms the unconfirmed balance will update as well:

```
>>> wallet.balance()
(0, 945000)
```

That's it! You've written your first bitcoin wallet.

But our wallet still has some serious flaws. One of the big ones is that it would require backup every time a new private key is generated. Otherwise, if you computer crashed you'd loose that un-backed-up private key. Managing backups was a big hassle with early bitcoin wallet. Our next wallet will use a "keypool" to generate a big chunk of keys ahead of time so that you would only need to backup once per chunk of keys generated. After that we will explore "deterministic" wallet that take one secret and generate a sequence or hierarchy of keys from it.
