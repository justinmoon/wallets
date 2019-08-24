import os
import json
import time
import uasyncio

from sys import stdin, stdout
from io import BytesIO
from binascii import unhexlify, hexlify

from asyn import Event
from m5stack import LCD, fonts, color565, SDCard, buttons
from bitcoin.mnemonic import secure_mnemonic
from bitcoin.hd import HDPrivateKey
from bitcoin.tx import Tx
from bitcoin.script import Script

# globals
lcd = LCD()
SIGN_IT = Event()
DONT_SIGN_IT = Event()
KEY = None

# TODO: I need a router class that keeps track of history, can go "back"
class Screen:
    '''Abstract base class for different screens in the wallet'''

    def a_release(self):
        pass

    def b_release(self):
        pass

    def c_release(self):
        pass

    def render(self):
        raise NotImplementedError()

    def visit(self):
        '''router function sets button callbacks and renders screen'''
        buttons.A.release_func(self.a_release)
        buttons.B.release_func(self.b_release)
        buttons.C.release_func(self.c_release)
        self.render()

class TraverseScreen(Screen):

    def __init__(self, address_index=0, address_type='legacy'):
        self.address_index = address_index
        self.address_type = address_type

    def a_release(self):
        '''decrement address index'''
        if self.address_index != 0:
            TraverseScreen(self.address_index - 1, self.address_type).visit()

    def b_release(self):
        '''flip address type'''
        address_type = 'bech32' if self.address_type == 'legacy' else 'legacy'
        TraverseScreen(self.address_index, address_type).visit()

    def c_release(self):
        '''increment address index'''
        TraverseScreen(self.address_index + 1, self.address_type).visit()
    
    def render(self):
        # calculate address and derivation path
        path = "m/44'/1'/0'/{}".format(self.address_index).encode()
        child = KEY.traverse(path)
        address = child.address() if self.address_type == 'legacy' else child.bech32_address()

        # print
        lcd.erase()
        lcd.set_font(fonts.tt24)
        lcd.set_pos(20, 20)
        lcd.print(path.decode())
        lcd.print(address)

        a = 'prev' if self.address_index > 0 else ''
        b = 'segwit' if self.address_type == 'legacy' else 'legacy'
        lcd.label_buttons(a, b, 'next')

class MnemonicScreen(Screen):

    def __init__(self, mnemonic):
        self.mnemonic = mnemonic

    def on_verify(self):
        '''display addresses once they've confirmed mnemonic'''
        # FIXME: slow, display loading screen
        save_key(self.mnemonic)
        TraverseScreen().visit()

    def a_release(self):
        self.on_verify()

    def b_release(self):
        self.on_verify()

    def c_release(self):
        self.on_verify()
    
    def render(self):
        lcd.title("Seed Words")

        # format mnemonic and print
        words = self.mnemonic.split()
        labeled = [str(i) + ". " + word for i, word in enumerate(words, 1)]
        words_per_col = len(words) // 2
        left = labeled[:words_per_col]
        right = labeled[words_per_col:]

        lcd.body_columns(left, right)

class HomeScreen(Screen):

    def render(self):
        lcd.erase()
        lcd.title("Home")

class ConfirmOutputScreen(Screen):

    def __init__(self, tx, index, output_meta):
        self.tx = tx
        self.index = index
        self.output_meta = output_meta

    def a_release(self):
        print("don't sign")
        DONT_SIGN_IT.set()
        SigningCancelled().visit()

    def b_release(self):
        pass

    def c_release(self):
        # confirm remaining outputs
        if len(self.tx.tx_outs) > self.index + 1:
            ConfirmOutputScreen(self.tx, self.index + 1, self.output_meta).visit()
        # done confirming. sign it.
        else:
            SIGN_IT.set()
            SigningComplete().visit()

    def render(self):
        lcd.erase()

        lcd.title("Confirm Output")

        lcd.set_font(fonts.tt24)
        tx_out = self.tx.tx_outs[self.index]
        print('cmds', tx_out.script_pubkey.cmds)
        address = tx_out.script_pubkey.address(testnet=True)
        amount = tx_out.amount
        change_str = " (change)" if self.output_meta[self.index]['change'] else ''
        msg = "Are you sure you want to send {} satoshis to {}{}?".format(amount, address, change_str)
        lcd.body(msg)

        lcd.label_buttons("no", "", "yes")

