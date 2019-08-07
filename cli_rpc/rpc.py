import time
import logging

from decimal import Decimal, getcontext

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

rpc_template = "http://%s:%s@%s:%s/wallet/%s"
bitcoind_wallet_name = 'hd_rpc'
default_url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, '')
default_rpc = AuthServiceProxy(default_url, timeout=60*5)  # 5 minute timeouts
wallet_url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, bitcoind_wallet_name)
wallet_rpc = AuthServiceProxy(wallet_url, timeout=60*5)  # 5 minute timeouts

logger = logging.getLogger(__name__)

COIN_PER_SAT = Decimal(10) ** -8
SAT_PER_COIN = 100_000_000

def btc_to_sat(btc):
    return int(btc*SAT_PER_COIN)

def sat_to_btc(sat):
    return Decimal(sat/100_000_000).quantize(COIN_PER_SAT)

def load_watchonly():
    bitcoind_wallets = default_rpc.listwallets()
    if bitcoind_wallet_name not in bitcoind_wallets:
        try:
            default_rpc.loadwallet(bitcoind_wallet_name)
            logger.debug(f"Loaded watch-only Bitcoin Core wallet \"{bitcoind_wallet_name}\"")
        except JSONRPCException as e:
            try:
                default_rpc.createwallet(bitcoind_wallet_name, True)
                logger.debug(f"Created watch-only Bitcoin Core wallet \"{bitcoind_wallet_name}\"")
            except JSONRPCException as e:
                raise RuntimeError("Couldn't establish watch-only Bitcoin Core wallet")
    else:
        logger.debug(f"Watch-only Bitcoin Core wallet \"{bitcoind_wallet_name}\" already loaded")

def export(descriptor, range, change):
    # validate descriptor
    descriptor = wallet_rpc.getdescriptorinfo(descriptor)['descriptor']
    wallet_rpc.importmulti([{
        # description of the keys we're exporting
        "desc": descriptor,
        # go this far back in blockchain looking for matching outputs
        "timestamp": int(time.time() - 60*60*24*30),  # 30 days
        # this range kinda get filled into the * in the descriptor
        # FIXME
        # "range": range,
        "range": [0, 1000],
        # matching outputs will be marked "watchonly" meaning bitcoind's wallet can't spend them
        "watchonly": True,
        # bitcoind shouldn't use these addresses when we request an address from it
        "keypool": False,
        # whether it's a change address
        "internal": change,
    }])
    logger.debug(f'bitcoind export successful: descriptor={descriptor} range={range}')

def get_balance():
    confirmed = wallet_rpc.getbalance('*', 1, True)
    unconfirmed = wallet_rpc.getbalance('*', 0, True) - confirmed
    return btc_to_sat(unconfirmed), btc_to_sat(confirmed)

def get_transactions():
    return wallet_rpc.listtransactions('*', 10, 0, True)

def get_unspent():
    # this rpc method supports an addresses parameter ...
    unspent = wallet_rpc.listunspent()
    return [
            {'prev_tx': bytes.fromhex(tx['txid']),
             'prev_index': tx['vout'],
             'amount': btc_to_sat(tx['amount']),
             'address': tx['address']}
        for tx in unspent
    ]

def create_raw_transaction(tx_ins, tx_outs):
    return wallet_rpc.createrawtransaction(tx_ins, tx_outs)

def fund_raw_transaction(rawtx, change_address):
    options = {'changeAddress': change_address, 'includeWatching': True}
    return wallet_rpc.fundrawtransaction(rawtx, options)['hex']

def get_address_for_outpoint(txid, index):
    tx = wallet_rpc.getrawtransaction(txid, 1)
    raw_script_pubkey = tx['vout'][index]['scriptPubKey']['hex']
    return tx['vout'][index]['scriptPubKey']['addresses'][0]

def broadcast(rawtx):
    return wallet_rpc.sendrawtransaction(rawtx)
