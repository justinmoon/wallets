# Simple CLI Wallet

## Introduction

A few pieces go into building a Bitcoin wallet:
1. Dealing with Private keys
2. Connecting to the Bitcoin network

We're going to build a series of wallets that explore a few different ways to accomplish both of these wallet engineering components. We'll start with the simplest approach for each, then explore different private key strategies until we reach the current state-of-the-hard ([Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki), and then explore a few bitcoin network strategies.

For these exercises, we will us my [bedrock](https://github.com/justinmoon/bedrock) library, which is based on the library from Jimmy Song's Programming Bitcoin book.

(Complete files from these exercises: [cli.py](./cli.py) & [wallet.py](./wallet.py))

## Setup

Create a virtual environment in the base of the `wallets` directory:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Generating Private Keys

Private keys are 256 bit integers in the range (1, 115792089237316195423570985008687907852837564279074904382605163141518161494337). This upper bound can be imported from `bedrock.ecc.N`.

To generate a private key we can use you computer's random number generator via Python's `random.randint` function:

```
>>> from random import randint
>>> from bedrock.ecc import N, PrivateKey
>>> secret = randint(1, N)
>>> print(secret)
>>> private_key = PrivateKey(secret)
>>> print(private_key)
```

## Generating Addresses

Once we have a private key, we're able to use it's associated public key (sometimes called a "point" because it's simply a pair of numbers like the `(x, y)` points you studied in algebra).

```
>>> address = private_key.point.address(testnet=True)
>>> print(address)
```

At this point we could fund this address and create a bitcoin UTXO controlled by `private_key`. But once we still need a way to store the private key so that it can be accessed after we close our REPL.

To do this, let's start building a `Wallet` class which knows how to save and load itself from disk.

## `Wallet` Class

### Constructor

To start with, our wallet class just contains a collection of `PrivateKey` instances. Type the following code in a file called `wallet.py`:

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

At this point we'd be able to call `.save()` on any `Wallet` instance and the wallet state (only private keys so far) would be saved to disk. But we wouldn't be able to load it from disk. For that, we need a few more methods:

```python
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
- `Wallet.open` opens `cls.filename` in order to read the contents of the wallet file. Now you see why we want a class-level `filename` attribute instead of an instance-level attribute: it is used to create instances and so must be defined before they are created. Another alternative would be to use a global variable but since the wallet `filename` is so intimately related to the `Wallet` class I think a class-level attribute works best.
- Both methods are `classmethod`s, which means they are called on the class itself and not on instances: `wallet = Wallet.open()` will read our wallet file and return a `Wallet` instance. `classmethod`s are useful in scenarios like this when you want to an instance without directly passing each parameter to the constructor (e.g. when loading from a json string as we're doing here).


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

This is exactly what we covered in the REPL earlier with one exception: we now call `self.save()` whenever `Wallet.keys` is modified. To review: every time you need a new address you will call `Wallet.consume_address()` which will generate a new private key, add it to the class key store, save the wallet state to disk, and return a testnet address.

Let try it out:
To review: 
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

```python
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

You will find a [`services.py`](./services.py) file in this directory containing a library of function to fetch the balance, transactions, and unspent outputs associated with a list of addresses. As I mentioned at the top, this is the easiest way to query the bitcoin blockchain, but it has some serious drawback: you don't control which consensus rules the node follows and you give up a lot of privacy by telling them your addresses.

Since these methods all take a list of addresses as argument, it would be convenient to make a method on `Wallet` to generate all our addresses. We could also make a couple convenience methods to exercise the functions defined in `services`:

```python
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
- `Wallet.balance()` returns a tuple of ("unconfirmed balance", "confirmed balance") 
- calling `Wallet.transactions()` doesn't show unconfirmed transactions at the moment. This is a shortcoming of the API being used currently. Will hopefully sort that out soon.

We're just missing one piece before you can call this a (very crappy) Bitcoin wallet: transaction signing.

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
- Once we have enough inputs to send `amount` plus `fee`, we break from the first loop.
- Check that we `input_sum` covers the `amount` plus `fee`. This check could fail if there weren't any unspents, for instance.
- Next we construct outputs. For both the output we're "sending" and our "change" output we must provide the `amount` and the `script_pubkey` -- which is the bitcoin script that was used to lock the unspent output we're spending. During the signing phase we'll need to provide a solution to this `script_pubkey` locking script.
- Next we construct a `Tx` instance.
- Then, we sign every input using the correspond private key we grabbed in the first loop. This fills in a `script_sig` locking script solution on each transaction input.
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

But our wallet still has some serious flaws. One of the big ones is that it would require backup every time a new private key is generated. Otherwise, if you computer crashed you'd lose that un-backed-up private key. Managing backups was a big hassle with early bitcoin wallets. Our next wallet will use a "keypool" to generate a big chunk of keys ahead of time so that you would only need to backup once per chunk (say, 1000) of keys generated. After that we will explore "deterministic" wallet that take one secret and generate a sequence or hierarchy of keys from it. These strategies only require a single backup at the time of wallet creation.

But before we more on, let's write a command-line-interface (CLI) for our wallet.

## CLI

To build our CLI we'll use [argparse](https://docs.python.org/3/library/argparse.html), a CLI library in the Python Standard Library.

### Create Wallet Command

To get started, add the following in a `cli.py` file:

```python
import argparse

from wallet import Wallet

def create_command(args):
    wallet = Wallet.create()
    address = wallet.consume_address()
    print("wallet created")
    print("your first receiving address:", address)

def parse_args():
    parser = argparse.ArgumentParser(description='Simple CLI Wallet')
    subparsers = parser.add_subparsers(help='sub-command help')

    # create
    create = subparsers.add_parser('create', help='create wallet')
    create.set_defaults(func=create_command)

    return parser.parse_args()

def main():
    args = parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
```

Notes:
- `parse_args` uses argparse to read and interpret the arguments passed when calling this `cli.py` function from the command line. Since we want our CLI to support a number of subcommands such as `python cli.py create`, `python cli.py balance`, `python cli.py send 2N2Yo65pN8WYihKUHnPqmXg2gshy3ZRFzPS 5000 500`, `python cli.py transactiuons` and `python cli.py unspent`, we use `subparsers = parser.add_subparsers` and `subparsers.add_parser(...)` to register register separate handlers for each of these cases.
- We define on such subparser for now: `create`. We associate it with a callback function using `balance.set_default(func=<callback>)`. This allows us to call `args.func(args)` further down. This will just call `<callback>` with `args` as the only argument.
- Lastly, our `create_command` callback takes that `args` object form argparse (which doesn't contain any interesting information in this case), creates a the wallet, fetches the balance, prints out the first receiving address.

Move your current `wallet.json` to a different location and create a new wallet from the command line:

```
$ mv wallet.json old.json
$ python cli.py create
wallet created
your first receiving address: n132VpbgSXLBZSRhpdgRXF3YrAbRVS1r8e
```

Once again, fund this address using a [testnet faucet](https://testnet-faucet.mempool.co/).

### Informational Commands

Now let's implement `balance`, `unspent`, `address`, and `transactions` commands:

```python
from pprint import pprint

def address_command(args):
    wallet = Wallet.open()
    address = wallet.consume_address()
    print(address)

def balance_command(args):
    wallet = Wallet.open()
    unconfirmed, confirmed = wallet.balance()
    print(f'unconfirmed: {unconfirmed}')
    print(f'confirmed: {confirmed}')

def transactions_command(args):
    wallet = Wallet.open()
    transactions = wallet.transactions()
    ids = [tx['txid'] for tx in transactions]
    pprint(ids)

def unspent_command(args):
    wallet = Wallet.open()
    unspent = wallet.unspent()
    pprint(unspent)

def parse_args():
    
    ...

    # address
    address = subparsers.add_parser('address', help='generate new address')
    address.set_defaults(func=address_command)

    # balance
    balance = subparsers.add_parser('balance', help='wallet balance')
    balance.set_defaults(func=balance_command)

    # transactions
    transactions = subparsers.add_parser('transactions', help='transaction history')
    transactions.set_defaults(func=transactions_command)

    # unspent
    unspent = subparsers.add_parser('unspent', help='unspent transaction outputs')
    unspent.set_defaults(func=unspent_command)
    
    ...
    
```

Notes:
- FIXME: add some kind of sorting flag or something to demonstrate argparse options
- This is mostly copy-paste

Let's test it:

```
$ python cli.py address
mobmPdXFkuwnk71Uf5dHrB7umvKEVLRVkK
$ python cli.py balance
unconfirmed: 0
confirmed: 1000000
$ python cli.py unspent
[{'address': 'muQsmiqoiKYXnSFohRHSg4dFfmkYiJYYAR',
  'amount': 1000000,
  'prev_index': 1,
  'prev_tx': b'\x13G\xad\xa8.0<\xdc\xfb\xdaGf\x99.K\xc0\xb4y\x80\x1e$<\x96\xd3'
             b'A\x17\xe0\xb6\xe2\x9e\xb6\xf5'}]
$ python cli.py transactions
['1347ada82e303cdcfbda4766992e4bc0b479801e243c96d34117e0b6e29eb6f5']
```

It's a little annoying how we have to manually call `Wallet.open()` at the top of each callback function. We could improve it by loading a `Wallet` instance and passing to the handler so long as the command isn't `create_command` (no wallet should exist in this case):

```python
...

def address_command(args, wallet):
    ...

def balance_command(args, wallet):
    ...

def unspent_command(args, wallet):
    ...

def transactions_command(args, wallet):
    ...

def main():
    args = parse()

    # call handler. load wallet if we're not creating a wallet.
    if args.func == create_command:
        args.func(args)
    else:
        wallet = Wallet.open()
        args.func(args, wallet)
```

You can test the examples above still work after this refactor.

### Send Command

Lastly, we need a `python cli.py send` command.

This one will be a little more interesting. It will need to take 3 arguments: address, amount, and fee. These will be passed as parameters to `Wallet.send()`.

```python
...

def send_command(args, wallet):
    response = wallet.send(args.address, args.amount, args.fee)
    print(response)

...

def parse_args():
    
    ...
    
    # "send"
    send = subparsers.add_parser('send', help='send bitcoins')
    send.add_argument('address', help='recipient\'s bitcoin address')
    send.add_argument('amount', type=int, help='how many satoshis to send')
    send.add_argument('fee', type=int, help='fee in satoshis')
    send.set_defaults(func=send_command)
    
    ...

```

Notes
- We register argument with the `send` subparsers by calling `send.add_argument`.
- We override the default `str` type of arguments for `amount` and `fee` to be of type `int`.
- Within `send_command`, these values are available on the `args` object and can be sent directly to `wallet.send(...)`

It shoudl print out a transaction ID you can look up in a [testnet block explorer](https://blockstream.info/testnet/):

```
$ python cli.py send mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt 4000 500
6ae9ca8816eb0a2e99afbbe7df1d250529d47b13f7a204ceb4b711aa0c213b7c
```

### Debug Command

Lastly, let's do us a favor and add a `--debug` command-line argument which will set the logging level to `DEBUG` if. We can pass this flag when debugging to get more output about the execution of our program:

```python
import logging

...

def parse_args():
    parser = argparse.ArgumentParser(description='Simple CLI Wallet')
    parser.add_argument('--debug', help='Print debug statements', action='store_true')
    ...
    
def main():
    args = parse_args()

    # configure logger
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)
    ...

```

Let's test it:

```
$ python cli.py --debug send mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt 4000 500
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): testnet-api.smartbit.com.au:443
DEBUG:urllib3.connectionpool:https://testnet-api.smartbit.com.au:443 "GET /v1/blockchain/address/muQsmiqoiKYXnSFohRHSg4dFfmkYiJYYAR,mobmPdXFkuwnk71Uf5dHrB7umvKEVLRVkK,mvp4SpP1z6awfzSTVbXRdpm2tmNEQW4Grv,moJj71qcFUVvkLL65wyaJGHE1XW5RYZzA6,mfa2n91fuQMs2ic75TAucpyUK6kZNEF7Pr/unspent HTTP/1.1" 200 402
DEBUG:BitcoinRPC:-1-> getrawtransaction ["f2fb5786f2b61df20c860311002a54da9d12a3b5ef50bde6924eb73606ae58ee"]
DEBUG:BitcoinRPC:<-1- "01000000017c3b210caa11b7b4ce04a2f7137bd42905251ddfe7bbaf992e0aeb1688cae96a010000006b483045022100a570c1f53e908e8ad56bd8367c147838178cb90a46589b7ea47e3c5e514f57e6022028664f753a1b8f4c4d1ca91be6a5a05113783ed9d1dac7123319440d33b9284801210349296aeca520b3f3b1b0716b7a658ccedb866a64f8e0b58c1aa2ab6d34ac5628ffffffff02a00f0000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688ac181f0f00000000001976a914557101063abca8a5e386744e454221e8a7f87dd588ac00000000"
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:30450221009a12be76e56eb0                              
INFO:bedrock.script:031d5d37523e3e6d3502d20c                              
INFO:bedrock.script:OP_DUP                                                
INFO:bedrock.script:OP_HASH160                                            
INFO:bedrock.script:557101063abca8a5e386744e                              
INFO:bedrock.script:OP_EQUALVERIFY                                        
INFO:bedrock.script:OP_CHECKSIG                                           
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:031d5d37523e3e6d3502d20c                              
INFO:bedrock.script:OP_DUP                                                
INFO:bedrock.script:OP_HASH160                                            
INFO:bedrock.script:557101063abca8a5e386744e                              
INFO:bedrock.script:OP_EQUALVERIFY                                        
INFO:bedrock.script:OP_CHECKSIG                30450221009a12be76e56eb0   
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:OP_DUP                                                
INFO:bedrock.script:OP_HASH160                                            
INFO:bedrock.script:557101063abca8a5e386744e                              
INFO:bedrock.script:OP_EQUALVERIFY                                        
INFO:bedrock.script:OP_CHECKSIG                031d5d37523e3e6d3502d20c   30450221009a12be76e56eb0
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:OP_HASH160                                            
INFO:bedrock.script:557101063abca8a5e386744e                              
INFO:bedrock.script:OP_EQUALVERIFY                                        031d5d37523e3e6d3502d20c
INFO:bedrock.script:OP_CHECKSIG                OP_DUP                     30450221009a12be76e56eb0
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:557101063abca8a5e386744e                              031d5d37523e3e6d3502d20c
INFO:bedrock.script:OP_EQUALVERIFY                                        031d5d37523e3e6d3502d20c
INFO:bedrock.script:OP_CHECKSIG                OP_HASH160                 30450221009a12be76e56eb0
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:                                                      557101063abca8a5e386744e
INFO:bedrock.script:OP_EQUALVERIFY                                        031d5d37523e3e6d3502d20c
INFO:bedrock.script:OP_CHECKSIG                557101063abca8a5e386744e   30450221009a12be76e56eb0
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:                                                      557101063abca8a5e386744e
INFO:bedrock.script:                                                      557101063abca8a5e386744e
INFO:bedrock.script:                                                      031d5d37523e3e6d3502d20c
INFO:bedrock.script:OP_CHECKSIG                OP_EQUALVERIFY             30450221009a12be76e56eb0
INFO:bedrock.script:------------------------------------------------------------------------------
INFO:bedrock.script:                                                      031d5d37523e3e6d3502d20c
INFO:bedrock.script:                           OP_CHECKSIG                30450221009a12be76e56eb0
DEBUG:bedrock.op:signature is good
DEBUG:bedrock.script:stack after execution: [b'\x01']
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): test-insight.bitpay.com:443
DEBUG:urllib3.connectionpool:https://test-insight.bitpay.com:443 "POST /api/tx/send HTTP/1.1" 200 None
14830db4c175cd37d0ed5f5eb1b4c41d4ddd15561364ed65eb0b9d1e56a76dd5
```

We receive a wealth of network information from the `urllib3` library underlying `requests` in `services.py`, as well as some a play-by-play of the evaluation of each transaction input's `script_sig` attribute courtesy of `bedrock`.
