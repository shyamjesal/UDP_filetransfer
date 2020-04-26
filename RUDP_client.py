#!/usr/bin/env python3

import socket
import json
import argparse
import pickle
from threading import Timer, Thread
filename = "receivedfile.zip"
buffer_size = 1056


def unpkg(data_string):
    # data_loaded = json.loads(data)
    data_loaded = data_string[32:]
    sequence_num = int.from_bytes(data_string[0:32], byteorder='big')
    # print("got packet", sequence_num, "of size", len(data_string))
    return data_loaded, sequence_num


def send_ak(sok, number):
    # t = Timer(2.0, send_ak, sok, number)
    # t.start()  # after 30 seconds, "hello, world" will be printed
    message = number.to_bytes(32, byteorder='big')
    sok.send(message)
    # print('sending ack for', number)


def write_file(sok, monitor):
    written = 0
    f = open(filename, 'wb')
    while(True):
        if written in monitor:
            f.write(monitor[written])
            print(written, "written")
            monitor.pop(written, -1)
            if written == 1483:
                break
            written += 1
    print("file written")
    f.close()
    exit()


def initiate_handshake(sok):
    # timer = Timer(0.5, initiate_handshake, args=(sok,))
    # timer.start()  # after 30 seconds, "hello, world" will be printed
    message = 'start'
    sok.send(message.encode())


def client(host, port):
    # fileno() method to peek at it
    sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sok.connect((host, port))

    # print(sok.fileno())
    initiate_handshake(sok)
    monitor = {}
    file_thread = Thread(
        target=write_file, args=(sok, monitor))
    file_thread.start()
    data, addr = sok.recvfrom(buffer_size)
    try:
        while(data):
            file_bytes, number = unpkg(data)
            monitor[number] = file_bytes
            data, addr = sok.recvfrom(buffer_size)
            send_ak(sok, number)
    except socket.timeout as e:
        print(e)
        print("Timeout")
    except OSError as e:
        # print(e)
        print("transfer complete")
    # modifiedMessage, serverAddress = sok.recvfrom(2048)
    # print(modifiedMessage.decode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and receive UDP,'
                                     ' pretending packets are often dropped')
    parser.add_argument('host', help='interface the server listens at;'
                        'host the client sends to')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060,
                        help='UDP port (default 1060)')
    # args = parser.parse_args()
    client('127.0.0.1', 1060)
