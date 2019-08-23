import time
from io import BytesIO

from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from bedrock.hd import HDPublicKey

rpc_template = "http://%s:%s@%s:%s/wallet/%s"
url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, 'hw_simple')
rpc = AuthServiceProxy(url, timeout=60*5)  # 5 minute timeouts

if __name__ == '__main__':
    account_xpub = 'tpubDBdFuvocSnGkestv95nKxDkM5B2B55gZeEiGmN1fxSiZ2nzYkeeRoY4NewDv3h4fPQDre3V3XCGWVnzQpYQFbENWhxTvcfySPqguxRdBeTr'
    descriptor = f"pkh({account_xpub}/0/*)"
    descriptor = rpc.getdescriptorinfo(descriptor)['descriptor']

    # export descriptor
    rpc.importmulti([{
        # description of the keys we're exporting
        "desc": descriptor,
        # go this far back in blockchain looking for matching outputs
        "timestamp": int(time.time() - 60*60*24*30),  # 30 days
        # this range kinda get filled into the * in the descriptor
        "range": [0, 100],
        # matching outputs will be marked "watchonly" meaning bitcoind's wallet can't spend them
        "watchonly": True,
        # bitcoind shouldn't use these addresses when we request an address from it
        "keypool": False,
        # whether it's a change address
        "internal": False,
    }])

