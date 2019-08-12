# RPC Wallet

## Requirements

You'll need a version 18.0 or higher Bitcoin Core node with a synced testnet chain for this exercise. Download Bitcoin Core [here](https://bitcoincore.org/en/download/), and sync the chain with `bitcoin-qt -testnet`.

## Introduction

In the last few lessons we've been working with a `services.py` file to access "the Bitcoin blockchain". But as you know, this isn't our blockchain: it's someone else's. We have no control over the software that is maintaining this blockchain. We are at the mercy of a 3rd party to decide our consensus rules for us. 

Using 3rd party services to access the blockchain goes against the design principals of Bitcoin. The whole design focuses on minimizing the costs of verifying the chain yourself. In this lesson we'll learn to connect to your Bitcoin core node using [JSON RPC](https://en.wikipedia.org/wiki/JSON-RPC), allowing us to connect to the bitcoin consensus implementation of our choice.

Once we've done this, we'll be able to offload some of the work to `bitcoind` -- the most well-maintained piece of software in the ecosystem. In particular, we'll have it do "coin selection" -- choose which UTXOs should be spent in a give transaction.

Let's get started:

## bitcoin-cli

First, add the following lines to your `~/.bitcoin/bitcoin.conf`, replacing the `YOURUSERNAME` and `YOURPASSWORD` with values of your choosing:

```
[test]
txindex=1
server=1
rpcuser=YOURPASSWORD
rpcpassword=YOURPASSWORD
```

Notes:
- `[test]` says that these options should only be active for the testnet chain.
- `server` tells bitcoin to run the JSON RPC server.
- The final two options set your RPC username and password. We'll need these to connect from Python.

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

The `help` command displays are all the available commands. Depending on which version of Bitcoin Core you're running, more or less commands will show up here.

The third command `getblockchaininfo` is basically `bitcoin-cli`'s "Hello, world!".

### `getblockchaininfo`

Run `bitcoin-cli help getblockchaininfo` to see a more detailed description of the this method.

TLDR it displays some state about your node. Very useful to see if you're synced to the tip or not:

If you just run `bitcoin-cli getblockchaininfo` it will query your mainnet node. To query your testnet node you must pass a `-testnet` flag:

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

Bitcoin Core supports the creation of multiple wallets. The default wallet is simply named the empty string: `""`. Let's create a new wallet for these exercises so that we don't interfere with any existing testnet coins you may have. Plus, we'll liberally make use of this command later in the lesson. Run `bitcoin-cli help createwallet` to learn more about this command. The first parameter is the wallet name. Let's call ours "tutorial". The second parameter says whether private keys should be disabled for the wallet. We'll keep private keys enabled for now, but later on in the tutorial we'll disable them and handle private keys in out CLI wallet, and eventually on our m5stack hardware wallet.

```
$ bitcoin-cli -testnet createwallet tutorial
{
  "name": "tutorial",
  "warning": ""
}
```

Note: the command returns JSON. That's because under the hood `bitcoin-cli` is simply doing JSON RPC.

## Set an alias

In order to query our "tutorial" testnet wallet's balance, we need to type the long command `bitcoin-cli -testnet -rpcwallet=tutorial getbalance`. That's cumbersome. Let's create a bash alias for the command: 

```
alias tutorial="bitcoin-cli -testnet -rpcwallet=tutorial getbalance"
```

Now we just have to type `tutorial getbalance`. But remember: if you reopen your terminal you'll have to redefine this alias. If you want aliases like this to be permanent, stick it in your `~/.bashrc`.

## `getnewaddress`

If you executed the `getbalance` command in the previous section you probably saw that you balance was zero. Let's fix this!

To fund you wallet you'll need to generate an address:

```
$ tutorial getnewaddress
2N5zVhSRjtGUN2jdR8G33H2Hx5sFrBBNn6x
```

