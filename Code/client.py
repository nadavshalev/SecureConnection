from Client.Client import Client
import threading


def receive_msg(conn, message):
    print(f'{conn.target_address}: {message}')


my_addr = input('my address: ')
other_addr = input('connect to: ')

client = Client(my_addr, '123123')

if other_addr:
    if not client.connect(other_addr):
        print('failed to connect. exit')
        exit(1)
else:
    if not client.accept():
        print('failed to connect. exit')
        exit(1)

client.receive_callback(receive_msg)


print('======== start ==========')
while True:
    msg = input('')
    if msg == 'Q':
        client.disconnect()
        exit(0)
    try:
        client.send(msg)
    except Exception as e:
        print(repr(e))
        exit(0)
