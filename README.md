Designing an application layer protocol which uses UDP sockets to relaibly transfer packets between a client and server. 

TO USE THE PROTOCOL:

Module name is RUDP_protocol

to import server module:
"from RUDP_protocol import RUDP_server"

to send a file from the server:
"RUDP_server.Server(ip_address_of_server, port_no, file_path_to_Send)"


to import client module:
"from RUDP_protocol import RUDP_client"


to receive a file by client:
"RUDP_client.Client(ip_address_of_server, port, file_path_to_Send)"

Required Libraries to be installed in python3:
1. python3
2. xxhash (if not installed do "pip3 install xxhash" on terminal)
3. tkinter (if not installed do "apt-get install python3-tk" on terminal)



TO USE THE APPLICATION

Run the file on terminal by the command:

"python3 file_transfer_application.py"

In the application window select the option sender or receiver.

IF sender:

Select the files to send and put the code displayed in the message dialog box in the code asked on receiver side.

IF receiver:

Select the path where to save the files and put the recever code from sender side in receiver code dialog box.
