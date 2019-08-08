import uasyncio
from m5stack import LCD, fonts
from sys import stdin, stdout

lcd = LCD()
lcd.set_font(fonts.tt32)
lcd.erase()

async def serial_manager():
    sreader = uasyncio.StreamReader(stdin)
    swriter = uasyncio.StreamWriter(stdout, {})  # TODO: what is this second param?
    while True:
        msg = await sreader.readline()
        msg = msg.decode()
        lcd.print(msg.strip('\n'))
        res = 'Serial: ' + msg
        await swriter.awrite(res)

def main():
    loop = uasyncio.get_event_loop()
    loop.create_task(serial_manager())
    loop.run_forever()

if __name__ == '__main__':
    main()
