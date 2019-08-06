# Keypools

One big problem with our "simple" wallet was that it required backup after every new address it generated. This is cumbersome. Early bitcoin developers implemented "keypools" to address this challenge. Instead of generating new private keys as they're needed, they derived a chunk of addresses ahead of time -- say 1000 of them -- and only after generating these chunks.

This drastically reduces the number of backups, which is good. But we still have to backup multiple times which isn't ideal. In the next lessons I'll demonstrate two ways to only require one initial backup.

## Getting Started

The final versions of our "simple" wallet are available in this directory as [cli.py](./cli.py) and [wallet.py](./wallet.py). We'll modify these to implement our keypool.

## Modifying the `Wallet` Constructor

- We'll need two new attributes on the `Wallet` class in order to implement this key generation strategy: a "chunk" size as discussed, and the index of our next key.
- We'll also need to modify the `Wallet.create` method since it's the only code in [wallet.py](./wallet.py) that directly exercises the Wallet constructor.
- We'll need to change `Wallet.generate_key()`, which generated a single key, to `Wallet.generate_keys()`, which will generate a chunk of keys.

```python
class Wallet:

    ...
    
    def __init__(self, keys, size, index):
        self.keys = keys
        self.size = size
        self.index = index
        
    @classmethod
    def create(cls, size):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        keys = []
        index = 0
        wallet = cls(keys, size, index)
        wallet.generate_keys()  # FIXME: a little weird to generate here when "simple" doesn't
        return wallet
 
    ...
    
    def generate_keys(self):
        for _ in range(self.size):
            secret = randint(1, N)
            key = PrivateKey(secret)
            self.keys.append(key)
        self.save()

    ...
```

Next we'll need to update the serialization methods to accommodate these constructor change:

```python
class Wallet:

    ...
    
    def serialize(self):
        dict = {
            'secrets': [key.secret for key in self.keys],
            'size': self.size,
            'index': self.index,
        }
        return json.dumps(dict, indent=4)

    ...

    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        keys = [PrivateKey(secret) for secret in data['secrets']]
        return cls(keys, data['size'], data['index'])
    
    ...
```

The following updates to [cli.py](./cli.py) will also be necessary:
- Add a required `size` argument to the `create` subparser in `parse_args()`.
- `create_command` should pass `args.size` to `Wallet.create(size)`.

In [wallet.py](./wallet.py):

```python
...

def create_command(args):
    wallet = Wallet.create(args.size)
    ...

...

def parse_args():
    ...
    create.add_argument('size', type=int, help='size of wallet keypool')
    ...

...
```

## Addresses

Our old `Wallet.generate_address()` method also broke -- it should lookup the key at `Wallet.index` and increment, calling `Wallet.generate_keys` if there is no key at that index.

```python
...

class Wallet:

    ...

    def consume_address(self):
        # refill keypool if it's empty
        if self.index >= len(self.keys):
            self.generate_keys()
        # fetch private key, increment index and save
        key = self.keys[self.index]
        self.index += 1
        self.save()
        # return testnet address
        return key.point.address(testnet=True)
    
    ...
```

`Wallet.addresses()` also needs a small update. It shouldn't iterate over all keys, only up to the key prior to `Wallet.index` -- because that is the next key that will be used.

```python
...

class Wallet:
    
    ...
    
    def addresses(self):
        keys = self.keys[:self.index]
        return [key.point.address(testnet=True) for key in keys]
    
    ...
```

Now we're ready to run it!

```
$ python cli_final.py create 10
wallet created
your first receiving address: n1dSDfJAQWLpeokunqdteChA3VN7z53zLQ
$ python cli.py balance
unconfirmed: 1000000
confirmed: 0
```

Wait for a confirmation

```
$ python cli.py balance
unconfirmed: 0
confirmed: 1000000
$ python cli.py send mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt 7000 500
6778e64225cdd9fad52364ab34f5389ad59b8316901aa5827c701b6b05463ab7
```

Beautiful. Our wallet is less stupid than it was, but still pretty stupid. Next step is to use a master private key and derive a sequence of child private keys from it.
