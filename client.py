from Connection.ConnSecure import ConnSecureClient
from Connection.ConnSocket import ConnSocketClient

f = open('./Connection/log_conn_client.txt', 'a')
conn_socket = ConnSocketClient('127.0.0.1', 65432, f)
conn_secure = ConnSecureClient(conn_socket, f)
conn_secure.connect()
while True:
    msg = input('Write Message Q[quit]: ')
    if msg == 'Q':
        conn_secure.disconnect()
        break
    conn_secure.send(msg)
    print(conn_secure.receive())