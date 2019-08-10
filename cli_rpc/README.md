# RPC Wallet

## Requirements

You'll need a version 18.0 or higher Bitcoin Core node with a synced testnet chain for this exercise. Download Bitcoin Core [here](https://bitcoincore.org/en/download/) if you don't have it installed already, and sync the chain with `bitcoin-qt -testnet`. Syncing is finished when the `headers` and `blocks` attributes of the response to `bitcoin-cli -testnet getblockchaininfo` are equal.

## Introduction

In the last few lessons we've been working with a `services.py` file to access "the bitcoin blockchain". But as you know, this isn't our blockchain: it's someone else's. We have no control over the software that is maintaining this blockchain. We are at the mercy of a 3rd party to decide our consensus rules for us. 

But this is Bitcoin. The whole design is focuses on minimizing the costs of verifying the chain yourself. In this lesson we'll learn to connect to your Bitcoin core node using [JSON RPC](https://en.wikipedia.org/wiki/JSON-RPC). We'll be able to connect to the bitcoin consensus implementation of our choice.

Once we've done this, we'll be able to offload some of the work to `bitcoind` -- the most well-maintained piece of software in the ecosystem. In particular, we'll have it select which UTXO we should spend.

Let's get started:

## `bitcoin-cli`

First, add the following lines to your `~/.bitcoin/bitcoin.conf`, replacing the `YOURUSERNAME` and `YOURPASSWORD` with values of your choosing:

```
[test]
server=1
rpcuser=YOURPASSWORD
rpcpassword=YOURPASSWORD
```

`[test]` says that these options should only be active for the testnet chain. `server` tells bitcoin to run the JSON RPC server and the other two set your RPC username and password.

