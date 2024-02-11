from cam_capture import capture
from qr_scanner import scan_qrcode

import time



def Dprint(msg):
    print(msg)


######################################################################
########################### Serial UART ##############################
######################################################################

import serial

ser = ""

PORT = "COM1"
UART_SPEED = 115200


def uart_init():
    Dprint("uart init..")
    serials = serial.Serial(PORT, UART_SPEED)
    return serials
    
def uart_print(msg):
    msg += '\n'
    Dprint(f'UART << {msg}')
    ser.write(msg.encode('utf-8'))


######################################################################
############# COMMANDS and get CMD AND ORDER from MQTT ###############
######################################################################

from mqtt_msg_center import (mqtt_connect,
                            subscribe_and_handler,
                            mqtt_publish_log,
                            mqtt_start,
                            mqtt_stop)

import mqtt_settings


client = ''

NO_CMD = 0
START_CMD = 1
BREAK_CMD = 2
PAUSE_CMD = 3
CH_ORDER_CMD = 4
SAVE_ORDER_CMD = 5

CMD = None

def reset_CMD():
    global CMD
    CMD = NO_CMD

reset_CMD()


commands = [
    {"cmd": NO_CMD,         "text": "no_cmd"},
    {"cmd": START_CMD,      "text": "start_cmd"},
    {"cmd": BREAK_CMD,      "text": "break_cmd"},
    {"cmd": PAUSE_CMD,      "text": "pause_cmd"},
    {"cmd": CH_ORDER_CMD,   "text": "ch_order_cmd"},
    {"cmd": SAVE_ORDER_CMD, "text": "save_order_cmd"}
]

NO_ORDER_MSG = ""
order_msg = NO_ORDER_MSG


MQTT_ORDER_TOPIC = mqtt_settings.MQTT_PREFIX + 'order'
MQTT_CMD_TOPIC = mqtt_settings.MQTT_PREFIX + 'cmd'


def mqtt_print(msg):
    mqtt_publish_log(client, msg)

def mqtton_CMDMSG(client, userdata, msg):
    global CMD
    CMDtext = msg.payload.decode('utf-8')
    print(f"Command '{CMDtext}' from '{msg.topic}'")
    CMD = NO_CMD
    for command in commands:
        if CMDtext == command["text"]:
            CMD = command["cmd"]
            break
    
     
def mqtton_orderMSG(client, userdata, msg):
    global order_msg
    order_msg = msg.payload.decode('utf-8')
    print(f"Order '{order_msg}' from '{msg.topic}'")


def mqtt_init():   
    print("mqtt init..")
    client = mqtt_connect()
    subscribe_and_handler(client, MQTT_ORDER_TOPIC, mqtton_orderMSG)
    subscribe_and_handler(client, MQTT_CMD_TOPIC, mqtton_CMDMSG)
    mqtt_start(client)
    return client
    
    
######################################################################
######################################################################


def log(msg):
    print(msg)
    mqtt_print(msg)




storage_cells_num = 9

storage_first_cell_pos_mm = 5
storage_cell_size_mm = 45

#//U - захват, V - Выдвижение
grip_opened_u_pos = 180
grip_closed_u_pos = 0
grip_opened_v_pos = 180
grip_closed_v_pos = 0


current_cell = 0


def D_home():
    global current_cell
    log("go home...")
    msg = f'G1 U{grip_opened_u_pos} V{grip_opened_v_pos}'
    uart_print(msg)
    uart_print('G28')
    time.sleep(2)  #### Change to receive 'done' cmd from Serial ESP32
    current_cell = 0
    

def D_pause():
    log("Pause order collecting!")
    uart_print('M18') #Motors off



def convert_cell(num):
    if num == 0:
        pos = 0
    elif num >= 1:
        pos = (storage_first_cell_pos_mm +
            (num - 1) * storage_cell_size_mm)
    return pos


