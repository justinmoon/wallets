import os
import json
import uasyncio
from asyn import Event
from binascii import unhexlify, hexlify
from io import BytesIO
from m5stack import LCD, fonts, color565, SDCard
from m5stack.pins import BUTTON_A_PIN, BUTTON_B_PIN, BUTTON_C_PIN
from bitcoin.mnemonic import secure_mnemonic
from bitcoin.hd import HDPrivateKey
from bitcoin.tx import Tx
from bitcoin.script import Script
from aswitch import Pushbutton
from machine import Pin
from sys import stdin, stdout

# FIXME: move to library
A_PIN = Pin(BUTTON_A_PIN, Pin.IN, Pin.PULL_UP)
B_PIN = Pin(BUTTON_B_PIN, Pin.IN, Pin.PULL_UP)
C_PIN = Pin(BUTTON_C_PIN, Pin.IN, Pin.PULL_UP)
A_BUTTON = Pushbutton(A_PIN)
B_BUTTON = Pushbutton(B_PIN)
C_BUTTON = Pushbutton(C_PIN)

lcd = LCD()
lcd.set_font(fonts.tt24)
lcd.erase()

# synchronization primitives
SIGN_IT = Event()
DONT_SIGN_IT = Event()


# TODO: I need a router class that keeps track of history, can go "back"
class Screen:

    def visit(self):
        A_BUTTON.release_func(self.a_release)
        B_BUTTON.release_func(self.b_release)
        C_BUTTON.release_func(self.c_release)
        self.render()

class TraverseScreen(Screen):

    def __init__(self, master_key, address_index=0, address_type='legacy'):
        self.master_key = master_key
        self.address_index = address_index
        self.address_type = address_type

    def a_release(self):
        '''decrement address index'''
        if self.address_index != 0:
            new_screen = TraverseScreen(self.master_key, self.address_index - 1, self.address_type)
            route(new_screen)

    def b_release(self):
        '''flip address type'''
        address_type = 'bech32' if self.address_type == 'legacy' else 'legacy'
        new_screen = TraverseScreen(self.master_key, self.address_index, address_type)
        route(new_screen)

    def c_release(self):
        '''increment address index'''
        new_screen = TraverseScreen(self.master_key, self.address_index + 1, self.address_type)
        route(new_screen)
    
    def render(self):
        # FIXME: change
        path = "m/84'/1'/0'/{}".format(self.address_index).encode()
        key = self.master_key.traverse(path)
        address = key.address() if self.address_type == 'legacy' else key.bech32_address()
        lcd.erase()
        lcd.set_pos(20, 20)
        lcd.print(path.decode())
        lcd.print(address)

class MnemonicScreen(Screen):

    def __init__(self, mnemonic):
        self.mnemonic = mnemonic

    def on_verify(self):
        '''display addresses once they've confirmed mnemonic'''
        # FIXME: slow, display loading screen
        key = save_key(self.mnemonic)
        TraverseScreen(key).visit()

    def a_release(self):
        self.on_verify()

    def b_release(self):
        self.on_verify()

    def c_release(self):
        print('verify')
        self.on_verify()
    
    def render(self):
        title("Seed Words")

        # set font
        lcd.set_font(fonts.tt24)

        # variables for printing
        words = self.mnemonic.split()
        labeled = [str(i) + ". " + word for i, word in enumerate(words, 1)]
        words_per_col = len(words) // 2
        col_width = max([lcd._font.get_width(w) for w in labeled])
        # 2 colunms with equal spacing on all sides
        pad_x = (lcd.width - 2 * col_width) // 3
        pad_y = 20
        left_col_x, left_col_y = pad_x, lcd._y + pad_y
        right_col_x, right_col_y = 2 * pad_x + col_width, lcd._y + pad_y

        # print left column
        lcd.set_pos(left_col_x, left_col_y)
        for word in labeled[:words_per_col]:
            lcd.print(word)

        # print right column
        lcd.set_pos(right_col_x, right_col_y)
        for word in labeled[words_per_col:]:
            lcd.print(word)


def seed_rng():
    from urandom import seed
    seed(999)

