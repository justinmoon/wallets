# RPC Wallet

## Requirements

You'll need a bitcoin core node with a synced testnet chain for this exercise. Download Bitcoin Core [here](https://bitcoincore.org/en/download/) if you don't have it installed already, and sync the chain with `bitcoin-qt -testnet`. Syncing is finished when the `headers` and `blocks` attributes of the response to `bitcoin-cli -testnet getblockchaininfo` are equal.

## Introduction

In the last few lessons we've been working with a `services.py` file to access "the bitcoin blockchain". But as you know, this isn't our blockchain: it's someone else's. We have no control over the software that is maintaining this blockchain. We are at the mercy of a 3rd party to decide our consensus rules for us. 

But this is Bitcoin. The whole design is focuses on minimizing the costs of verifying the chain yourself. In this lesson we'll learn to connect to your Bitcoin core node using [JSON RPC](https://en.wikipedia.org/wiki/JSON-RPC). We'll be able to connect to the bitcoin consensus implementation of our choice.

Once we've done this, we'll be able to offload some of the work to bitcoind -- the most well-maintained piece of software in the ecosystem. In particular, we'll have it generate receiving addresses and select which UTXO we should spend. The second of these two is a huge improvement. So far we've always spent the first available UTXO returned to us, but many better heuristics exist and some of these are implemented by Bitcoin Core.

Let's get started:

## `bitcoin-cli`

First, add the following lines to your `~/.bitcoin/bitcoin.conf`, replacing the `YOURUSERNAME` and `YOURPASSWORD` with values of your choosing:

```
[test]
server=1
rpcuser=YOURPASSWORD
rpcpassword=YOURPASSWORD
```

`server` tells bitcoin to run the JSON RPC server and the other two set your username and password for RPC.

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

These are all the available commands. Depending on which version of Bitcoin Core you're running and the options you've set in your `bitcoin.conf` configuration file, more or less commands will show up here.

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

Bitcoin Core supports the creation of multiple wallets. The default wallet is simply named the empty string: "". Let's create a new wallet for these exercises so that we don't interfere with any existing testnet coins you may have. Plus, we'll liberally make use of this command later in the less. Run `bitcoin-cli help createwallet` to learn more about this command. The first parameter is the wallet name. Let's call ours "tutorial". The second parameter says whether private keys should be disabled for the wallet. We'll keep private keys enabled for now, but later on in the tutorial we'll disable them and handle private keys in out CLI wallet, and eventually on our m5stack hardware wallet.

```
$ bitcoin-cli -testnet createwallet tutorial
{
  "name": "tutorial",
  "warning": ""
}
```

Note: the command returns JSON. That's because under the hood `bitcoin-cli` is simply doing JSON RPC.

## Set an alias

In order to query our "tutorial" testnet wallet's balance, we need to type the long command `bitcoin-cli -testnet -rpcwallet=tutorial getbalance`. That's cumbersome. It may help to create a bash alias for the command: `alias tutorial="bitcoin-cli -testnet -rpcwallet=tutorial"`. Then you'd just have to type `tutorial getbalance`. But I'll continue to type the full commands out in the tutorial.

## `getnewaddress`

If you executed the `getbalance` command in the previous section you probably saw that you balance was zero. Let's fix this!

To fund you wallet you'll need to generate an address:

```
$ bitcoin-cli -testnet -rpcwallet=tutorial getnewaddress
2N5zVhSRjtGUN2jdR8G33H2Hx5sFrBBNn6x
```

Hop on over to our trusty [testnet faucet](https://testnet-faucet.mempool.co) and send yourself some tBTC. After doing so, they'll show up in `listtransactions` and after they confirm they'll show up in `getbalance`:

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

No work required using this approach:

```
$ tutorial sendtoaddress mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt 0.0001
5302dc4c1859294e3f203b1e7576d8fb0bb4f5b9224755b1ee1f6b9276546f89
```

### Manual Sending

But there are commands to give you more control over how the transaction is constructed and signed. For instance, we could create an unsigned transaction with no inputs and one output sending 0.0001 tBTC to the faucet's receiving address mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt like this:

```
$ tutorial createrawtransaction "[]" '[{"mkHS9ne12qx9pS9VojpwU5xtRd4T7X7ZUt":"0.0001"}]'
02000000000110270000000000001976a914344a0f48ca150ec2b903817660b9b68b13a6702688ac00000000
```

It returns the serialized hex of the transaction. We can decode it like this:

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

Just as we expected: no inputs, one output with address and amount matching what we specified. In order to sign this transaction, we need to fill in an input. Let's ask the Bitcoin Core wallet to do this for us:

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
- Have bitcoin core prepare an unsigned transaction
- Have bitcoin core fund it
- Have our wallet (cli but eventually hardware wallet, where the huge security benefit comes in) sign it
- Have bitcoin core broadcast it

Notice how bitcoin doesn't even really need private keys to do any of this. There's a name for this kind of wallet: "watch-only". It moniters balances and utxos but cannot spend. That's the hardware wallet's job!

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

## Update Wallet Constructor

## Create / Load Our Watch-Only Wallet

## Generate & Export Addresses To Bitcoin Core

... fund it 

## Update Informational Methods

## Send Bitcoins

## WalletRPC Class


```
class WalletRPC:
    
    def __init__(self, account_name):
        self.wallet_name = 'buidl-' + account_name

    def rpc(self):
        rpc_template = "http://%s:%s@%s:%s/wallet/%s"
        url = rpc_template % ('YOURUSERNAME', 'YOURPASSWORD', 'localhost', 18332, self.wallet_name)
        return AuthServiceProxy(url, timeout=60*5)  # 5 minute timeouts

        
rpc = WalletRPC('tutorial')

print(rpc.rpc().getbalance())
print(rpc.rpc().gettransactions())
```

This is a little cludgy, but the idea will be to add methods for all the specific operations we want and not call `WalletRPC.rpc()` directly from outside the class.


- create watchonly
- generate address (or reverse order with previous step?)
- (fund it)
- watch-only export so that the outputs show up in our wallet
- get balance, unspent, transactions
- Wallet.send


Questions:
- when to change wallet constructor?


Let's add some methods we used for 

# Issues

`getbalance` doesn't show unconfirmed balance even if you set `min_conf` to 0 b/c bug: https://bitcoin.stackexchange.com/questions/80926/update-to-0-17-0-broke-several-rpc-api-calls-that-worked-under-0-16-3-how-to-mi. For some reason, `getunconfirmedbalance` also doesn't work for me. ^^ shows a new, unreleased (getbalances) which will be released in bitcoin 18.1.
