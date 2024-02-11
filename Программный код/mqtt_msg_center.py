from paho.mqtt import client as mqtt_client

import random

import time


MQTT_HOST = '172.16.102.124'
MQTT_PORT = 1883
MQTT_CLIENT_ID = f'Auto_OrderPicker_1517-{random.randint(0,1000)}'
MQTT_USER = 'admin'
MQTT_PSWD = '12344321'

MQTT_PREFIX = 'Auto_OrderPicker_1517/'

MQTT_ORDER_TOPIC = MQTT_PREFIX + 'order'
MQTT_CMD_TOPIC = MQTT_PREFIX + 'cmd'

MQTT_LOG_TOPIC = MQTT_PREFIX + 'log'



def subscribe_and_handler(client, topic, msg_callback):
    client.subscribe(MQTT_PREFIX + topic)
    client.message_callback_add(topic, msg_callback)

def mqtt_publish_log(client: mqtt_client, msg):
    client.publish(MQTT_LOG_TOPIC, msg)


def mqtt_start(client: mqtt_client):
    client.loop_start()

def mqtt_stop(client: mqtt_client):
    client.loop_stop(force=False)

    
    
    
def mqtt_on_message(client, userdata, msg):
    print(f"Received '{str(msg.payload)}' from '{msg.topic}' topic")
    print("Unknown data")
   

def mqtt_enable_will(client):
    client.will_set(MQTT_LOG_TOPIC, "Device is offline..")


def mqtt_subcribe(client: mqtt_client):
    topics = [(MQTT_ORDER_TOPIC, 0),
              (MQTT_CMD_TOPIC, 0)]
    client.subscribe(topics)
    

def mqtt_on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"Connected to '{MQTT_HOST}' host")
        mqtt_publish_log(client, "Device is online")
        mqtt_subcribe(client)
        client.on_message = mqtt_on_message
        mqtt_enable_will(client)
    else:
        print(f'Failed to connect, return code {rc}')
        

def mqtt_connect() -> mqtt_client:
    client = mqtt_client.Client(MQTT_CLIENT_ID)
    client.username_pw_set(MQTT_USER, MQTT_PSWD)
    client.on_connect = mqtt_on_connect
    client.connect(MQTT_HOST, MQTT_PORT)
    #client.connect_async(MQTT_HOST, MQTT_PORT)
    return client





if __name__ == '__main__':
    client = mqtt_connect()
    #client.loop_forever()
    mqtt_start(client)
    time.sleep(60)
    mqtt_stop(client)