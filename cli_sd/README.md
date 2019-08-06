# Sequential Deterministic Wallet

## Introduction

Our "keypool" design alleviated our need for ongoing wallet backup, but it didn't remove the need entirely.

A better design would be to start with a master private key and derive child private keys by repeatedly hashing it. For instance, the 3rd private key could be `sha256(sha256(sha256(master_secret)))`. Then we'd only need to backup the `master_secret` when it's created and never have to worry about backups after that.

## Change `Wallet` Constructor

This time around let's just have our `Wallet` class keep track of our master `secret` (an integer) and the index of the next child key.

Update the `Wallet` constructor and `Wallet.create()` in `wallet.py` likewise:

```python
...

class Wallet:

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
    ...
```

Notes:
-  `Wallet.create()` used to call `wallet.generate_keys()` which save wallet state for us. Since we're no longer calling this keypool-specific method, we now need to directly call `self.save()` to save wallet state to disk.

## Changing (De)serialization Methods

Since the attributes of the `Wallet` class have changed, we need to update (de)serialization methods:

```
...

class Wallet:

    ...

    def serialize(self):
        dict = {
            'secret': self.secret,
            'index': self.index,
        }
        return json.dumps(dict, indent=4)

    ...

    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        return cls(**data)
```

Notes:
- Since our `Wallet` class no longer holder `PrivateKey` instances, we don't have to worry about converting between `PrivateKey` and `int`. We just deal with the `ints` which are natively JSON-serializable.
- Since the `data = json.loads(raw_json)` has exactly the same shape as arguments to `Wallet.__init__`, we can "splat" it with `cls(**data)`.

## Addresses & Key Derivation

In order to generate multiple addresses we need to implement the repeated hashing discussed in the intro.

Let's implement a `Wallet.child` method for this:

```
from bitcoin.helper import sha256
...

class Wallet:

    ...

    def child(self, index):
        # hash master secret "index" times
        secret_bytes = self.secret.to_bytes(32, 'big')
        for _ in range(index):
            secret_bytes = sha256(secret_bytes)
        child_secret = int.from_bytes(secret_bytes, 'big')
        return PrivateKey(child_secret)
    
    # delete the generate_keys() method

    ...
```

Notes:
- `bitcoin.helper.sha256` is a light wrapper around `hashlib.sha256` that just returns `bytes` instead of the default "hash object" using `hashlib.sha256(input).digest()` which makes for easier repeated hashing.
- `Wallet.secret` is a 32 byte integer so we need to convert it to bytes before we can hash it. We do this with `self.secret.to_bytes(32, 'bit')`
- We use a for-loop to hash `index`-many times.
- When we're done hashing we convert back to integer type using `int.from_bytes(secret_bytes, 'big')` and return a `PrivateKey` instance containing this derived child secret.

With the ability to derive multiple keys, we're ready to produces addresses:

```

    def keys(self):
        return [self.child(index) for index in range(self.index)]

    def lookup_key(self, address):
        for key in self.keys():  # self.keys is now a function, just add () before :
            if key.point.address(testnet=True) == address:
                return key

    def addresses(self):
        return [key.point.address(testnet=True) for key in self.keys()]

    def consume_address(self):
        # fetch private key, increment index and save
        key = self.child(self.index)
        self.index += 1
        self.save()
        # return testnet address
        return key.point.address(testnet=True)
```


Notes:
- `Wallet.keys` was a static attribute because the keypool wallet manually generated keys from randomness ahead-of-time. Now it's a method because child keys are deterministically derived just-in-time by repeated hashing.
- `Wallet.keys` iterates over `range(self.index)` because `self.index` is the _next key_ that will be used, but which hasn't been used yet.
- `Wallet.lookup_key` & `Wallet.addresses` iterate over `self.keys()` instead of `self.keys`.
- `Wallet.consume_address` no longer calls the deleted `Wallet.generate_keys()`, and replaces `self.keys[self.index]` with `self.child(self.index`.

## Update CLI

The `size` parameters we added to the cli for the keypool now need to be deleted:

- Delete the `create.add_argument('size', type=int, help='size of wallet keypool')` line
- Change `wallet = Wallet.create(args.size)` to `wallet = Wallet.create()`

Now it's ready for testing. Try creating, funding, generating multiple addresses, and sending funds. Run `cat wallet.json` between steps that derive new keys. You'll see that the `secret` attribute stays fixed, but `index` increments.
