#!/usr/bin/env python3
import socket
import argparse
from threading import Timer, Thread
from timeit import default_timer as current_time
import threading
import os
import time
# os.system('pip install xxhash')
import xxhash
from tkinter import filedialog
from tkinter import *

filename = "/run/media/s_jesal/48fb6712-a555-4e8c-a7db-d95cb326910a/MEGAsync/4-2/networks/PacketTracer711_64bit_linux.tar"
# filename = "assignment-3.pdf"
file_buffer_size = 65400

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
    # data_string = sequence_number_bytes + data
    # print(sequence_number, "of size", len(data_string))
    return data_string


def listener(sok, monitor, rate_queue, timeout_params):
    timeout_interval = 0.5
    while(len(monitor)):
        try:
            sok.settimeout(timeout_interval)
            message, clientAddress = sok.recvfrom(2048)
            # sequence_num = int.from_bytes(message[0:4], byteorder='big')
            first_byte = message[0]
            if first_byte >> 7 & 1 == 0:
                continue
            else:
                sequence_num = (first_byte & int('7f', 16)).to_bytes(
                    1, byteorder='big') + message[1:4]
                sequence_num = int.from_bytes(
                    sequence_num[0:4], byteorder='big')
            if sequence_num in monitor:

                # finding RTT
                sampleRTT = current_time() - monitor[sequence_num]
                if timeout_params.get('estRTT', -1) == -1:
                    timeout_params['devRTT'] = 0
                    timeout_params['estRTT'] = sampleRTT
                else:
                    timeout_params['estRTT'] = 0.125 * \
                        (sampleRTT) + 0.875*timeout_params['estRTT']
                    timeout_params['devRTT'] = 0.75 * \
                        timeout_params['devRTT'] + \
                        abs(timeout_params['estRTT']-sampleRTT)
                    timeout_params['interval'] = timeout_params['estRTT'] + \
                        4*timeout_params['devRTT']

                monitor.pop(sequence_num, -1)

                # rate_queue.pop(sequence_num, -1)
            # if rate_queue.get(sequence_num, -1) != -1:
            #     print("got ack for", sequence_num, "qlen", len(rate_queue),
            #           "RTT", current_time() - rate_queue[sequence_num])
            # else:
            print("got ack for", sequence_num)
        except socket.timeout:
            print('will try after {} seconds'.format(timeout_interval))
            timeout_interval *= 1.5
        except ConnectionRefusedError:
            print('It seems the server is not online, sleeping for {} seconds'.format(
                timeout_interval))
            time.sleep(timeout_interval)
            timeout_interval *= 1.5
        finally:
            if timeout_interval > 10:
                print('no response since 10 seconds. exiting')
                monitor['disconnected'] = True
                exit()
    sok.close()


def send_packet(sok, sequence_number, data, clientAddress, monitor, last_packet_num, rate_queue):
    if monitor.get('disconnected', False):
        return
    elif sequence_number in monitor:
        # timer = Timer(0.1, send_packet, args=(sok, sequence_number,
        #                                       data, clientAddress, monitor, last_packet_num, rate_queue))
        # timer.start()  # after 30 seconds, "hello, world" will be printed
        monitor[sequence_number] = current_time()
        packet_string = makepkg(sequence_number, data, last_packet_num)
        sok.sendto(packet_string, clientAddress)
        # rate_queue[sequence_number] = True
        # print('\t\t\t\tsent packet number', sequence_number)
    else:
        return


def Server(host, port, filename):
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
    rate_queue = {}
    timeout_params = {'estRTT': 0, 'interval': 0, 'devRTT': 0}
    for i in range(0, last_packet_num+1):
        monitor[i] = -1
    listener_thread = Thread(
        target=listener, args=(sok, monitor, rate_queue, timeout_params))
    listener_thread.start()

    f = open(filename, "rb")
    sequence_number = 0
    file_data = f.read()

    # send fragments
    flag = 1
    while(len(monitor) and flag):
        send_list = monitor.copy()
        for sequence_number in send_list:
            # temp = current_time()
            if monitor.get('disconnected', False):
                flag = 0
                break
            if monitor.get(sequence_number, -2) == -2:
                continue
            time.sleep(0.02)
            while(current_time() - monitor.get(sequence_number, 0) < timeout_params['interval']):
                time.sleep(0.001)
            print("sending packet", sequence_number, "qlen", len(monitor))
            data = file_data[sequence_number * file_buffer_size:file_buffer_size *
                             (sequence_number + 1)]
            send_packet(sok, sequence_number, data,
                        clientAddress, monitor, last_packet_num, rate_queue)
            # print('time taken', current_time()-temp)

    f.close()
    # while (data):


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Send and receive UDP,'
    #                                  ' pretending packets are often dropped')
    # parser.add_argument('host', help='interface the server listens at;'
    #                     'host the client asks from')
    # parser.add_argument('-p', metavar='PORT', type=int, default=1060,
    #                     help='UDP port (default 1060)')
    # args = parser.parse_args()
    # print(args)

    # Server(args.host, args.p)
    Server('127.0.0.1', 1060, filename)
