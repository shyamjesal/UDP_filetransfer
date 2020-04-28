#!/usr/bin/env python3
import socket
import argparse
from threading import Timer, Thread
import threading
import os
import time
os.system('pip install xxhash')
import xxhash
from tkinter import filedialog
from tkinter import *
import RUDP_client
import RUDP_server

from zipfile import ZipFile
window = Tk()

window.title("Shareit by Bitsians")

window.geometry('350x200')

lbl = Label(window, text="Are you a Sender or receiver")

lbl.grid(column = 2, row = 0)

def create_zip(files):
	zipObj = ZipFile("tempfile.zip", 'w')
	for file in files:
		zipObj.write(file)
	return "tempfile.zip"	
def extract_zip(file, my_dir):
	zip = ZipFile(file, 'r')
	for zip_info in zip.infolist():
		if zip_info.filename[-1] == '/':
			continue
		zip_info.filename = os.path.basename(zip_info.filename)
		zip.extract(zip_info, my_dir)

def clicked1():

    lbl.configure(text="Are you a Sender or receiver !!")
    files = filedialog.askopenfilenames()
    print(files)
    zip_file = create_zip(files)
    RUDP_server.Server('127.0.0.1', 1060, zip_file)
    os.remove("tempfile.zip")

def clicked2():

    lbl.configure(text="Are you a Sender or receiver")
    root = Tk()
    root.title("Select directory to save")
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    root.destroy()
    RUDP_client.Client('127.0.0.1', 1060)
    extract_zip("./receivedfile.zip",folder_selected)
    os.remove("./receivedfile.zip")

btn1 = Button(window, text="Sender", command = clicked1)

btn1.grid(column=1, row=1)

btn2 = Button(window, text="Receiver", command = clicked2)

btn2.grid(column = 3, row=1)

window.mainloop()