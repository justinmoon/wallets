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


