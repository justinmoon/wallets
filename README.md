# Wallets

We will build a number of increasingly complex bitcoin wallets:

1. [`cli_simple`](./cli_simple) will generate new secrets for every address we use
2. [`cli_keypool`](./cli_keypool) will generate addresses in chunks, reducing the need for backup
3. [`cli_sd`](./cli_sd) will be a "sequential deterministic wallet" which hashes the master private key to derive an infinite chain of sequential child private keys
4. [`cli_hd`](./cli_hd) will use BIP32's "hierarchical deterministic" key derivation to produce a tree of child private keys from one master private key
5. [`cli_rpc`](./cli_rpc) modified our multi-account HD wallet to work with Bitcoin Core instead of 3rd party HTTP APIs.
6. [`m5stack`](./m5stack) will include basic exercises to learn to do the following with your m5stack:
    - install custom firmware with bitcoin primitives
    - upload micrpython files to the device
    - manipulate the display
    - respond to button presses
    - communite with desktop using serial port
    - use asyncio for concurrency (for example, listen to serial port and buttons at the same time)
    - access filesystem and SD card
7. `hw_simple` a basic hardware wallet with 1 private key which only signs legacy p2pkh & p2sh transactions
8. `hw_hd` a hierarchical deterministic wallet which signs segwit p2wpkh & p2wsh transactions 
9. `hd_psbt` modifies `hd_watch_only` to prepare [Partially Signed Bitcoin Transactions](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) using exported watch-only addresses and bitcoin core's coin selection algorithm. We will also do multisig using HWI with popular hardware wallets like Trezor & Coldcard.
