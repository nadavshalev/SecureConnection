from Connection.ConnSecure import ConnSecureClient
from Connection.ConnSocket import ConnSocketClient
import json
import threading


def receive_msg(sc):
    print('inside!!!!!')
    while True:
        data = sc.receive()
        if not data:
            exit(0)
        print(data)


f = open('./Connection/log_conn_client.txt', 'a')
conn_socket = ConnSocketClient('127.0.0.1', 65432, f)
conn_secure = ConnSecureClient(conn_socket, f)
conn_secure.connect()

threading.Thread(target=receive_msg, args=(conn_secure,)).start()

addr = input('Write Address: ')
while True:
    msg_str = input('Write Message Q[quit]: ')
    if msg_str == 'Q':
        conn_secure.disconnect()
        exit(0)

    msg = {
        "to": addr,
        "msg": msg_str
    }
    json_msg = json.dumps(msg)
    conn_secure.send(json_msg)