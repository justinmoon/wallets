import sys
import json
from serial import Serial
from serial.tools import list_ports

def find_port():
    '''figure out which port to connect to'''
    ports = list(list_ports.grep('CP2104 USB to UART Bridge Controller'))
    if len(ports) > 1:
        raise OSError("too many devices plugged in")
    elif len(ports) == 0:
        raise OSError("no device plugged in")
    else:
        return ports[0].device

def send_and_recv(msg):
    # this is the connection to the serial port
    ser =  Serial(find_port(), baudrate=115200)
    # send msg to device
    ser.write(msg.encode() + b'\n')
    # get response from device
    while True:
        raw = ser.read_until(b'\n').strip(b'\n').decode()
        try:
            msg = json.loads(raw)
            return msg
        except:
            print('bad msg', raw)
            continue

def xpub():
    msg = json.dumps({'command': 'xpub'})
    print(send_and_recv(msg))

def address():
    msg = json.dumps({'command': 'address'})
    print(send_and_recv(msg))

def sign():
    address = '2N9dGmuuvGnNEWKYbpjxHruYuKvBPQzsRyq'
    amount = 1000

    from rpc import WalletRPC, sat_to_btc
    rpc = WalletRPC('hw_simple')

    # create unfunded transaction
    tx_ins = []
    tx_outs = [
        {address: sat_to_btc(amount)},
    ]
    rawtx = rpc.create_raw_transaction(tx_ins, tx_outs)

    # fund it
    change_address = 'n49fcB6UxepXvow8r7Dt19J9MHrZWwqHpd'
    fundedtx = rpc.fund_raw_transaction(rawtx, change_address)

    decoded = rpc.rpc().decoderawtransaction(fundedtx)
    tx_id = decoded['vin'][0]['txid']
    tx_index = decoded['vin'][0]['vout']

    tx_obj = rpc.rpc().getrawtransaction(tx_id, True)
    from bedrock.helper import encode_varstr
    script_pubkey = encode_varstr(bytes.fromhex(tx_obj['vout'][tx_index]['scriptPubKey']['hex'])).hex()
    print(script_pubkey)

    meta = [{'script_pubkey': script_pubkey}]
    msg = json.dumps({'command': 'sign', 'tx': fundedtx, 'meta': meta})
    res = send_and_recv(msg)
    print(rpc.broadcast(res['tx']))

if __name__ == '__main__':
    sign()
