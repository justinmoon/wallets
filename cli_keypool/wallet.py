from bedrock.ecc import N, PrivateKey

class KeyPool:

    def __init__(self, n, private_keys, index):
        self.n = n
        self.private_keys = private_keys
        self.index = index

    @classmethod
    def create(cls, n):
        keypool = cls(n, [], 0)
        keypool.fill()
        return keypool

    def fill(self):
        '''Generate N new private keys and add them to keypool'''
        for i in range(self.n):
            secret = randint(1, N)
            private_key = PrivateKey(secret)
            self.keys.append(private_key)

    def address(self):
        '''generate next address've run out'''
        # refill keypool if it's empty
        if self.index >= len(self.private_keys):
            self.fill()
        # fetch private key and increment index
        private_key = self.private_keys[self.index]
        self.index += 1
        # return testnet address
        return private_key.address(testnet=True)

class Wallet:

    def __init__(self, receiving_keypool, change_keypool):
        self.receiving_keypool = KeyPool()
        self.change_keypool = KeyPool()

    @classmethod
    def create(cls, n):
        receiving_keypool = KeyPool.create(n)
        change_keypool = KeyPool.create(n)
        return cls(receiving_keypool, change_keypool)

    def save(self):
        pass

    def load(self):
        pass

    def balance(self):
        pass

    def unspents(self):
        pass

    def transactions(self):
        pass

    def receiving_address(self):
        pass

    def change_address(self):
        pass

    def send(self, address, amount):
        pass