def title(s):
    # calculations
    sw = fonts.tt32.get_width(s)
    padding = (lcd.width - sw) // 2

    # configure lcd
    lcd.set_font(fonts.tt32)
    lcd.set_pos(padding, 20)

    # print
    lcd.print(s)

def load_key():
    with open('/sd/key.txt', 'rb') as f:
        return HDPrivateKey.parse(f)

def save_key(mnemonic):
    derivation_path = b'm'
    password = ''
    key = HDPrivateKey.from_mnemonic(mnemonic, password, path=derivation_path, testnet=True)
    with open('/sd/key.txt', 'wb') as f:
        f.write(key.serialize())
    return key

def main():
    # mount SD card to filesystem
    sd = SDCard()
    os.mount(sd, '/sd')

    # load key if it exists
    if 'key.txt' in os.listdir('/sd'):
        key = load_key()
        TraverseScreen(key).visit()
    # create and display mnemonic, derive and save key if it doesn't
    else:
        seed_rng()
        mnemonic = secure_mnemonic()
        MnemonicScreen(mnemonic).visit()

class ConfirmOutputScreen(Screen):

    def __init__(self, tx, index):
        self.tx = tx
        self.index = index

    def a_release(self):
        DONT_SIGN_IT.set()

    def b_release(self):
        pass

    def c_release(self):
        if len(self.tx.tx_outs) > self.index + 1:
            ConfirmOutputScreen(self.tx, self.index + 1).visit()
        else:
            SIGN_IT.set()

    def render(self):
        lcd.erase()

        title("Confirm Output")

        lcd.set_font(fonts.tt24)
        tx_out = self.tx.tx_outs[self.index]
        print('cmds', tx_out.script_pubkey.cmds)
        address = tx_out.script_pubkey.address(testnet=True)
        amount = tx_out.amount
        msg = "Are you sure you want to send {} satoshis to {}?".format(amount, address)
        lcd.print(msg)

async def sign_tx(tx, input_meta, output_meta):
    print(input_meta)
    assert len(tx.tx_outs) == len(output_meta)
    assert len(tx.tx_ins) == len(input_meta)

    ConfirmOutputScreen(tx, 0).visit()

    while True:
        if SIGN_IT.is_set():
            lcd.print("SIGN IT")
            SIGN_IT.clear()
            break
        if DONT_SIGN_IT.is_set():
            lcd.print("DON'T SIGN IT")
            DONT_SIGN_IT.clear()
            break
        print('waiting')
        await uasyncio.sleep(1)

    master_key = load_key()
    for i, meta in enumerate(input_meta):
        script_hex = meta['script_pubkey']
        script_pubkey = Script.parse(BytesIO(unhexlify(script_hex)))
        receiving_path = meta['derivation_path'].encode()
        print(receiving_path)
        receiving_key = master_key.traverse(receiving_path).private_key
        tx.sign_input_p2pkh(i, receiving_key, script_pubkey)

    res = json.dumps({
        "tx": hexlify(tx.serialize()),
    })
    return res

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

        # lcd.print(msg_str)

        if msg['command'] == 'xpub':
            master_key = load_key()
            derivation_path = msg['derivation_path'].encode()
            print(derivation_path)
            key = master_key.traverse(derivation_path)
            xpub = key.xpub()
            res = json.dumps({"xpub": xpub})
            await swriter.awrite(res+'\n')

        if msg['command'] == 'address':
            master_key = load_key()
            derivation_path = msg['derivation_path'].encode()
            key = master_key.traverse(derivation_path)
            address = key.address()
            res = json.dumps({"address": address})
            await swriter.awrite(res+'\n')

        if msg['command'] == 'sign':
            tx = Tx.parse(BytesIO(unhexlify(msg['tx'])), testnet=True)
            res = await sign_tx(tx, msg['input_meta'], msg['output_meta'])
            await swriter.awrite(res+'\n')

if __name__ == '__main__':
    main()
    loop = uasyncio.get_event_loop()
    # FIXME: only run this in when a key is available for signing
    loop.create_task(serial_manager())
    loop.run_forever()

