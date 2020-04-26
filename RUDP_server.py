#!/usr/bin/env python3

import socket
import json
import argparse
import pickle
from threading import Timer, Thread
import threading
import os
filename = "test.zip"
buffer_size = 1024


def makepkg(sequence_number, data):
    data_string = sequence_number.to_bytes(32, byteorder='big')+data
    # print(sequence_number, "of size", len(data_string))
    return data_string


def listener(sok, monitor):
    while(len(monitor)):
        message, clientAddress = sok.recvfrom(2048)
        sequence_num = int.from_bytes(message[0:32], byteorder='big')
        if sequence_num in monitor:
            monitor[sequence_num].cancel()
            monitor.pop(sequence_num, -1)
        print("got ack for", sequence_num)
    sok.close()


def send_packet(sok, sequence_number, data, clientAddress, monitor):
    if sequence_number in monitor:
        timer = Timer(0.5, send_packet, args=(sok, sequence_number,
                                              data, clientAddress, monitor))
        timer.start()  # after 30 seconds, "hello, world" will be printed
        monitor[sequence_number] = timer
        packet_string = makepkg(sequence_number, data)
        sok.sendto(packet_string, clientAddress)
        print('\t\t\t\tsent packet number', sequence_number)
    else:
        return


def server(host, port):
    sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientAddress = (host, port)
    sok.bind(clientAddress)

    while(True):
        message, clientAddress = sok.recvfrom(2048)
        if message.decode() == 'hello':
            break

    print('start received')
    b = os.path.getsize(filename)
    number_of_packets = int(b/buffer_size)
    if b % buffer_size == 0:
        number_of_packets -= 1
    monitor = {}
    for i in range(0, number_of_packets+1):
        monitor[i] = -1
    listener_thread = Thread(
        target=listener, args=(sok, monitor))
    listener_thread.start()

    # exit()
    f = open(filename, "rb")
    sequence_number = 0
    data = f.read(buffer_size)

    while (data):
        send_packet(sok, sequence_number, data, clientAddress, monitor)
        data = f.read(buffer_size)
        sequence_number += 1
    f.close()


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Send and receive UDP,'
    #                                  ' pretending packets are often dropped')
    # parser.add_argument('host', help='interface the server listens at;'
    #                     'host the client sends to')
    # parser.add_argument('-p', metavar='PORT', type=int, default=1060,
    #                     help='UDP port (default 1060)')
    # args = parser.parse_args()
    # server(args.host, args.p)
    server('127.0.0.1', 1060)
