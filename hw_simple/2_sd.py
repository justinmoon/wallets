import os
from m5stack import LCD, fonts, color565, SDCard
from bitcoin.mnemonic import secure_mnemonic
from bitcoin.hd import HDPrivateKey


lcd = LCD()
lcd.set_font(fonts.tt24)
lcd.erase()

def print_address(master):
    path = b"m/84'/1'/0'/0"
    key = master.traverse(path)
    address = key.address()
    lcd.erase()
    lcd.set_pos(20, 20)
    lcd.print(path.decode())
    lcd.print(address)

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

def display_mnemonic(mnemonic):
    # print title
    title("Seed Words")

    # set font
    lcd.set_font(fonts.tt24)

    # variables for printing
    words = mnemonic.split()
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

    return mnemonic

def load_key():
    with open('/sd/key.txt', 'rb') as f:
        return HDPrivateKey.parse(f)

def save_key(mnemonic):
    derivation_path = b'm'
    password = ''
    key = HDPrivateKey.from_mnemonic(mnemonic, password, path=derivation_path, testnet=True)
    with open('/sd/key.txt', 'wb') as f:
        f.write(key.serialize())

def main():
    # mount SD card to filesystem
    sd = SDCard()
    os.mount(sd, '/sd')

    # load key if it exists
    if 'key.txt' in os.listdir('/sd'):
        key = load_key()
        print_address(key)
    # create and display mnemonic, derive and save key if it doesn't
    else:
        seed_rng()
        mnemonic = secure_mnemonic()
        display_mnemonic(mnemonic)
        save_key(mnemonic)

if __name__ == '__main__':
    main()
