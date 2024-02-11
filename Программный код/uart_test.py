import serial
from time import *


def uart_init():
    print("uart init..")
    return serial.Serial("COM3", 115200)


ser = uart_init()



def uart_print(msg):
    # msg += '\n'
    print(f'UART << {msg}')
    ser.write((msg + '\n').encode('utf-8'))


def uart_read():
    msg = ser.read().decode('utf-8')
    print(f"Received << {msg}")


def prints():
    uart_print('G28')
    sleep(5)
    uart_print('G1 Y5')
    sleep(2)
    uart_print('G1 Y45')
    sleep(2)
    uart_print('G1 Y85')
    sleep(2)
    #uart_print('G1 U180')
    #sleep(1)
    #uart_print('G1 V180')
    #sleep(1)
    #uart_print('G1 U0')
    #sleep(1)
    #uart_print('G1 V0')
    #sleep(1)


while True:
    prints()
    
    msg = ""
    ch = ser.read().decode('utf-8')
    while ch != "":
        msg += ch
        ch = ser.read().decode('utf-8')
    print(f"UART >> '{msg}'")    
    