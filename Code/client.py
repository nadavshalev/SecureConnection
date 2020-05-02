import os
import time

from Client import Client


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


username = input('username: ')

client = Client(username, '123123')

if not client.connect():
    print('failed to connect. exit')
    exit(1)

other_user = input('connect to: ')

print('======== start ==========')
while True:
    msg = input('')
    if msg == 'Q':
        client.disconnect()
        exit(0)
    try:
        client.send(msg, other_user)
        client.print_status()
    except Exception as e:
        print(repr(e))
        exit(0)
