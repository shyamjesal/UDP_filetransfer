#!/usr/bin/env python3

import socket
import argparse
import time
import xxhash
from timeit import default_timer as current_time
from threading import Timer, Thread
filename = "receivedfile.zip"
buffer_size = 65507


def process_data(sok, data_string, monitor):
    data_hash = data_string[4:8]
    data_loaded = data_string[8:]
    if data_hash != xxhash.xxh32(data_loaded).digest():
        return
    first_byte = data_string[0]
    sequence_num = (first_byte & int('3f', 16)).to_bytes(
        1, byteorder='big') + data_string[1:4]
    sequence_num = int.from_bytes(sequence_num[0:4], byteorder='big')
    if first_byte >> 7 & 1:
        if first_byte >> 6 & 1:
            monitor['eof'] = sequence_num
        monitor[sequence_num] = data_loaded
    # print("got packet", sequence_num, "of size", len(data_string))

    # Thread(target=send_ak, args=(sok, sequence_num)).start()
    send_ak(sok, sequence_num)


def send_ak(sok, number):
    message = number.to_bytes(4, byteorder='big')
    sok.send(message)
    # print('sending ack for', number)


def write_file(sok, monitor):
    written = 0
    f = open(filename, 'wb')
    # data = b''
    while(True):
        if written in monitor:
            f.write(monitor[written])
            # data += monitor[written]
            monitor.pop(written, -1)
            if monitor.get('eof', -1) == written:
                monitor['finished'] = True
                break
            written += 1
    f.write(data)
    print("file written")
    f.close()
    exit()


def initiate_handshake(host, port):
    timeout_time = 0.5
    sok = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sok.connect((host, port))
    message = 'start'
    while(True):
        try:
            sok.send(message.encode())
            sok.settimeout(timeout_time)
            sok.recvfrom(buffer_size)
            return sok
        except socket.timeout:
            print('will try after {} seconds'.format(timeout_time))
        except ConnectionRefusedError:
            print('It seems the server is not online, sleeping for {} seconds'.format(
                timeout_time))
            time.sleep(timeout_time)
        finally:
            timeout_time *= 2


def Client(host, port):
    sok = initiate_handshake(host, port)
    start_time = current_time()
    monitor = {}
    file_thread = Thread(
        target=write_file, args=(sok, monitor))
    file_thread.start()
    data, addr = sok.recvfrom(buffer_size)

    timeout_interval = 0.5
    while(True):
        temp = current_time()
        try:
            # temp1 = current_time()
            process_data(sok, data, monitor)
            # print('time1', -temp1+current_time())
            # temp2 = current_time()
            sok.settimeout(timeout_interval)
            # print('time2', -temp2+current_time())
            # temp3 = current_time()
            data, addr = sok.recvfrom(buffer_size)
            # print('time3', -temp3+current_time())
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
                break
            if monitor.get('finished', False):
                print("transfer Complete in", current_time()-start_time)
                break
        print('time taken', current_time()-temp)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Send and receive UDP,'
    #                                  ' pretending packets are often dropped')
    # parser.add_argument('host', help='interface the server listens at;'
    #                     'host the client asks from')
    # parser.add_argument('-p', metavar='PORT', type=int, default=1060,
    #                     help='UDP port (default 1060)')
    # args = parser.parse_args()
    Client('127.0.0.1', 1061)
