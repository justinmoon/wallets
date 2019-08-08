import sys
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
    return ser.read_until(b'\n').strip(b'\n').decode()

def main():
    msg = ' '.join(sys.argv[1:])
    print(send_and_recv(msg))

if __name__ == '__main__':
    main()
