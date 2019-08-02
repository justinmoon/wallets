# cli_keypool

The simplest bitcoin wallet will randomly generate new private keys for every new addresses that is requested. But there's a big downside: you need to backup each time these keys are created in order to get any redundancy. Utilizing a "keypool" can help with this. A keypool will generate N private keys ahead of time, and only when the N corresponding addresses have been used will it generate another N private keys. Therefore, you only need to backup once per N addresses consumed.

A keypool should also differentiate between internal / change addresses and receiving addresses.

For these exercises, we will us my "bedrock" library, which is based on the library from Jimmy Song's Programming Bitcoin book.

## Getting Started

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
>>> from bedrock.ecc import N
>>> secret = randint(1, N)
>>> print(secret)
```

Now that we know how to generate a private key, let's think about how a `Wallet` class might look. It should offer the following services:

- Save all wallet state to disk
- Load all wallet state from disk
- Fetch your balance
- Fetch unspent transaction outputs
- Fetch transaction history
- Generate a new private key
- Fill the keypool with N new addresses
- Maintain 2 keypools for receiving addresses & change addresses
- Consume addresses from receiving and change keypools

I think it makes sense to define 2 separate classes: 

- `KeyPool`: Stores the keys, refills keypool, consumes addresses (tracks an "index" of current address)
- `Wallet`: Requests new addresses from "change" and "receiving" keypools, prepares transactions, fetches balance / unspents / transaction history from external services, saves and loads state from disk

Let's sketch out how these classes might look:

```python
class KeyPool:
    pass

class Wallet:
    pass
```


## KeyPool Class

Let's start on the keypool class first. 

The class constructor should take:
- `n` the number of keys to generate ahead of time
- `private_keys` the private keys themselves
- `index` index of next private key

```
class Keypool:
    def __init__(n, private_keys, index):
        pass
    ...
```

Let's hop over to the REPL and play with our keypool. We'll create a new `KeyPool` instance of size 3. We consume 3 addresses, and see that the keypool still only contains 3 keys. But when we consume another address, the keypool grows by 3 to contain 6 total addresses.

# FIXME: maybe use n=2

```
>>> from wallet import KeyPool
>>> keypool = KeyPool.create(3)
>>> len(keypool.private_keys)
3
>>> keypool.address()
...
>>> keypool.address()
...
>>> keypool.address()
...
>>> len(keypool.private_keys)
3
>>> keypool.address()
...
>>> len(keypool.private_keys)
6
```

TODO: 
- `create` classmethod? If yes, discuss why we wouldn't do this in the constructor.
- fill
- address

## Wallet Class

Now that we have a `KeyPool` class, let's utilize it to build our `Wallet` class. Let's create a constructor and a `create` classmethod to initialize a wallet with change and receiving keypools.

Next, let's hop over to the REPL and demonstrate consumption of change and receiving addresses

```
>>> ...
```

Now that our `Wallet` class has its keypools, let's fund one of our receiving addresses. But before we do this, let's add methods to save and load the `Wallet` class to disk. We also want to be sure to call `save()` after every call to `Wallet.change_address()` and `Wallet.receiving_address()`

```
...
```

Now we can fund the address without fear of losing the private key:

```
>>> address = keypool.receiving_address()
...
```

Visit https://testnet-faucet.mempool.co/ and send some testnet coins to this address. After 10 or so minutes this transaction should confirm.

Now that we've create a UTXO backed by one of our private keys, let's write methods to fetch our balance, unspents, and transaction history from a 3rd party service.

```python
class Wallet:
    ...
    def balance(self):
        pass
    ...
```

```python
>>> keypool = KeyPool.load()
>>> keypool.balance()
```

```python
class Wallet:
    ...
    def transactions(self):
        pass
    ...
```

```python
>>> keypool = KeyPool.load()
>>> keypool.transactions()
```

```python
class Wallet:
    ...
    def unspents(self):
        pass
    ...
```

```python
>>> keypool = KeyPool.load()
>>> keypool.unspents()
```

## Sending Bitcoin

Finally, it's time to spend the testnet bitcoin we now own. Let's utilize the `Tx`, `TxOut`, and `TxIn` classes from `bedrock.tx` to write a `Wallet.send` method.

```

```

The testnet faucet we used advertises a receiving address `mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt` on it's page where you can donate your tBTC back when your finished with it. Let's send our tBTC back to them:

```
>>> wallet.send(mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt, 0.001)
```

Voila! You've written your first (extremely primitive) bitcoin wallet.
