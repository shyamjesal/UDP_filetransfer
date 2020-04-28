#!/usr/bin/env python3

import socket
import argparse
from threading import Timer, Thread
import threading
import os
import time
import xxhash
filename = "assignment-3.pdf"
file_buffer_size = 1428

''' First bit indicates the message type    0->handshake
                                            1->data
    second bit indicates last packet        0->not last
                                            1->last
    Next 4 bytes are the xxhash value 
'''


def makepkg(sequence_number, data, last_packet_num):
    sequence_number_bytes = sequence_number.to_bytes(4, byteorder='big')
    # make the first bit 1 as this is data packet
    first_byte = (int('80', 16) | sequence_number_bytes[0]).to_bytes(
        1, byteorder='big')
    sequence_number_bytes = first_byte+sequence_number_bytes[1:4]
    # make the second bit 1 if the packet is the last one
    if sequence_number == last_packet_num:
        first_byte = (int('c0', 16) | sequence_number_bytes[0]).to_bytes(
            1, byteorder='big')
        sequence_number_bytes = first_byte+sequence_number_bytes[1:4]
    data_hash = xxhash.xxh32(data).digest()
    data_string = sequence_number_bytes + data_hash + data
    # print(sequence_number, "of size", len(data_string))
    return data_string


def listener(sok, monitor):
    timeout_interval = 0.5
    while(len(monitor)):
        try:
            sok.settimeout(timeout_interval)
            message, clientAddress = sok.recvfrom(2048)
            sequence_num = int.from_bytes(message[0:4], byteorder='big')
            if sequence_num in monitor:
                monitor[sequence_num].cancel()
                monitor.pop(sequence_num, -1)
            # print("got ack for", sequence_num)
        except socket.timeout:
            print('will try after {} seconds'.format(timeout_interval))
            timeout_interval *= 2
        except ConnectionRefusedError:
            print('It seems the server is not online, sleeping for {} seconds'.format(
                timeout_interval))
            time.sleep(timeout_interval)
            timeout_interval *= 2
        finally:
            if timeout_interval > 10:
                print('no response since 10 seconds. exiting')
                monitor['disconnected'] = True
                exit()
    sok.close()


def send_packet(sok, sequence_number, data, clientAddress, monitor, last_packet_num):
    if monitor.get('disconnected', False):
        return
    elif sequence_number in monitor:
        timer = Timer(0.5, send_packet, args=(sok, sequence_number,
                                              data, clientAddress, monitor, last_packet_num))
        timer.start()  # after 30 seconds, "hello, world" will be printed
        monitor[sequence_number] = timer
        packet_string = makepkg(sequence_number, data, last_packet_num)
        sok.sendto(packet_string, clientAddress)
        # print('\t\t\t\tsent packet number', sequence_number)
    else:
        return


def server(host, port):
    sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientAddress = (host, port)
    sok.bind(clientAddress)

    while(True):
        message, clientAddress = sok.recvfrom(2048)
        if message.decode() == 'start':
            break

    print('start received')
    b = os.path.getsize(filename)
    last_packet_num = int(b/file_buffer_size)
    if b % file_buffer_size == 0:
        last_packet_num -= 1
    print(last_packet_num)
    monitor = {}
    for i in range(0, last_packet_num+1):
        monitor[i] = -1
    listener_thread = Thread(
        target=listener, args=(sok, monitor))
    listener_thread.start()

    f = open(filename, "rb")
    sequence_number = 0
    data = f.read(file_buffer_size)

    while (data):
        if monitor.get('disconnected', False):
            break
        send_packet(sok, sequence_number, data,
                    clientAddress, monitor, last_packet_num)
        data = f.read(file_buffer_size)
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