Hop on over to our trusty [testnet faucet](https://testnet-faucet.mempool.co) and send yourself some tBTC. After doing so, they'll show up in `listtransactions` and after they confirm they'll show up in `getbalance` (I sent myself two 0.01 tBTC transactions in this example):

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

The previous command returns returns the serialized hex of the unfunded (no inputs), unsigned transaction (inputs need to be signed and we don't have any inputs yet!). We can decode it like this:

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

The transaction now has an input sufficient to transfer 0.001 to our recipient, and it also has a change output sending the remaining tBTC back to us less fees. But it's still unsigned: the lone input's `scriptSig` (script signature) values are empty.

Now it's time to sign the transaction. This is exactly the step where our CLI program will take over once we integrate JSON RPC with it. Same goes for the hardware wallet. But for this introduction we'll just have Bitcoin Core do the signing: 

```
tutorial signrawtransactionwithwallet 0200000001896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc02530100000000feffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f8700000000
{
  "hex": "02000000000101896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc0253010000001716001470637926f70cf907392e62fe857a0e324d40f34bfeffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f870247304402201c5dfc9cff549bc99b773b770a471f7abc01bc1390a17d1ad2027ca7fbbf397e0220494968186bfe1d0b591221c0a499d9f28a8c7dfe134ac0bcdf4e914234caff890121028793185ade8e1aa1a2adc54a970c4b7c470d3327b0387ce7f1808def4898607100000000",
  "complete": true
}
```

Now we broadcast the raw hex from the previous step to the network using `sendrawtransaction`:

```
$ tutorial sendrawtransaction 02000000000101896f5476926b1feeb1554722b9f5b40bfbd876751e3b203f4e2959184cdc0253010000001716001470637926f70cf907392e62fe857a0e324d40f34bfeffffff0210270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688acb6341e000000000017a91436903319b4aa2b9e2d9551811bd8b101fbf6640f870247304402201c5dfc9cff549bc99b773b770a471f7abc01bc1390a17d1ad2027ca7fbbf397e0220494968186bfe1d0b591221c0a499d9f28a8c7dfe134ac0bcdf4e914234caff890121028793185ade8e1aa1a2adc54a970c4b7c470d3327b0387ce7f1808def4898607100000000
```

Hopefully this gives you a high level overview how our wallet will work:
- Bitcoin Core prepares an unsigned transaction.
- Bitcoin Core funds it.
- Our wallet (CLI wallet initially but hardware wallet eventually) sign it.
- Bitcoin Core broadcasts it.

Notice how Bitcoin Core doesn't even really need private keys to do any of this, since it doesn't handle signing transactions. There's a name for this kind of wallet: "watch-only". It moniters balances and utxos but cannot spend because it only knows about public keys, addresses and scripts -- but not private keys. That should be the hardware wallet's job!

Note: if you'd like to learn more about this kind of stuff, check out [this section of the "Learn Bitcoin From The Command Line" book](https://github.com/ChristopherA/Learning-Bitcoin-from-the-Command-Line/blob/master/04_0_Sending_Bitcoin_Transactions.md)

## JSON RPC From Python

Now that you have a high-level idea how our wallet will need to interact with your bitcoin node, let's learn to do this stuff from Python.

### Connecting To JSON RPC Server

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

You should see the same transactions and balance printed as you saw using `bitcoin-cli` above.

### Spending From Python

This short script will execute manual transaction signing process we covered earlier from the command line:

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

## Integrating Our `rpc_hd` Wallet With JSON RPC

[`cli.py`](./cli.py) and [`wallet.py`](./wallet.py) contain the finished versions of the CLI and wallet implementations from the previous `cli_hd` multi-account HD wallet exercise. Let's start update them to work with your full node's JSON RPC.

### Update Wallet Constructor

Our watch-only wallet will need to export it's addresses to Bitcoin Core -- otherwise Bitconi Core won't know what UTXOs we're interested in.

`bitcoin-cli` has an `importmulti` command which allows us to notify Bitcoin Core of a ["descriptor"](https://github.com/bitcoin/bitcoin/blob/master/doc/descriptors.md) describing the transaction type, HD derivation path, and public keys of a range of addresses we control.

Our wallet contructor will need a parameter defining the size of this "range". Update `wallet.py` with this snippet. For instance, when we first create our wallet, we'll export `Wallet.export_size`-many addresses to Bitcoin Core. Every time we've used them up, we'll repeat:

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

Notes:
- We set a very low default `export_size` of 10 so that we can easily test exhausting exported addresses.

## Create / Load Our Watch-Only Wallet

Let's create a `WalletRPC` class which will be our interface for doing RPC with a specific Bitcoin Core wallet. `WalletRPC.rpc()` will return an `AuthServiceProxy` instance, but we'll try to only call this directly from inside the class. Any external callers will call `WalletRPC` methods which fills in whatever parameters make sense for our usecase.

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
- If we try to load a wallet that's already loaded, an exception is raised by the `python-bitcoinrpc` we're using. We catch that exception and log a debug statement.
- `create_watchonly_wallet` which creates a watch-only Bitcoin Core wallet by feeding `createwallet` a second `True` variable.

Let's exercise these methods from `wallet.py` where appropriate:

```

class Wallet:
    
    ...
    
    @classmethod
    def open(cls):
        with open(cls.filename, 'r') as f:
            raw_json = f.read()
            wallet = cls.deserialize(raw_json)
            # load associated Bitcoin Core watch-only wallets
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
        # create associated Bitcoin Core watch-only wallet
        WalletRPC('').create_watchonly_wallet(account_name)
        self.accounts[account_name] = account
        self.save()
    
    ...
```

Notes:
- When we open our wallet, we load the associated Bitcoin Core wallets for all our accounts. We use the default `""` wallet because it's the only wallet that's is loaded by default.
- When registering accounts, we create a Bitcoin Core watch-only account for the account name.

## Generate & Export Addresses To Bitcoin Core

In order to export a chunk of addresses to Bitcoin Core watch-only wallets, we will exercise the `importmulti` rpc command. This command supports a few ways to communicate the addresses that we control. We can export pubkeys, addresses, scripts, or a "descriptor".

Descriptors are a feature that was recently added to Bitcoin Core which allows you to express large ranges of addresses associated with BIP 32 derivation paths. Read the official wiki [here](https://github.com/bitcoin/bitcoin/blob/master/doc/descriptors.md). We'll use these to communicate which addresses we want Bitcoin Core watch-only wallets to watch for us.

First, let's add a `Wallet.bitcoind_export` method which will call `importmulti` with a descriptor describing the addresses belonging to an account, and also add a `Wallet.descriptor` method that generates a descriptor for a given account:

```
...

class Wallet:
    
    ...
    
    def register_account(self, account_name):
        ...
        self.accounts[account_name] = account
        # create watch-only Bitcoin Core wallet
        WalletRPC('').create_watchonly_wallet(account_name)
        # export first chunk of receiving & change addresses
        self.bitcoind_export(account_name, True)
        self.bitcoind_export(account_name, False)
        self.save()
        
    def descriptor(self, account_name, change):
        account_number = self.accounts[account_name]['account_number']
        account_path = f"m/44'/1'/{account_number}'".encode()
        account_xpub = self.master_key.traverse(account_path).xpub()
        change = int(change)
        descriptor = f"pkh({account_xpub}/{change}/*)"
        return descriptor

    def bitcoind_export(self, account_name, change):
        account = self.accounts[account_name]
        descriptor = self.descriptor(account_name, change)
        address_index = account['change_index'] if change else account['receiving_index']
        export_range = (address_index, address_index + self.export_size)
        WalletRPC(account_name).export(descriptor, export_range, change)  # doesn't exist yet

    ...
    
    def consume_address(self, account_name, change):
        account = self.accounts[account_name]
        if change:
            address_index = account['change_index']
            if account['change_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
            account['change_index'] += 1
        else:
            address_index = account['receiving_index']
            if account['receiving_index'] % self.export_size == 0:
                self.bitcoind_export(account_name, change)
            account['receiving_index'] += 1
        key = self.derive_key(account_name, change, address_index)
        self.save()
        return key.pub.point.address(testnet=True)
    ...

```

Notes:
- Each method takes `account_name`, and every once except `register_account` takes a `change` arguments:
  - `account_name` corresponds to the account we're working with.
  - `change` is a boolean indicating whether we're exporting change or receiving addresses.
- We use a "pay-to-pubkey-hash" descriptor of form `pkh(...)`.
- We use the `Wallet.export_size` variable to contruct the range of addresses we want to to express with out descriptor. Think of this range as filling in the `*` in the descriptor.
    - For example, the first time this is called with `change=True` for the first account in a wallet that hasn't consumed any addresses yet, our descriptor exports keys from `m/44'/1'/0'/1/0` to `m/44'/1'/0'/1/10`, assuming `Wallet.export_size` is set to the default value of 10.
- We update `consume_address` to export another chunk of addresses if we're crossing an export boundary. This is admittedly ugly ...

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
- `getdescriptorinfo` validates our descriptor and appends a checksum to it.
- Comments should adequately describe each parameter passed to `importmulti`.
- Just to be safe, we tell Bitcoin Core to rescan the past 30 days to looking for UTXOs we control. This should really be a configuration option ...
- We log a debug-level statement when it's done.

Let's test what we've got. We'll create 3 different accounts which will create 3 different Bitcoin Core wallets:

```
$ python cli.py --account rpc1 create
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

The first 3 `create` and `register` commands should cause "rescanning" Bitcoin QT popups. They'll take a few seconds as the blockchain is searched looking for matching UTXOs.

Next we fund each address. You should receive desktop notification from Bitcoin QT each time, and the transactions should show up in Bitcoin QT (there is a wallet selector in the top-right of the UI which allows you to toggle between different wallets).

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
        confirmed = self.rpc().getbalance('*', 1, True)
        unconfirmed = self.rpc().getbalance('*', 0, True) - confirmed
        return btc_to_sat(unconfirmed), btc_to_sat(confirmed)

    def get_transactions(self):
        return self.rpc().listtransactions('*', 10, 0, True)

    def get_unspent(self):
        return self.rpc().listunspent()

```

Notes:
- We add a helper functions for converting BTC to and from satoshis.
- Oddly, `getbalance('*', 0, True)` doesn't find unconfirmed transactions, even though we set the second `confirmations` parameter to `0`. This might be a [Bitcoin Core bug](https://bitcoin.stackexchange.com/questions/80926/update-to-0-17-0-broke-several-rpc-api-calls-that-worked-under-0-16-3-how-to-mi). Therefore, the unconfirmed balance will always be 0. I'll investigate and fix this soon.
- `get_unspent` doesn't attempt to convert any of the data like `services.get_unspent` did because we won't be directly dealing with unspent transactions in this iterations. This work will be outsourced to Bitcoin Core. But we still implement the method for feature parity

Let's test it out:

```
$ python cli.py --account rpc1 transactions
['4a795549135063ce3463a83b77fb3bafee93d26dd9cc8334ebeeabd5b7467e24']
$ python cli.py --account rpc1 unspent
...
$ python cli.py --account rpc1 balance
unconfirmed: 0
confirmed: 1000000
```

Notes:
- The `unspent` command's output contains a `"desc"` field. Get used to these things!

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
from io import BytesIO
from bedrock.tx import Tx

...

class WalletRPC:

    ...
    
    def create_raw_transaction(self, tx_ins, tx_outs):
        return self.rpc().createrawtransaction(tx_ins, tx_outs)

    def fund_raw_transaction(self, rawtx, change_address):
        options = {'changeAddress': change_address, 'includeWatching': True}
        return self.rpc().fundrawtransaction(rawtx, options)['hex']

    def get_address_for_outpoint(self, txid, index):
        rawtx = self.rpc().gettransaction(txid)['hex']
        tx = Tx.parse(BytesIO(bytes.fromhex(rawtx)))
        tx_out = tx.tx_outs[index]
        script_pubkey = tx_out.script_pubkey
        return script_pubkey.address(testnet=True)

    def broadcast(self, rawtx):
        return self.rpc().sendrawtransaction(rawtx)
```

Notes:
- `get_address_for_output` is complicated because we must derive an address from a raw transaction because `bitcoin-cli` doesn't provide addresses in the response to `gettransaction` -- it's method for looking up wallet transactions. If your testnet node has `txindex=1` parameter set, you could use `getrawtransaction`, which can lookup any transaction and which does return the address.

Now you should be able to send coins and have everything show up in Bitcoin Core. Let's send 10000 satoshis from `rpc1` to `rpc2`:

```
$ python cli.py --account rpc2 address
myR5UYFJ28XNsJXv2WuCwW1LEyTJqNGQNY
$ python cli.py --account rpc1 send myR5UYFJ28XNsJXv2WuCwW1LEyTJqNGQNY 10000 500
69d513d255ce31427c90181c3b0742174f7ad8200bf3057254328a78269ad1c3
```

Voila! We now have a multi-account HD wallet connected to your full node. One step remains: move the secrets and transaction signing to a hardware wallet that that is much harder to hack than your desktop machine because it's not connected to the internet and doesn't have a complex (backdoored) modern operating system.

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

It works!
