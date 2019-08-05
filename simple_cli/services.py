import requests

from pprint import pprint

SMARTBIT = 'https://testnet-api.smartbit.com.au/v1/blockchain'
ADDRESS_URL = SMARTBIT + '/address/{}'
BALANCE_URL = ADDRESS_URL + '?limit=1'
UNSPENT_URL = ADDRESS_URL + '/unspent'

# smartbits doesn't have an endpoint to get transactions for multiple addresses
BITPAY = 'https://test-insight.bitpay.com/api'
TRANSACTION_URL = BITPAY + '/addrs/{}/txs'
BROADCAST_URL = BITPAY + '/tx/send'

def get(url):
    response = requests.get(url,)
    if response.status_code != 200:
        raise ConnectionError
    return response.json()

def post(url, data):
    response = requests.post(url, data)
    if response.status_code != 200:
        raise ConnectionError
    return response.json()

def get_balance(addresses):
    unconfirmed = 0
    confirmed = 0
    addresses = ','.join(addresses)
    data = get(ADDRESS_URL.format(addresses))
    if 'address' in data:
        addresses = [data['address']]
    else:
        addresses = data['addresses']
    for address in addresses:
        unconfirmed += address['unconfirmed']['balance_int']
        confirmed += address['confirmed']['balance_int']
    return unconfirmed, confirmed

def get_transactions(addresses):
    addresses = ','.join(addresses)
    return get(TRANSACTION_URL.format(addresses))['items']

def get_unspent(addresses):
    unspent = []
    addresses = ','.join(addresses)
    data = get(UNSPENT_URL.format(addresses))
    for tx in data['unspent']:
        # sanity check
        assert len(tx['addresses']) == 1
        # convert response to a dictionary w/ only parameters we care about
        unspent.append({
            # convert next two to formats used by TxIn class
            'prev_tx': bytes.fromhex(tx['txid']),
            'prev_index': tx['n'],
            'amount': tx['value_int'],
            'address': tx['addresses'][0],
        })
    return unspent

def broadcast(rawtx):
    data = {'rawtx': rawtx}
    response = post(BROADCAST_URL, data)
    return response['txid']