class SigningComplete(Screen):

    def render(self):
        lcd.erase()
        lcd.alert("Transaction signed")
        time.sleep(3)
        HomeScreen().visit()

class SigningCancelled(Screen):

    def render(self):
        lcd.erase()
        lcd.alert("Aborted")
        time.sleep(3)
        HomeScreen().visit()

def seed_rng():
    from urandom import seed
    seed(999)

def load_key():
    global KEY
    with open('/sd/key.txt', 'rb') as f:
        KEY = HDPrivateKey.parse(f)

def save_key(mnemonic):
    '''saves key to disk, sets global KEY variable'''
    global KEY
    derivation_path = b'm'
    password = ''
    KEY = HDPrivateKey.from_mnemonic(mnemonic, password, path=derivation_path, testnet=True)
    with open('/sd/key.txt', 'wb') as f:
        f.write(KEY.serialize())

def main():
    # mount SD card to filesystem
    sd = SDCard()
    os.mount(sd, '/sd')

    # load key if it exists
    if 'key.txt' in os.listdir('/sd'):
        load_key()
        TraverseScreen().visit()
    # create and display mnemonic, derive and save key if it doesn't
    else:
        seed_rng()
        mnemonic = secure_mnemonic()
        MnemonicScreen(mnemonic).visit()


async def sign_tx(tx, input_meta, output_meta):
    assert len(tx.tx_outs) == len(output_meta)
    assert len(tx.tx_ins) == len(input_meta)

    ConfirmOutputScreen(tx, 0, output_meta).visit()

    while True:
        if SIGN_IT.is_set():
            SIGN_IT.clear()
            break
        if DONT_SIGN_IT.is_set():
            DONT_SIGN_IT.clear()
            return json.dumps({"error": "cancelled by user"})
        await uasyncio.sleep(1)

    for i, meta in enumerate(input_meta):
        script_hex = meta['script_pubkey']
        script_pubkey = Script.parse(BytesIO(unhexlify(script_hex)))
        receiving_path = meta['derivation_path'].encode()
        receiving_key = KEY.traverse(receiving_path).private_key
        tx.sign_input_p2pkh(i, receiving_key, script_pubkey)

    return json.dumps({"tx": hexlify(tx.serialize())})

async def serial_manager():
    sreader = uasyncio.StreamReader(stdin)
    swriter = uasyncio.StreamWriter(stdout, {})  # TODO: what is this second param?
    while True:
        msg_bytes = await sreader.readline()
        msg_str = msg_bytes.decode()
        try:
            msg = json.loads(msg_str)
        except Exception as e:
            print('bad msg')
            print(msg_str)
            print(e)
            continue

        if msg['command'] == 'xpub':
            derivation_path = msg['derivation_path'].encode()
            child = KEY.traverse(derivation_path)
            xpub = child.xpub()
            res = json.dumps({"xpub": xpub})
            await swriter.awrite(res+'\n')

        if msg['command'] == 'address':
            derivation_path = msg['derivation_path'].encode()
            child = KEY.traverse(derivation_path)
            address = child.address()
            res = json.dumps({"address": address})
            await swriter.awrite(res+'\n')

        if msg['command'] == 'sign':
            tx = Tx.parse(BytesIO(unhexlify(msg['tx'])), testnet=True)
            res = await sign_tx(tx, msg['input_meta'], msg['output_meta'])
            await swriter.awrite(res+'\n')

if __name__ == '__main__':
    main()
    loop = uasyncio.get_event_loop()
    ## FIXME: only run this in when a key is available for signing
    loop.create_task(serial_manager())
    loop.run_forever()

