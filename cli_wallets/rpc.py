import time
from hd_rpc_wallet import *
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException


# FIXME
from bitpay import parse_script_pubkey, Unspent

rpc_template = "http://%s:%s@%s:%s/wallet/%s"
# regtest_url = rpc_template % ('bitcoin', 'python', 'localhost', 18443)
# regtest = AuthServiceProxy(regtest_url, timeout=60*5)  # 5 minute timeouts
default_url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, '')
default_rpc = AuthServiceProxy(default_url, timeout=60*5)  # 5 minute timeouts
wallet_url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, 'hd_rpc_wallet')
wallet_rpc = AuthServiceProxy(wallet_url, timeout=60*5)  # 5 minute timeouts


def load_watchonly():
    watch_only_name = 'hd_rpc_wallet'
    bitcoin_wallets = default_rpc.listwallets()
    if watch_only_name not in bitcoin_wallets:
        try:
            default_rpc.loadwallet(watch_only_name)
            print(f"Loaded watch-only Bitcoin Core wallet \"{watch_only_name}\"")
        except JSONRPCException as e:
            try:
                default_rpc.createwallet(watch_only_name, True)
                print(f"Created watch-only Bitcoin Core wallet \"{watch_only_name}\"")
            except JSONRPCException as e:
                # TODO: catch this in callers ...
                raise RuntimeError("Couldn't establish watch-only Bitcoin Core wallet")

def build_descriptor_w_fingerprint(hd_private_key, account_number):
    origin_path = "/84'/1'/0'"
    path_suffix = f"/{account_number}/*"
    fingerprint = hd_private_key.traverse(b"m/0'").pub.fingerprint.hex()
    xpub = hd_private_key.traverse(b"m" + origin_path.encode()).xpub()
    inner = f'[{fingerprint}{origin_path}]{xpub}{path_suffix}'
    raw_descriptor = f"pkh({inner})"
    print('raw_descriptor', raw_descriptor)
    # validates and appends checksum
    response = wallet_rpc.getdescriptorinfo(raw_descriptor)
    return response['descriptor']

def build_descriptor(hd_private_key, account_number):
    origin_path = "m/84'/1'/0'"
    xpub = hd_private_key.traverse(origin_path.encode()).xpub()
    path_suffix = f"/{account_number}/*"
    inner = f'{xpub}{path_suffix}'
    raw_descriptor = f"pkh({inner})"
    print('raw_descriptor', raw_descriptor)
    # validates and appends checksum
    response = wallet_rpc.getdescriptorinfo(raw_descriptor)
    return response['descriptor']

def export(hd_private_key, account_number, start, end):
    descriptor = build_descriptor(hd_private_key, account_number)
    print('exporting descriptor', descriptor)
    wallet_rpc.importmulti([{
        "desc": descriptor,
        # "timestamp": "now",  # FIXME
        "timestamp": int(time.time() - 60*60*24*30),  # 30 days
        "range": [start, end],
        "watchonly": True,
        "keypool": True,
        "internal": False,
    }])

# TODO: move to helpers
from decimal import Decimal, getcontext
SAT = Decimal(10) ** -8
def btc_to_sat(btc):
    return int(btc*100_000_000)

# TODO: move to helpers
def sat_to_btc(sat):
    return Decimal(sat / 100_000_000).quantize(SAT)

def display_btc(btc):
    return "{0:.8f}".format(btc)

def get_unspent():
    # this rpc method supports an addresses parameter ...
    unspent = wallet_rpc.listunspent()
    return [
        Unspent(tx_id=bytes.fromhex(tx['txid']),
                index=tx['vout'],
                amount=btc_to_sat(tx['amount']),
                script_pubkey=parse_script_pubkey(tx['scriptPubKey']))
        for tx in unspent
    ]

def get_transactions():
    return wallet_rpc.listtransactions('*', 10, 0, True)

def get_balance():
    return wallet_rpc.getbalance('*', 1, True)

def create_raw_transaction(tx_ins, tx_outs):
    return wallet_rpc.createrawtransaction(tx_ins, tx_outs)

def fund_raw_transaction(rawtx, change_address):
    options = {'changeAddress': change_address, 'includeWatching': True}
    return wallet_rpc.fundrawtransaction(rawtx, options)['hex']

def get_address_for_outpoint(txid, index):
    tx = wallet_rpc.getrawtransaction(txid, 1)
    raw_script_pubkey = tx['vout'][index]['scriptPubKey']['hex']
    script_pubkey = parse_script_pubkey(raw_script_pubkey)
    return script_pubkey.address(testnet=True)

def broadcast(rawtx):
    return wallet_rpc.sendrawtransaction(rawtx)
