import os

from m5stack import LCD, fonts

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

file_name = 'counter.txt'

def load():
    with open(file_name, 'r') as f:
        return int(f.read())

def save(counter):
    with open(file_name, 'w') as f:
        f.write(str(counter))

def main():
    # load and increment counter if counter file exists
    if file_name in os.listdir():
        counter = load()
        counter += 1
    # initialize if it doesn't
    else:
        counter = 0
    # save counter to sd card and print it's value
    save(counter)
    lcd.print("Counter: {}".format(counter))

if __name__ == '__main__':
    main()