def device_next_cell():
    global current_cell
    current_cell += 1
    log("Go to next cell")
    pos = convert_cell(current_cell)
    uart_print(f'G1 Y{pos}')
    time.sleep(11.5)  #### Change to receive 'done' cmd from Serial ESP32

def device_take_object():
    log("Grab the object")
    uart_print(f'G1 U{grip_opened_u_pos}')
    time.sleep(1)  #### Change to receive 'done' cmd from Serial ESP32
    uart_print(f'G1 V{grip_opened_v_pos}')
    time.sleep(1)  #### Change to receive 'done' cmd from Serial ESP32
    uart_print(f'G1 U{grip_closed_u_pos}')
    time.sleep(1)

def device_down_object():
    log("Pull the object")
    uart_print(f'G1 V{grip_closed_u_pos}')
    time.sleep(1)  #### Change to receive 'done' cmd from Serial ESP32

def device_release_object():
    log("Release the object")
    uart_print(f'G1 U{grip_opened_u_pos}')
    time.sleep(1)  #### Change to receive 'done' cmd from Serial ESP32

def device_stop():
    pass



warehouse = ["гайки",
             "винты",
             "шайбы",
             "шпильки",
             "подшипники",
             "линейные направляющие",
             "валы",
             "двигатели",
             "датчики"
]

order = []
collected = []
def reset_collected_order():
    global collected
    collected = []
def reset_order():
    global order
    order = []


def orderlist_str(items):
    msg = ', '.join(str(item) for item in items)
    return msg
    

def decode_order():
    global order_msg
    if order_msg != NO_ORDER_MSG:
        log("New order was received!")
        reset_order()
        msg = list(set(order_msg.split(", ")))
        correct_fl = True
        for word in msg:
            if word in collected:
                log(f"Warning! Item '{word}' is already picked up!")
            elif word in warehouse:
                order.append(word)
                log(f"Item '{word}' was added to order list")
            else:
                log(f"Error! Incorrect item '{word}'")
                correct_fl = False
        
        if (not correct_fl):
            log("Warning! One or more order positions were incorrect!")
        
        msg = 'Текущий заказ: ' + orderlist_str(order)
        order_msg = NO_ORDER_MSG
        log(msg)



def start_handler():
    Dprint(">> Starting handler")
    global state
    if (len(order) == 0):
        if (len(collected) > 0):
            log("Order is already picked up!")
            state = FINISH_ST
        else:
            log("Warning! Order is empty!")
            state = WAITING_ST
    else:
        log("Starting order collecting..")
        state = SCANNING_ST

def initial_handler():
    Dprint(">> Initializing handler")
    global client
    global ser
    global state
    client = mqtt_init()
    ser = uart_init()
    D_home()
    log("Waiting for commands")
    state = WAITING_ST


def wait_handler():
    Dprint(">> Waiting handler")
    Dprint(f">> Command is '{CMD}'")
    global state
    if CMD == CH_ORDER_CMD:
        log("Changing order..")
        state = SETTING_ORDER_ST
    elif CMD == START_CMD:
        state = STARTING_ST
    elif CMD == NO_CMD:
        pass
    else:
        log(f'Error! Wrong command - {CMD}')
    reset_CMD()

def set_order_handler():
    Dprint(">> Setting order handler")
    global state
    decode_order()
    Dprint(">> decoded order: ")
    Dprint(order)
    Dprint(f">> Command is '{CMD}'")
    if CMD == SAVE_ORDER_CMD:
        log("Saving the order")
        state = STARTING_ST #WAITING_ST
    reset_CMD()




MOVE = 0
SCAN = 1
GRAB = 2
THROW = 3
scanning_stage = MOVE

item = ""


def reset_scanStage():
    global item
    global current_cell
    global scanning_stage
    item = None
    current_cell = 0
    scanning_stage = MOVE

def reset_scanData():
    reset_scanStage()
    reset_order()
    reset_collected_order()

def end_scan():
    if (len(collected) > 0):
        log('Collected: ' + orderlist_str(collected))
    if (len(order) > 0):
        log('Not collected: ' + orderlist_str(order))
    
    reset_scanData()
    D_home()
    log("Waiting for commands")