Now, start bitcoin-qt (or restart if you already had it running.

Let's try a few commands using bitcoin-cli. 

### `help`

```
$ bitcoin-cli help
== Blockchain ==
getbestblockhash
getblock "blockhash" ( verbosity )
getblockchaininfo
getblockcount
...
```

These are all the available commands. Depending on which version of Bitcoin Core you're running, more or less commands will show up here.

The third command `getblockchaininfo` is basically `bitcoin-cli`'s "Hello, world!".

### `getblockchaininfo`

Run `bitcoin-cli help getblockchaininfo` to see a more detailed description of the this method.

TLDR it displays some state about your node. Very useful to see if you're synced to the tip or not:

If you just run `bitcoin-cli getblockchaininfo` it will query your mainnet node -- which is offline if your testnet node is running. To query your testnet node you must pass a `-testnet` flag:

```
$ bitcoin-cli -testnet getblockchaininfo
{
  "chain": "test",
  "blocks": 1573692,
  "headers": 1573692,
  ...
}
```

### `createwallet`

Bitcoin Core supports the creation of multiple wallets. The default wallet is simply named the empty string: "". Let's create a new wallet for these exercises so that we don't interfere with any existing testnet coins you may have. Plus, we'll liberally make use of this command later in the lesson. Run `bitcoin-cli help createwallet` to learn more about this command. The first parameter is the wallet name. Let's call ours "tutorial". The second parameter says whether private keys should be disabled for the wallet. We'll keep private keys enabled for now, but later on in the tutorial we'll disable them and handle private keys in out CLI wallet, and eventually on our m5stack hardware wallet.

```
$ bitcoin-cli -testnet createwallet tutorial
{
  "name": "tutorial",
  "warning": ""
}
```

Note: the command returns JSON. That's because under the hood `bitcoin-cli` is simply doing JSON RPC.

## Set an alias

In order to query our "tutorial" testnet wallet's balance, we need to type the long command `bitcoin-cli -testnet -rpcwallet=tutorial getbalance`. That's cumbersome. Let's create a bash alias for the command: `alias tutorial="bitcoin-cli -testnet -rpcwallet=tutorial"`. Then you'd just have to type `tutorial getbalance`. But remember: if you reopen your terminal you'll have to redefine this alias. 

## `getnewaddress`

If you executed the `getbalance` command in the previous section you probably saw that you balance was zero. Let's fix this!

To fund you wallet you'll need to generate an address:

```
$ bitcoin-cli -testnet -rpcwallet=tutorial getnewaddress
2N5zVhSRjtGUN2jdR8G33H2Hx5sFrBBNn6x
```

Hop on over to our trusty [testnet faucet](https://testnet-faucet.mempool.co) and send yourself some tBTC. After doing so, they'll show up in `listtransactions` and after they confirm they'll show up in `getbalance` (I sent myself 2 0.01 tBTC transactions in this example):

```
$ tutorial listtransactions
[
  {
    "address": "2NDLcU63nX5GzeTfs8UdoBeMmsP6wzwEd3d",
    "category": "receive",
    "amount": 0.01000000,
    "label": "",
    "vout": 1,
    "confirmations": 1,
    "blockhash": "0000000000000143a03218e02613de2f63bbe2fc3ba64d30916bf75adf01f39d",
    "blockindex": 56,
    "blocktime": 1565409508,
    "txid": "1b1772297430b9985ef63ba0ba6028d349acc861795defd10acfc2fdde90ff3b",
    "walletconflicts": [
    ],
    "time": 1565409502,
    "timereceived": 1565409502,
    "bip125-replaceable": "no"
  },
  {
    "address": "2NDLcU63nX5GzeTfs8UdoBeMmsP6wzwEd3d",
    "category": "receive",
    "amount": 0.01000000,
    "label": "",
    "vout": 1,
    "confirmations": 0,
    "trusted": false,
    "txid": "c9cb11c097ad7cf4b782dfd46b4104d5a5fa2d1627eebd79740568f55b74f808",
    "walletconflicts": [
    ],
    "time": 1565409521,
    "timereceived": 1565409521,
    "bip125-replaceable": "no"
  }
]
$ tutorial getbalance
0.02000000
```


## Two Ways To Send Bitcoins

### Automated Sending w/ `sendtoaddress`

With this approach we just need to supply an address and an amount, but we don't have much control over how to tranasction is constructed or signed:

```
$ tutorial sendtoaddress mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt 0.0001
5302dc4c1859294e3f203b1e7576d8fb0bb4f5b9224755b1ee1f6b9276546f89
```

### Manual Sending

There are other commands which give you more control over how the transaction is constructed and signed. For instance, we could create an unsigned transaction with no inputs and one output sending 0.0001 tBTC to the faucet's receiving address mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt like this:


```
$ tutorial createrawtransaction "[]" '[{"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt":"0.0001"}]'
02000000000110270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688ac00000000
```

The first argument is JSON representation of the inputs we want to consume (none so far). The second argument is the outputs we want the transaction to create. See `bitcoin-cli help createrawtransaction` for more details.

The previous command returns returns the serialized hex of the unfunded (no inputs), unsigned transaction. We can decode it like this:

```
$ tutorial decoderawtransaction 02000000000110270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688ac00000000
{
  "txid": "c289d8164443f1958d70d5a6e600f7886a6db1beae369243e488b1ec1f1a7096",
  "hash": "c289d8164443f1958d70d5a6e600f7886a6db1beae369243e488b1ec1f1a7096",
  "version": 2,
  "size": 44,
  "vsize": 44,
  "weight": 176,
  "locktime": 0,
  "vin": [
  ],
  "vout": [
    {
      "value": 0.00010000,
      "n": 0,
      "scriptPubKey": {
        "asm": "OP_DUP OP_HASH160 344a0f48ca150ec2b903817660b9b68b13a67026 OP_EQUALVERIFY OP_CHECKSIG",
        "hex": "76a914344a0f48ca150ec2b903817660b9b68b13a6702688ac",
        "reqSigs": 1,
        "type": "pubkeyhash",
        "addresses": [
          "mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt"
        ]
      }
    }
  ]
}
```

Just as we expected: no inputs, one output with address and amount matching what we specified. In order to sign this transaction, we need to fund it by supplying an input spending one of our UTXOS. Let's ask the Bitcoin Core wallet to do this for us by passing the raw hex to `fundrawtransaction`:

```
$ tutorial fundrawtransaction 02000000000110270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688ac00000000
{
  "hex": "0200000001896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc02530100000000feffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f8700000000",
  "fee": 0.00000168,
  "changepos": 1
}
```

The `"hex"` attribute of the resulting JSON now has sufficient inputs to pay for our output, as well as a change output so we don't overpay:

```
$ tutorial decoderawtransaction 0200000001896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc02530100000000feffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f8700000000
{
  "txid": "b0ed7fef500b9056c56bb84d74808af4441b0e9bbf9dc937d3fe0fade5d2d42e",
  "hash": "b0ed7fef500b9056c56bb84d74808af4441b0e9bbf9dc937d3fe0fade5d2d42e",
  "version": 2,
  "size": 117,
  "vsize": 117,
  "weight": 468,
  "locktime": 0,
  "vin": [
    {
      "txid": "5302dc4c1859294e3f203b1e7576d8fb0bb4f5b9224755b1ee1f6b9276546f89",
      "vout": 1,
      "scriptSig": {
        "asm": "",
        "hex": ""
      },
      "sequence": 4294967294
    }
  ],
  "vout": [
    {
      "value": 0.00010000,
      "n": 0,
      "scriptPubKey": {
        "asm": "OP_DUP OP_HASH160 344a0f48ca150ec2b903817660b9b68b13a67026 OP_EQUALVERIFY OP_CHECKSIG",
        "hex": "76a914344a0f48ca150ec2b903817660b9b68b13a6702688ac",
        "reqSigs": 1,
        "type": "pubkeyhash",
        "addresses": [
          "mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt"
        ]
      }
    },
    {
      "value": 0.01979574,
      "n": 1,
      "scriptPubKey": {
        "asm": "OP_HASH160 36903319b4aa2b9e2d9551811bd8b101fbf6640f OP_EQUAL",
        "hex": "a91436903319b4aa2b9e2d9551811bd8b101fbf6640f87",
        "reqSigs": 1,
        "type": "scripthash",
        "addresses": [
          "2MxDjDonPrZddU1HjHvehJS7Z72doGD96Gk"
        ]
      }
    }
  ]
}
```

The transaction now has an input sufficient to transfer 0.001 to our recipient, and it also has a change output sending the remaining tBTC back to us less fees.

Now it's time to sign the transaction. This is exactly the step where our CLI program will take over once we integrate JSON RPC with it. Same goes for the hardware wallet. But for this introduction we'll just have Bitcoin Core do the signing: 

```
tutorial signrawtransactionwithwallet 0200000001896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc02530100000000feffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f8700000000
{
  "hex": "02000000000101896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc0253010000001716001470637926f70cf907392e62fe857a0e324d40f34bfeffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f870247304402201c5dfc9cff549bc99b773b770a471f7abc01bc1390a17d1ad2027ca7fbbf397e0220494968186bfe1d0b591221c0a499d9f28a8c7dfe134ac0bcdf4e914234caff890121028793185ade8e1aa1a2adc54a970c4b7c470d3327b0387ce7f1808def4898607100000000",
  "complete": true
}
```

Now we broadcast to the network using `sendrawtransaction`:

```
$ tutorial sendrawtransaction 02000000000101896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc0253010000001716001470637926f70cf907392e62fe857a0e324d40f34bfeffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f870247304402201c5dfc9cff549bc99b773b770a471f7abc01bc1390a17d1ad2027ca7fbbf397e0220494968186bfe1d0b591221c0a499d9f28a8c7dfe134ac0bcdf4e914234caff890121028793185ade8e1aa1a2adc54a970c4b7c470d3327b0387ce7f1808def4898607100000000
```

Hopefully this gives you a high level overview how our wallet will work:
- Have bitcoin core prepare an unsigned transaction.
- Have bitcoin core fund it.
- Have our wallet (cli initially but eventually hardware wallet, where the huge security benefit comes in) sign it.
- Have bitcoin core broadcast it.

Notice how bitcoin doesn't even really need private keys to do any of this. There's a name for this kind of wallet: "watch-only". It moniters balances and utxos but cannot spend. That should be the hardware wallet's job!

Note: if you'd like to learn more about this kind of stuff, check out [this section of the "Learn Bitcoin From The Command Line" book](https://github.com/ChristopherA/Learning-Bitcoin-from-the-Command-Line/blob/master/04_0_Sending_Bitcoin_Transactions.md)

## JSON RPC From Python

Now that you have a high-level idea how our wallet will need to interact with your bitcoin node, let's learn to do this stuff from Python.

Enter the following into `rpc.py`, once again replacing `YOURUSERNAME` and `YOURPASSWORD` with the values you entered into your `~/.bitcoin/bitcoin.conf` at the beginning of this tutorial.

```
from bitcoinrpc.authproxy import AuthServiceProxy

rpc_template = "http://%s:%s@%s:%s/wallet/%s"
url = rpc_template % ('YOURUSERNAME', 'YOURPASSWORD', 'localhost', 18332, 'tutorial')
rpc = AuthServiceProxy(url)
```

`AuthServiceProxy` is a class which can make authenticated requests to Bitcoin Core's JSON RPC server. The single parameter it took is a connetion string which specifies the username, password, host, port, and wallet name we wish to connect to.


Now add the following two lines to the bottom of the file and run it:

```
print(rpc.listtransactions())
print(rpc.getbalance())
```

You should see the same transactions and balance printed as you saw from the command line.

### Spending From Python

This will do the whole manual transaction signing thing we covered earlier:

```
from rpc import rpc

# create unsigned transaction
inputs = []
outputs = [{"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt":"0.0001"}]
rawtx = rpc.createrawtransaction(inputs, outputs)

# add inputs and change output
fundedtx = rpc.fundrawtransaction(rawtx)['hex']

# sign it
signedtx = rpc.signrawtransactionwithwallet(fundedtx)['hex']

# broadcast it
result = rpc.sendrawtransaction(signedtx)
print("result:", result)
```

Pretty easy, huh?

Next step is to sign the transaction with our wallet. In the hardware wallet lesson this is exactly the place where we'll send the funded raw transaction to our hardware wallet for signing.

Since we'll be mostly doing JSON RPC with specific wallet names, let's start constructing a class which just takes a `wallet_name` variable and fills out the connection string using this variable:

## Watch-Only Wallet

Let's create another Bitcoin Core wallet which doesn't contain any private keys. But this one is watch-only:

```

```

Let's create a private key, derive a child key, and fund it.

```

```

Note that it doesn't show up in bitcoin core of course. We need to tell Bitcoin Core to watch for it.

One way would be to use `importaddress`, buy this requires lots of work. A better strategy is to use a descriptor to export a large range of addresses. <link>

```

```

Next, we need to tell Bitcoin Core to watch this descriptor

```

```

Your transaction should now show up. Let's spend it by signing from python:

```

```

This transaction should also show up in bitcoin core. Now we know all about running a Bitcoin Core watch-only wallet from Python. Let's now integrate these techniquest with the multi-account HD wallet we built in the previous tutorial:

## Integrating Our `rpc_hd` Wallet With JSON RPC

`cli.py` and `wallet.py` contain the finished versions of the cli and wallet from the past `cli_hd` multi-account HD wallet exercise. Let's start update them to work with your full node's JSON RPC.

## Update Wallet Constructor

Our watch-only wallet will need to export it's addresses to Bitcoin Core -- otherwise Bitconi Core won't know what UTXOs are ours. `bitcoin-cli` has an `importmulti` command which allows us to notify Bitcoin Core of a ["ranged descriptor"](https://github.com/bitcoin/bitcoin/blob/master/doc/descriptors.md) describing the transaction type, HD derivation path, and public keys of a range of addresses we control.

Our wallet contructor will need a parameter defining the size of this "range". Update `wallet.py` with this snippet:

```
...

class Wallet:

    filename = "wallet.json"

    def __init__(self, master_key, accounts, export_size):
        self.master_key = master_key
        self.accounts = accounts
        self.export_size = export_size

    @classmethod
    def create(cls, account_name, export_size=10):  # artificially low for testing
        if isfile(cls.filename):
            raise OSError("wallet file already exists")
        mnemonic, master_key = HDPrivateKey.generate(testnet=True)
        accounts = {}
        wallet = cls(master_key, accounts, export_size)
        wallet.register_account(account_name)
        return mnemonic, wallet
        
    def serialize(self):
        dict = {
            'master_key': self.master_key.serialize().hex(),
            'accounts': self.accounts,
            'export_size': self.export_size,
        }
        return json.dumps(dict, indent=4)

...
```

## Create / Load Our Watch-Only Wallet

Let's create a `WalletRPC` class which will be our interface for doing RPC with a specific Bitcoin Core wallet. `WalletRPC.rpc()` will return an `AuthServiceProxy` instance, but we'll try to only call this directly from inside the class. Any external callers will call WalletRPC methods which fills in whatever parameters make sense for our usecase.

```
import logging
from bitcoinrpc.authproxy import AuthServiceProxy

logger = logging.getLogger(__name__)

class WalletRPC:
    
    def __init__(self, account_name):
        self.wallet_name = 'buidl-' + account_name

    def rpc(self):
        rpc_template = "http://%s:%s@%s:%s/wallet/%s"
        url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, self.wallet_name)
        return AuthServiceProxy(url, timeout=60*5)  # 5 minute timeouts
    
    def load_wallet(self, account_name):
        try:
            return self.rpc().loadwallet(account_name)
        except JSONRPCException:
            logger.debug(f'"{account_name}" wallet already loaded')
    
    def create_watchonly_wallet(self, account_name):
        wallet_name = f'buidl-{account_name}'
        watchonly = True
        return self.rpc().createwallet(wallet_name, watchonly)

...
```

We create two methods on `WalletRPC`:
- `load_wallet`, which loads a previously created Bitcoin Core wallet. By default only the default `""` wallet is loaded.
- `create_wallet` which creates a watch-only Bitcoin Core wallet.

Let's exercise these methods from `wallet.py` where appropriate:

```

class Wallet:
    
    ...
    
    @classmethod
    def open(cls):
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            wallet = cls.deserialize(raw_json)
            for account_name in wallet.accounts.keys():
                WalletRPC('').load_wallet(account_name)
            return wallet

    def register_account(self, account_name):
        assert account_name not in self.accounts, 'account already registered'
        account_number = len(self.accounts)
        account = {
            'account_number': account_number,
            'receiving_index': 0,
            'change_index': 0,
        }
        WalletRPC('').create_watchonly_wallet(account_name)
        self.accounts[account_name] = account
        self.save()
    
    ...
```

Notes:
- When we open our wallet, we load the associated Bitcoin Core wallets for all our accounts. We use the default "" wallet because it's the only wallet that's is loaded by default in Bitcoin Core.
- When register accounts, we create a Bitcoin Core watch-only account for this account name.

## Generate & Export Addresses To Bitcoin Core

In order to export a chunk of addresses to Bitcoin Core watch-only wallets, we will exercise the `importmulti` rpc command. This command supports a few ways to communicate the addresses that we control. We can export pubkeys, addresses, scripts, or a descriptor.

Descriptors are a feature that was recently added to Bitcoin Core which allows you to export large ranges of addresses associated with BIP 32 derivation paths. Read the official wiki [here](https://github.com/bitcoin/bitcoin/blob/master/doc/descriptors.md). We'll use these for our wallet.

First, let's add a `Wallet.bitcoind_export` method which will call `importmulti` with a descriptor describing the addresses belonging to an account, and also add a `Wallet.descriptor` method that generates a descriptor for a given account:

```
...

class Wallet:
    
    ...
    
    def register_account(self, account_name):
        ...
        self.accounts[account_name] = account
        # create watch-only Bitcoin Core wallet and export first chunk of addresses
        WalletRPC('').create_watchonly_wallet(account_name)
        self.bitcoind_export(account_name, True)
        self.bitcoind_export(account_name, False)
        self.save()
        
    def descriptor(self, account_name, change):
        account_number = self.accounts[account_name]['account_number']
        account_path = f"m/44'/1'/{account_number}'"
        account_xpub = self.master_key.traverse(account_path.encode()).xpub()
        change = int(change)
        descriptor = f"pkh({account_xpub}/{change}/*)"
        return descriptor

    def bitcoind_export(self, account_name, change):
        account = self.accounts[account_name]
        descriptor = self.descriptor(account_name, change)
        address_index = account['change_index'] if change else account['receiving_index']
        export_range = (address_index, address_index + self.export_size)
        WalletRPC(account_name).export(descriptor, export_range, change)

    ...
    
    def consume_address(self, account_name, change):
        account = self.accounts[account_name]
        if change:
            address_index = account['change_index']
            account['change_index'] += 1
            if account['change_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
        else:
            address_index = account['receiving_index']
            account['receiving_index'] += 1
            if account['receiving_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)
    ...

```

Notes:
- Each method takes `account_name` and `change` arguments:
  - `account_name` corresponds to the account we're working with.
  - `change` is a boolean indicating whether we're exporting change or receiving addresses.
- We use a "pay-to-pubkey-hash" descriptor
- We use the `Wallet.export_size` variable to contruct the range or addresses we want to to express with out descriptor. This of this range as fillin in the `*` in the descriptor.
- We update `consume_address` to export another chunk of addresses if we're crossing an export boundary.

Now let's create a `WalletRPC.export` method which will call `importmulti`:

```
import time

...

class WalletRPC:

    ...
    
    def export(self, descriptor, range, change):
        # validate descriptor
        descriptor = self.rpc().getdescriptorinfo(descriptor)['descriptor']
        # export descriptor
        self.rpc().importmulti([{
            # description of the keys we're exporting
            "desc": descriptor,
            # go this far back in blockchain looking for matching outputs
            "timestamp": int(time.time() - 60*60*24*30),  # 30 days
            # this range kinda get filled into the * in the descriptor
            "range": range,
            # matching outputs will be marked "watchonly" meaning bitcoind's wallet can't spend them
            "watchonly": True,
            # bitcoind shouldn't use these addresses when we request an address from it
            "keypool": False,
            # whether it's a change address
            "internal": change,
        }])
        logger.debug(f'bitcoind export successful: descriptor={descriptor} range={range}')

```

Notes:
- Comments should describe each parameter we pass
- Just to be safe, we tell Bitcoin Core to rescan the past 30 days to look for UTXOs. This should really be a configuration option but this project is already getting too complicated!
- We log a debug-level statement when it's done

Let's test what we've got. We'll create 3 different accounts which will be exported as 3 different Bitcoin Core wallets:

```
$ python cli.py --account rpc1 
createowallet created. here is your mnemonic.
around wild weird gas churn fox guess fitness assault gather fly improve
your first receiving address: n1ZHwt9kBwDSeCcruyAUJKXkhk3yU4KJUb
$ python cli.py register rpc2
{'rpc1': {'account_number': 0, 'change_index': 0, 'receiving_index': 1},
 'rpc2': {'account_number': 1, 'change_index': 0, 'receiving_index': 0}}
$ python cli.py --account rpc2 address
n28LgYMy6U2mFyvkVn4yv3jiTKp7byuTDf
$ python cli.py register rpc3
{'rpc1': {'account_number': 0, 'change_index': 0, 'receiving_index': 1},
 'rpc2': {'account_number': 1, 'change_index': 0, 'receiving_index': 0},
 'rpc3': {'account_number': 2, 'change_index': 0, 'receiving_index': 0}}
$ python cli.py --account rpc3 address
n2wqGXwiPAWdaSjaK4sFxaCrAWFNAmqPbs
```

This first 3 commands should cause "rescanning" Bitcoin QT popups. They'll take a few seconds as the blockchain is rescanned looking for UTXOs.

Fund each address. You should receive desktop notification from Bitcoin QT each time, and they should show up in Bitcoin QT (there is a wallet selector in the top-right of the UI).

## Update Informational Methods

Now we need `WalletRPC` methods for fetching balances, transactions, and unspents:

```
...

from decimal import Decimal

...

COIN_PER_SAT = Decimal(10) ** -8
SAT_PER_COIN = 100_000_000

def btc_to_sat(btc):
    return int(btc*SAT_PER_COIN)

def sat_to_btc(sat):
    return Decimal(sat/100_000_000).quantize(COIN_PER_SAT)

...

class WalletRPC:
    
    ...
    
    def get_balance(self):
        watchonly
        confirmed = self.rpc().getbalance('*', 1, True)
        unconfirmed = self.rpc().getbalance('*', 0, True) - confirmed
        return btc_to_sat(unconfirmed), btc_to_sat(confirmed)

    def get_transactions(self):
        return self.rpc().listtransactions('*', 10, 0, True)

    def get_unspent(self):
        # this rpc method supports an addresses parameter ...
        unspent = self.rpc().listunspent()
        return [
                {'prev_tx': bytes.fromhex(tx['txid']),
                 'prev_index': tx['vout'],
                 'amount': btc_to_sat(tx['amount']),
                 'address': tx['address']}
            for tx in unspent
        ]

```

Notes:
- We add a helper functions for converting BTC to and from satoshis.
- Oddly, `getbalance('*', 0, True)` doesn't find unconfirmed transactions. This might be a [Bitcoin Core bug](https://bitcoin.stackexchange.com/questions/80926/update-to-0-17-0-broke-several-rpc-api-calls-that-worked-under-0-16-3-how-to-mi). Therefore, the unconfirmed balance will always be 0. I'll investigate and fix this soon.

Let's test it out:

```
$ python cli.py --account rpc1 transactions
['4a795549135063ce3463a83b77fb3bafee93d26dd9cc8334ebeeabd5b7467e24']
$ python cli.py --account rpc1 unspent
[{'address': 'n1ZHwt9kBwDSeCcruyAUJKXkhk3yU4KJUb',
  'amount': 1000000,
  'prev_index': 1,
  'prev_tx': b'JyUI\x13Pc\xce4c\xa8;w\xfb;\xaf\xee\x93\xd2m\xd9\xcc\x834'
             b'\xeb\xee\xab\xd5\xb7F~$'}]
$ python cli.py --account rpc1 balance
unconfirmed: 0
confirmed: 1000000
```

## Send Bitcoins

Now that Bitcoin Core is monitering a range of addresses for us, we'll be able to ask it to fund our transaction (select UTXOs as inputs to transactions) which will greatly reduce the complexity of our `Wallet.send` method.

To get started, delete the body of `Wallet.send` and replace it with:

```
from rpc import sat_to_btc

...

class Wallet:
    ...
    def send(self, account_name, address, amount, fee):
        rpc = WalletRPC(account_name)

        # create unfunded transaction
        tx_ins = []
        tx_outs = [
            {address: sat_to_btc(amount)},
        ]
        rawtx = rpc.create_raw_transaction(tx_ins, tx_outs)
        
        # fund it
        change_address = self.consume_address(account_name, True)
        fundedtx = rpc.fund_raw_transaction(rawtx, change_address)
        ...
```

This will fund transactions just like before, but will use Bitcoin Core's sophisticated coin selection algorithm for us!

Let's complete the method by signing the transaction and broadcasting over RPC:

```
from rpc import WalletRPC, sat_to_rpc

...

class Wallet:

    ...
    
    def send(self, account_name, address, amount, fee):
    
        ...
        
        # sign
        tx = Tx.parse(BytesIO(bytes.fromhex(fundedtx)), testnet=True)
        for index, tx_in in enumerate(tx.tx_ins):
            output_address = rpc.get_address_for_outpoint(tx_in.prev_tx.hex(), tx_in.prev_index)
            hd_private_key = self.lookup_key(account_name, output_address)
            assert tx.sign_input(index, hd_private_key.private_key)
        
        # broadcast
        rawtx = tx.serialize().hex()
        return rpc.broadcast(rawtx)
```

Lastly, we'll need to add a few `WalletRPC` methods:

```
class WalletRPC:

    ...
    
    def create_raw_transaction(self, tx_ins, tx_outs):
        return self.rpc().createrawtransaction(tx_ins, tx_outs)

    def fund_raw_transaction(self, rawtx, change_address):
        options = {'changeAddress': change_address, 'includeWatching': True}
        return self.rpc().fundrawtransaction(rawtx, options)['hex']

    def get_address_for_outpoint(self, txid, index):
        tx = self.rpc().getrawtransaction(txid, 1)
        raw_script_pubkey = tx['vout'][index]['scriptPubKey']['hex']
        return tx['vout'][index]['scriptPubKey']['addresses'][0]

    def broadcast(self, rawtx):
        return self.rpc().sendrawtransaction(rawtx)
```

Now you should be able to send coins and have everything show up in Bitcoin Core. Let's send 10000 satoshis from `rpc1` to `rpc2`:

```
$ python cli.py --account rpc2 address
myR5UYFJ28XNsJXv2WuCwW1LEyTJqNGQNY
$ python cli.py --account rpc1 send myR5UYFJ28XNsJXv2WuCwW1LEyTJqNGQNY 10000 500
69d513d255ce31427c90181c3b0742174f7ad8200bf3057254328a78269ad1c3
```

Voila! We now have a multi-account HD wallet connected to your full node. One step remains: move the secrets and transaction to a hardware wallet that that is much harder to hack than your desktop machine because it's not connected to the internet and doesn't have a modern operating system.

## Notes:

We never tested whether new chunks of addresses will be exported when an index crosses a multiple of `Wallet.export_size`. To do this, run the following command 10 times:

```
$ python cli.py --debug --account rpc2 address
mgxQqKMDr285GiC4VVnw2VoLnKiRRPs8Jd

...

$ python cli.py --debug --account rpc2 address
DEBUG:BitcoinRPC:-4-> getdescriptorinfo ["pkh(tpubDCeSUfeRBUgTScoC8cu6Xhh37hPmxdPEU1jApZEqZkvdr5WxWtNYokjNVHMg1G11hjvYJwAHHhFUpDt1H1eLcURjVsJzxJBfoQpQKRxE25Q/0/*)"]
DEBUG:BitcoinRPC:<-4- {"descriptor": "pkh(tpubDCeSUfeRBUgTScoC8cu6Xhh37hPmxdPEU1jApZEqZkvdr5WxWtNYokjNVHMg1G11hjvYJwAHHhFUpDt1H1eLcURjVsJzxJBfoQpQKRxE25Q/0/*)#4laypw8e", "isrange": true, "issolvable": true, "hasprivatekeys": false}
DEBUG:BitcoinRPC:-5-> importmulti [[{"desc": "pkh(tpubDCeSUfeRBUgTScoC8cu6Xhh37hPmxdPEU1jApZEqZkvdr5WxWtNYokjNVHMg1G11hjvYJwAHHhFUpDt1H1eLcURjVsJzxJBfoQpQKRxE25Q/0/*)#4laypw8e", "timestamp": 1562878644, "range": [20, 30], "watchonly": true, "keypool": false, "internal": false}]]
DEBUG:BitcoinRPC:<-5- [{"success": true}]
DEBUG:rpc:bitcoind export successful: descriptor=pkh(tpubDCeSUfeRBUgTScoC8cu6Xhh37hPmxdPEU1jApZEqZkvdr5WxWtNYokjNVHMg1G11hjvYJwAHHhFUpDt1H1eLcURjVsJzxJBfoQpQKRxE25Q/0/*)#4laypw8e range=(20, 30)
mjfqXtsrPHdbriEL6UhKxqut3RuMZeffCq
```
