import os
import threading
import time

from pynput.keyboard import Key

from Client import Client
from pynput import keyboard

def clear_screen():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')

def receive_msg(client):
    while client.connected:
        client.print_status()
        time.sleep(0.5)
        clear_screen()


def on_press(key):
    global key_buff
    if key == Key.enter:
        if key_buff == 'Q':
            client.disconnect()
            exit(0)
        if key_buff:
            client.send(key_buff, other_user)
            key_buff = ''
    else:
        try:
            key_buff += key.char
        except:
            key_buff = ''


username = input('username: ')

client = Client(username, '123123')

key_buff = ''

if not client.connect():
    print('failed to connect. exit')
    exit(1)

other_user = input('connect to: ')

print('======== start ==========')

threading.Thread(target=receive_msg, args=(client,)).start()
#
# with keyboard.Listener(
#         on_press=on_press) as listener:
#     listener.join()

while True:
    user_input = input('> ')
    # clear_screen()
    if user_input == 'Q':
        client.disconnect()
        exit(0)
    else:
        client.send(user_input, other_user)