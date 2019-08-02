from io import BytesIO

from requests import get, post
from bedrock.helper import encode_varstr
from bedrock.script import Script

# FIXME: use blockstream.info's api
BASE_URL = 'https://test-insight.bitpay.com/api'
ADDRESS_URL = BASE_URL + '/addr/{}'
BALANCE_URL = ADDRESS_URL + '/balance'
UNSPENT_URL = ADDRESS_URL + '/utxo'
TXS_URL = BASE_URL + '/addrs/{}/txs'
TIMEOUT = 5
BROADCAST_URL = BASE_URL + '/tx/send'

# BASE_URL = 'https://blockstream.info/testnet/api'
# ADDRESS_URL = BASE_URL + '/address/{}'
# UNSPENT_URL = ADDRESS_URL + '/utxo'


def get_balance(address):
    r = get(BALANCE_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()

class Unspent:

    def __init__(self, tx_id, index, amount, script_pubkey):
        self.tx_id = tx_id
        self.index = index
        self.amount = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return f'Unspent(output={self.tx_id.hex()}:{self.index} amount={self.amount})'

def broadcast(rawtx):
    data = {'rawtx': rawtx}
    r = post(BROADCAST_URL, data=data, timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()

def parse_script_pubkey(s):
    return Script.parse(BytesIO(encode_varstr(bytes.fromhex(s))))

def get_unspent(address):
    r = get(UNSPENT_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return [
        Unspent(tx_id=bytes.fromhex(tx['txid']),
                index=tx['vout'],
                amount=tx['satoshis'],
                script_pubkey=parse_script_pubkey(tx['scriptPubKey']))
        for tx in r.json()
    ]

def get_transactions(address):
    r = get(ADDRESS_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()['transactions']

def get_full_transactions(addresses):
    addresses = ''.join(addresses)
    r = get(TXS_URL.format(addresses), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    print(r.json())
    return r.json()['items']