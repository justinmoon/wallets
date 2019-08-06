# Hierarchical Deterministic Wallet

Our "sequential deterministic wallet" was able to reduce the required backups to just 1 -- a huge win. But instead of just a "sequence" of private keys, it would be much better if we could have a tree of private keys.

Bitcoin's [BIP 32](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki) described such a sceme which has now become widely adopted by bitcion wallets. We will use [bedrock's implementation](https://github.com/justinmoon/bedrock/blob/master/bedrock/hd.py) for this iteration of our command-line wallet.

## `bedrock.hd.HDPrivateKey`

Bedrock has a class for hierarchical deterministic private keys following the BIP32 standard. Here's how it works:

```
>>> from bedrock.hd import HDPrivateKey
>>> mnemonic, master_key = HDPrivateKey.generate()
>>> print(mnemonic)
victory horn math alarm term lend ship develop oven jelly face hood
>>> print(master_key.pub.point.address(testnet=True))
mxZiCvJwv3GFCnBcBiyz7vq1JBCu6mU6if
>>> master_key.serialize()
b'zprvAWgYBBk7JR8GjK2UCTcxNyzJCk4Cz1huGP7QyQxuCfqU26DVdwUSmLqs8qbgQNLt5qS5WCroDLxYX83KEqz8yeXUw4XpFYR1CAunXG4Dys4'
>>> HDPrivateKey.parse(BytesIO(master_key.serialize())).serialize()
b'zprvAWgYBBk7JR8GjK2UCTcxNyzJCk4Cz1huGP7QyQxuCfqU26DVdwUSmLqs8qbgQNLt5qS5WCroDLxYX83KEqz8yeXUw4XpFYR1CAunXG4Dys4'
>>> master_key.private_key.sign(10)
Signature(60ed3042c7a11100a9a5c60b629667bda50e478f26a1f385aae6cbb9c43f0d15,39d5cbc771adc4fd09215a9df64a4ab37e01436762522c28f4f565fe471c5fb3)
```

Notes:
- `bedrock.hd.HDPrivateKey.pub` is in instance of `bedrock.hd.HDPublicKey`. 
- We can generate addresses with `bedrock.hd.HDPublicKey.point.address`. This is a little grueling to type / remember. I should improve the library to make this easier.
- `bedrock.hd.HDPrivateKey.serialize()` will returns the bytes-serialization of the key, `bedrock.hd.HDPrivateKey.parse()` reads a key out of a serialized byte stream.
- Notice how serializing (2nd last step) produced same result as serializing then parsing then serializing.
- `HDPrivateKey.private_key.sign` is what we'll use to sign transactions

This covers everything our SD wallet could do. But the tree structure of the keys in a wallet employing HD key derivation allows for a new feature we'll implement in this wallet: named accounts. 

BIP 32 supports 2 kinds of key derivation: hardened and unhardened derivation. The difference is explained in [this stackexchange post](https://bitcoin.stackexchange.com/a/37489/85335). 

BIP 32 also introduces a notation for deriving a tree of keys:
- `m/2/4/1` says start at the master private key `m` and derive the second child, then fourth child, then first child. 
- `m/3'/1'/5` says start at the master private key and derived the third hardened child, then the first hardened child, then the fifth unhardened child.

So perhaps our account structure could work like this:

> `m/<account-number>/n` where `<account-number>` is stored in our wallet and associated with some account name, e.g. `payroll`.

This would work, but something better exists called BIP44, which defines a [standard derivation paths](https://github.com/bitcoin/bips/blob/master/bip-0044.mediawiki#path-levels):

> m / purpose' / coin_type' / account' / change / address_index

Notes:
- `purpose`
    - 44 if you're using bitcoin (there are exceptions to this which we'll address later).
    - Hardened derivation
- `coin_type`
    - Allows for multiple coin types to be stored in a HD key tree
    - Mainnet is 0, Testnet is 1
    - Codes for shitcoins found [here](https://github.com/satoshilabs/slips/blob/master/slip-0044.md)
- `account`
    - The same "account number" idea instroduced above.
- `change`
    - 0 for "receiving" addresses -- when other people are sending you coins.
    - 1 for "change" addresses -- when you send coins back to yourself when sum of transaction inputs exceed outputs you're sending plus the miner fee.
- `address_index`
    - Same idea as the `address_index` in our SD wallet.

Let's play with this in the REPL. Using the `master_key` defined in the prior REPL example, let's derive the 3rd receiving address from our 77th account:

```
>>> master_key.traverse(b"m/44'/0'/0'/77/3")
<bedrock.hd.HDPrivateKey object at 0x7f6523518b70>
```

And the 22nd change address in our 2nd account

```
>>> master_key.traverse(b"m/44'/0'/1'/2/22")
<bedrock.hd.HDPrivateKey object at 0x7f6523518b70>
```

Now we're ready to start integrating bedrock's HD key derivation into our wallet!

## Update The Constructor

First, delete the `Wallet.child()` method definition and the `sha256` import.

Next, let's edit the constructor method and `Wallet.create` methods. We'll also add a call to a `Wallet.register_account()` which we'll define in the next step:

```
from bedrock.hd import HDPrivateKey

...

class Wallet:

    def __init__(self, master_key, accounts):
        self.master_key = master_key
        self.accounts = accounts

    @classmethod
    def create(cls, account_name):
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        mnemonic, master_key = HDPrivateKey.generate(testnet=True)
        accounts = {}
        wallet = cls(master_key, accounts)
        wallet.register_account(account_name)
        return mnemonic, wallet
    
    ...
```

Notes:
- Our `Wallet` class now contains 2 attributes:
    - `master_key` which is an instance of `HDPrivateKey`.
    - `accounts` which will be a dictionary. We'll flesh this out in the next step.
- `Wallet.create` calls `HDPrivateKey.generate()` which returns a `(mnemonic, master_key)` tuple. `mnemonic` is a human-readable form of the master private key which I'm sure you've encountered using bitcoin wallets in the past. We return this same tuple.

Now we need to define `Wallet.register_account`. It will take an `account_name` parameter and map that `account_name` to a dictionary representing this account of the form:

> {'account_number': <account_number>, 'receiving_index': <int>, 'change_index': <int>}

Let's implement it:

```
...

class Wallet:
    
    ...
    
    def register_account(self, account_name):
        assert account_name not in self.accounts, 'account already registered'
        account_number = len(self.accounts)
        account = {
            'account_number': account_number,
            'receiving_index': 0,
            'change_index': 0,
        }
        self.accounts[account_name] = account
        self.save()

    ...
```

Notes:
- We make sure `account_name` hasn't already been defined
- We get `account_number` by counting the number of accounts we have previously. This works because we will be indexing our accounts from 0.
- We now keep track of two indices: for receiving addresses and change addresses.
- We save at the end

## Update (De)serialization

Since the attributes of our `Wallet` class changed, so must our serialization:

```
...
from io import BytesIO

...

class Wallet:
    
    ...
    
    def serialize(self):
        dict = {
            'master_key': self.master_key.serialize().hex(),
            'accounts': self.accounts,
        }
        return json.dumps(dict, indent=4)
    
    ...
    
    @classmethod
    def deserialize(cls, raw_json):
        data = json.loads(raw_json)
        master_key_stream = BytesIO(bytes.fromhex(data['master_key']))
        data['master_key'] = HDPrivateKey.parse(master_key_stream)
        return cls(**data)
    
    ...
```

Notes:
- We serialize `HDPrivateKeys().serialize()` as hex because `bytes` aren't JSON-serializable.
- We need `BytesIO` to deserialize because `HDPrivateKey.parse()` takes a stream as its argument.

## Key Derivation

Now let's define a `Wallet.derive_key` method which derives a key for a given account name:

```
...

class Wallet:

    ...
    
    def derive_key(self, account_name, change, address_index):
        account = self.accounts[account_name]
        account_number = account['account_number']
        change_number = int(change)
        address_index = account['change_index'] if change else account['receiving_index']
        path_bytes = f"m/44'/1'/{account_number}'/{change_number}/{address_index}".encode()
        return self.master_key.traverse(path_bytes)
    
    ...
    
    def keys(self, account_name):
        keys = []
        account = self.accounts[account_name]
        # receiving addresses
        for address_index in range(account['receiving_index']):
            key = self.derive_key(account_name, False, address_index)
            keys.append(key)
        # change addresses
        for address_index in range(account['change_index']):
            key = self.derive_key(account_name, True, address_index)
            keys.append(key)
        return keys
    ...
```

Notes:
- `Wallet.derive_key()`
    - We build a BIP 44 path template with `purpose` (`44'` for BIP 44) and `coin_type` (`1'` for testnet) filled in, but open slots for `account_name`, `change`, and `address_index`.
    - We look up the `account_number` by `account_name` in `Wallet.accounts`.
    - `change` should be a `bool` to start, and we cast it to `int` because that's what the template wants.
    - We look up `address_index` differently according to whether we're deriving a change address or not.
    - We encode the path as `bytes` and pass to `self.master_key.traverse`
- `Wallet.keys()`
    - This is exactly the same as our old `Wallet.keys` except for 3 things:
        1. We only iterate over the keys of a single account.
        2. We iterate over both receiving and change address indices.
        3. We call the new `Wallet.derive_key` function.

Alright, this should support every kind of key derivation supported by BIP 32 / BIP 44.

## Addresses

Now let's update all the existing code dealing with address generation.


```
...

class Wallet:

    ...

    def lookup_key(self, account_name, address):
        for key in self.keys(account_name):
            if key.pub.point.address(testnet=True) == address:
                return key

    def addresses(self, account_name):
        return [key.pub.point.address(testnet=True) for key in self.keys(account_name)]

    def consume_address(self, account_name, change):
        account = self.accounts[account_name]
        if change:
            address_index = account['change_index']
            account['change_index'] += 1
        else:
            address_index = account['receiving_index']
            account['receiving_index'] += 1
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)
    
    ...
```

Notes:
- Every method gets an `account_name` variable.
- To get addresses we must call `HDPrivateKey.pub.point.address(testnet=True)` as described earlier.
- The `if`-statement looks up and increments indices according to whether we're consuming a change address or not.

## 3rd Party Services

Our code for 3rd party services needs some tweeks to work with accounts:

```
...

class Wallet:

    ...

    def balance(self, account_name):
        return get_balance(self.addresses(account_name))

    def unspent(self, account_name):
        return get_unspent(self.addresses(account_name))

    def transactions(self, account_name):
        return get_transactions(self.addresses(account_name))
    
    ...
```

## Transaction Signing

`Wallet.sign` requires 2 small tweeks to make it work with accounts and `HDPrivateKey`

```
...

class Wallet:

    ...
    
    def send(self, account_name, address, amount, fee):
        ...
        
        unspent = self.unspent(account_name)
        
        ...
        
        for utxo in unspent:
            ...
            
            hd_private_key = self.lookup_key(account_name, utxo['address'])
            private_keys.append(hd_private_key.private_key)
        
        ...
        
        change_script_pubkey = address_to_script_pubkey(self.consume_address(account_name, True))
        
        ...
```

Notes:
- `Wallet.sign()` also get as `account_name` variable. We put it first in all methods for simplicity sake.
- These are all small tweeks to existing lines in this method.
- `HDPrivateKey.PrivateKey.sign()` is what we'll now use to generate ECDSA signatures.
- We pass `True` as second parameter to `Wallet.consume_address` because we want a change address.

## CLI

First of all, we need to support a `--account` flag so that users can specify which account to use in the case that more than 1 is present.

```
...

def parse_args():
    
    ...
    
    parser.add_argument('--account', help='which account to use', default=argparse.SUPPRESS)
    
    ...
    
    # if --account wasn't passed
    if 'account' not in args:

        # if there aren't any wallets, set it to 'default'
        if not hasattr(args, 'wallet'):
            args.account = 'default'

        # if there's just 1 account we can safely guess it
        elif len(args.wallet.accounts) == 1:
            args.account = list(args.wallet.accounts.keys())[0]

        # otherwise display an error telling them to pass --account and return
        else:
            options = ','.join(args.wallet.accounts.keys())
            msg = f'--account must be set for wallets with more than 1 account (options: {options})'
            return parser.error(msg)
    
    return args
```

Notes:
- This is an optional argument indicated by the leading `--`.
- `default=argparse.SUPPRESS` says that if no value is passed that `args` shouldn't have an `account` attribute.
- At the bottom of `parse_args` we check for the absense of `args.account`. If it isn't there, it means we need to attempt to set it. We can set it in the case that the wallet has 0 or 1 accounts, but we need to raise an error in the case that there are more than 1 accounts.
- `parser.error()` will display a nice error message.

Now we update `create_command` to reflect that `Wallet.create` now returns a `(mnemonic, HDPrivateKey)` tuple. We also must pass `args.account` to each call that needs it:

```
...

def create_command(args):
    mnemonic, wallet = Wallet.create(args.account)
    print("wallet created. here is your mnemonic.")
    print(mnemonic)
    address = wallet.consume_address(args.account, False)
    print("your first receiving address:", address)

def address_command(args):
    address = args.wallet.consume_address(args.account, False)
    print(address)

def balance_command(args):
    unconfirmed, confirmed = args.wallet.balance(args.account)
    print(f'unconfirmed: {unconfirmed}')
    print(f'confirmed: {confirmed}')

def unspent_command(args):
    unspent = args.wallet.unspent(args.account)
    pprint(unspent)

def transactions_command(args):
    transactions = args.wallet.transactions(args.account)
    ids = [tx['txid'] for tx in transactions]
    pprint(ids)

def send_command(args):
    response = args.wallet.send(args.account, args.address, args.amount, args.fee)
    print(response)

...
```

Note:
- We print the mnemonic since that's kinda important ;)
- Every call to `Wallet.consume_address` now passes `False` as its second variable because these are not change addresses.

There's just one thing missing: how do we allow users to create new accounts? Let's make a `register` command to do this:

```
...

def register_command(args):
    args.wallet.register_account(args.name)
    pprint(args.wallet.accounts)

...

def parse_args():
    
    ...
    
    # register
    register_account = subparsers.add_parser('register', help='register a new account')
    register_account.add_argument('name', help='what to call this account')
    register_account.set_defaults(func=register_command)

    ...
```

## Testing

Let's test out our new HD multi-account wallet:

```
$ python cli.py create
wallet created. here is your mnemonic.
process copper limb desk kit fatal coach pause echo trophy spirit female
your first receiving address: n4Vw3Q3STTor2CaRbxazvehtrDiJDLTSwM
$ python cli.py register second
{'default': {'account_number': 0, 'receiving_index': 1, 'change_index': 0},
 'second': {'account_number': 1, 'receiving_index': 0, 'change_index': 0}}
```

Now fund both addresses the `default` account address but don't fund any `second` account addresses. We'll fund `second` from `default`!

```
$ python cli.py --account default balance
unconfirmed: 1000000
confirmed: 0
$ python cli.py --account second balance
unconfirmed: 0
confirmed: 0
```

While waiting for a confirmation let's verify that we get an error if we forget to pass `--account`:

```
$ python cli.py balance
usage: cli.py [-h] [--debug] [--account ACCOUNT]
                    {create,address,balance,transactions,unspent,register,send}
                    ...
cli.py: error: --account must be set for wallets with more than 1 account (options: default,second)
```

Once our transaction confirms, let's send some coins from `default` to `second`:

```
$ python cli.py --account second address
mp5p8f6Qx8FtqDjtsM8o8iG8J9akw2XFZE
$ python cli.py --account default send mp5p8f6Qx8FtqDjtsM8o8iG8J9akw2XFZE 4000 500
29d8eeadf659b0a10a0fa418667d1c1ce4415ceebda428d8f31c4394417652e6
$ python cli.py --account default balance
unconfirmed: -4500
confirmed: 100000
$ python cli.py --account second balance
unconfirmed: 0
confirmed: 4000
```

Also, take a look at `wallet.json` to see that 1 change address was consumed by the `default` account:

```
$ cat wallet.json
{
    "master_key": "7670727639444d55785834536867784d4c6d5859745573476d41334c78797a517941617144736f32344872394c5831734d623850724455744a773463464b4242777146476a4465397a5665707147344b76434e343934557838323358343343326638326d633467506943713965704c",
    "accounts": {
        "default": {
            "account_number": 0,
            "receiving_index": 1,
            "change_index": 1  # change index no longer zero
        },
        "second": {
            "account_number": 1,
            "receiving_index": 1,
            "change_index": 0
        }
    }
```

## Exercises

- Can you use `HDPrivateKey.from_mnemonic()` to allow people to restore from mnemonic via cli?
