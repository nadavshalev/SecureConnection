from Connection.ConnSecure import ConnSecureClient
from Connection.ConnSocket import ConnSocketClient
from Connection.ConnP2P import ConnP2PClient
import json
import threading


def receive_msg(conn_p2p):
    while True:
        try:
            msg = conn_p2p.receive()
        except Exception as e:
            # print(repr(e))
            exit(0)
        if not msg:
            exit(0)
        print(f'{conn_p2p.conn_addr}: {msg}')


f = open('./Connection/log_conn_client.txt', 'a')
conn_socket = ConnSocketClient('127.0.0.1', 65432, f)
conn_secure = ConnSecureClient(conn_socket, f)

my_addr = input('my address: ')

conn_p2p = ConnP2PClient(conn_secure, my_addr, f)

other_addr = input('connect to: ')
if other_addr:
    success = conn_p2p.connect(other_addr)
else:
    success = conn_p2p.connect()

if not success:
    print('cant connect. exit')
    exit()

threading.Thread(target=receive_msg, args=(conn_p2p,)).start()

print('======== start ==========')
while True:
    msg = input('')
    if msg == 'Q':
        conn_p2p.disconnect()
        exit(0)
    try:
        conn_p2p.send(msg)
    except Exception as e:
        # print(repr(e))
        exit(0)