import os
import uasyncio
from m5stack import LCD, fonts, color565, SDCard
from m5stack.pins import BUTTON_A_PIN, BUTTON_B_PIN, BUTTON_C_PIN
from bitcoin.mnemonic import secure_mnemonic
from bitcoin.hd import HDPrivateKey
from aswitch import Pushbutton
from machine import Pin

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
    seed(888)

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

if __name__ == '__main__':
    main()
    loop = uasyncio.get_event_loop()
    loop.run_forever()
