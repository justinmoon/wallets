from bitcoinrpc.authproxy import AuthServiceProxy

rpc_template = "http://%s:%s@%s:%s/wallet/%s"
url = rpc_template % ('bitcoin', 'python', 'localhost', 18332, 'tutorial')
rpc = AuthServiceProxy(url)