def finish_handler():
    Dprint(">> Finish handler")
    log("Order completed!")
    global state
    ### Display finish screen
    end_scan()
    state = WAITING_ST

def pause_handler():
    Dprint(">> Pause handler")
    global state
    if CMD == CH_ORDER_CMD:
        state = CH_ORDER_ST
    elif CMD == START_CMD:
        state = STARTING_ST
    elif CMD == BREAK_CMD:
        state = BREAK_ST
    reset_CMD()


def break_handler():
    Dprint(">> Break handler")
    log("Break order collecting!")
    global state
    device_stop()
    end_scan()
    state = WAITING_ST

    
def change_order_handler():
    Dprint(">> Changing order handler")
    global state
    decode_order()
    Dprint(">> decoded order: ")
    Dprint(order)
    Dprint(f">> Command is '{CMD}'")
    if CMD == SAVE_ORDER_CMD:
        state = PAUSE_ST
    reset_CMD()
    


def scan_handler():
    global state
    global item
    global current_cell
    global scanning_stage
    Dprint(">> Scanning handler")
    Dprint(f">> Command is '{CMD}'")
    if CMD == PAUSE_CMD:
        if scanning_stage == GRAB:
            scanning_stage = SCAN
        D_pause()
        state = PAUSE_ST
        return
    elif CMD == BREAK_CMD:
        state = BREAK_ST
        return
    reset_CMD()

    if scanning_stage == MOVE:
        if (current_cell == storage_cells_num):
            log("The last cell was reached! Scan again from the first cell!")
            current_cell = 0
        Dprint('Going to the next cell..')
        device_next_cell()
        Dprint(f'Current cell is #{current_cell}')
        scanning_stage = SCAN

    elif scanning_stage == SCAN:
        Dprint('Capture img and scan for QR')
        filename = f'cell-{current_cell}.png'
        Dprint(filename)

        capture(filename)
        data = scan_qrcode(filename)
        if (not data):
            log(f'Cant found QR code. Try again..')
        else:
            Dprint("Successfully found and read QR code!")
            log(f"Found '{data}' item")
            if (data in order):
                log(f"'{data}' is in order! Collecting..")
                item = data
                scanning_stage = GRAB
            else:
                log(f"'{data}' is not in order! Continue scanning!")
                scanning_stage = MOVE

    elif scanning_stage == GRAB:
        device_take_object()
        device_down_object()
        device_release_object()
        log(f'{item} was collected!')

        index = order.index(item)
        collected.append(order.pop(index))

        Dprint("order:")
        Dprint(order)
        Dprint("collected:")
        Dprint(collected)

        item = None
        scanning_stage = MOVE
        if (len(order) == 0):
            log("Order is picked up!")
            state = FINISH_ST
    else:
        Dprint("Error! Wrong scanning stage!")



INITIALIZING_ST     = 0
WAITING_ST          = 1
SETTING_ORDER_ST    = 2
STARTING_ST         = 3
SCANNING_ST         = 4
FINISH_ST           = 5
PAUSE_ST            = 6
CH_ORDER_ST         = 7
BREAK_ST            = 8

state = INITIALIZING_ST

state_handlers = [
        {"state": INITIALIZING_ST,  "func": initial_handler},
        {"state": WAITING_ST,       "func": wait_handler},
        {"state": SETTING_ORDER_ST, "func": set_order_handler},
        {"state": STARTING_ST,      "func": start_handler},
        {"state": SCANNING_ST,      "func": scan_handler},
        {"state": FINISH_ST,        "func": finish_handler},
        {"state": PAUSE_ST,         "func": pause_handler},
        {"state": CH_ORDER_ST,      "func": change_order_handler},
        {"state": BREAK_ST,         "func": break_handler}
]

while True:
    for handler in state_handlers:
        if handler["state"] == state:
            handler["func"]()
            break
    time.sleep(1)
