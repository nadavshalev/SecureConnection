from Connection import ConnSecureClient, ConnSocketClient, ConnP2PClient
import threading

from Connection.ConnSecure import ConnSecureClientAccept


def receive_msg(client_secure):
    while True:
        try:
            msg = client_secure.receive()
            if not msg:
                print(f'exit receive thread')
                exit(0)
            print(f'{client_secure.get_addr()}: {msg}')
        except Exception as e:
            print(repr(e))
            exit(0)


my_addr = input('my address: ')

other_addr = input('connect to: ')

f = open('./log_client.txt', 'a')
conn_socket = ConnSocketClient('54.157.229.65', 65432, f)
conn_secure = ConnSecureClient(conn_socket, f)
conn_p2p = ConnP2PClient(conn_secure, my_addr, f, other_addr)

if other_addr:
    client_secure = ConnSecureClient(conn_p2p, f)
else:
    client_secure = ConnSecureClientAccept(conn_p2p, f)
if not client_secure.connect():
    print('cant connect. exit')
    exit()

threading.Thread(target=receive_msg, args=(client_secure,)).start()

print('======== start ==========')
while True:
    msg = input('')
    if msg == 'Q':
        client_secure.disconnect()
        exit(0)
    try:
        client_secure.send(msg)
    except Exception as e:
        print(repr(e))
        exit(0)