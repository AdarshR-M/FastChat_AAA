"""This file is the file on the client's side of things. It handles all the actions of the client, including sending and receiving messages, logging to and exiting from the servers and all the other functions.

Attributes
----------
IP : str
    The IP address of the client

PORT : int
    The port of the client
    
PORT_S : int
    The port of the server that it is connecting to
    
IP_S : str
    The IP of the server that it is connecting to
    
PORT_BALANCER : int
    The port of the load balancer
    
MAX_SIZE : int
    The max size limit for the message

"""
import sys
import socket
import selectors
import types
import json
from enc import Encrypt
import threading
import datetime
import base64


IP = '127.0.0.1'
PORT = int(sys.argv[1])
# the port (taken as second argument in command line) should be same as the port of the server to connect to that
PORT_S = int(sys.argv[2])
IP_S = '127.0.0.1'
PORT_BALANCER = 9000
MAX_SIZE = 1048576


class Client(object):
    """Class for the client to communicate with the server
    """
    def __init__(self, *args):
        """Initialises all the class variables
        
        """
        self.IP = args[0]
        self.PORT = args[1]
        self.IP_S = args[2]
        self.PORT_S = args[3]
        self.server_sign = 0
        self.call_balancer()
        self.user = 0
        # Maintains the list of group_ids the user is a part of
        # Is updated when the client is added into the group
        self.groups = list()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect_ex((args[2], self.PORT_S))
        self.socket.setblocking(False)
        self.selector = selectors.DefaultSelector()
        self.read = selectors.EVENT_READ
        self.write = selectors.EVENT_WRITE
        self.selector.register(self.socket, self.read | self.write, data=None)
        self.exit_flag = 0
        self.keys = None
        self.encrypt = 0
        self.handle()

    def call_balancer(self):
        """This function calls the load balancer, which changes the port numbers of the servers to which it connects to. It then connects to the specific server, and disconnects the previous connection with the load balancer from the clients end.
        """
        # create a TCP/ IP socket at the client side using TCP/ IP protocol
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # connect it to server and port number to local computer
        s.connect((self.IP_S, self.PORT_S))
        # receive message form the server - 1024 B at a times
        msg = json.loads(s.recv(MAX_SIZE))
        # msg = s.recv(MAX_SIZE).decode()
        print(msg)
        # while msg:
        #     print('Received:' + msg.decode())
        #     msg = s.recv(1024)
        self.PORT_S = (msg['server_port'])
        self.IP_S = msg['server_ip']
        self.server_sign = msg['sign']
        print(self.PORT_S)
        # disconnect the client
        s.close()

    def handle(self):
        """This is the function that handles the different possibilities of events. It handles read and write events, as well as the initial connecting of the client to the server.
        
        Threading has been used to separate the input and the output processes, to make sure that we can send input while not blocking the receiving of output.
        """
        try:
            while True:
                if self.init_connect():
                    break
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
            exit()
        print('Successful Login')
        thread = threading.Thread(target=self.message_read, daemon=True)
        thread.start()
        while True:
            if self.message_send() == 0:
                break
        # thread.join()
        print('Bye!! ...')
        

    def Send(self, key):
        """This is the function that deals with the sending of messages. There are different options for direct messages, group emssages, creation, addition and deletion from a group. 

        Parameters
        ----------
        key : obj
            An object which contains the socket through which the data is to be sent, and will store the data that is to be sent through the socket

        Returns
        -------
        bool
            `False` if the socket closes and the user disconnects, `True` otherwise
        """
        while True:
            print('1. Direct Message')
            print('2. Group Message')  # implement this
            print('3. Create a new Group')  # Implement how to handle this
            print('4. Add a new participant into a group')
            print('5. Remove a participant from a group')
            print('0. Exit')
            try:
                a = int(input())
            except:
                print('Invalid Option!')
                continue
            if a in [0, 1, 2, 3, 4, 5]:
                break
            print('Invalid Option!')
        isgroup = 0
        if a in [2, 3, 4, 5]:
            isgroup = 1
        if a == 1:
            while True:
                try:
                    user = int(input('ID : '))
                    break
                except:
                    continue
        if a == 2:
            while True:
                try:
                    user = int(input('Group ID : '))
                    break
                except:
                    continue
        # Creating a new group
        if a == 3:
            participants = list()  # Stores the list of participants to be added to the group
            print("Enter 0 to stop adding participants")
            while True:
                try:
                    part_id = int(input('Participant ID: '))
                    if (part_id == 0):
                        break
                    else:
                        participants.append(str(part_id))
                except:
                    continue
            # converts the list to comma separated string to send to the server
            participants = ",".join(participants)
            print("The participants are : ", participants)
        if a in [4, 5]:
            group_id = int(input("Enter the group ID: "))
            while (group_id <= 0):
                group_id = int(
                    input("You've entered an invalid group ID, please re_enter: "))
            if a == 4:
                part_id = int(
                    input("Enter the user ID of the participant to be added: "))
            else:
                part_id = int(
                    input("Enter the user ID of the participant to be removed: "))
            while (part_id <= 0 or part_id == self.user):
                part_id = int(
                    input("You've entered an invalid user ID, please re_enter: "))

        # Handle this case in server.py
        # Create the database functions to get the participnts and the keys
        if a == 1 or a == 2:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if mask & self.write:
                    sock = key.fileobj
                    msg = {'type': 'keys', 'dest': 'server', 'from': self.user,
                           'message': user, 'isgroup': isgroup, 'response': 0}
                    sock.send(json.dumps(msg).encode())
            while True:
                if isinstance(self.keys, dict):
                    
                    break
                elif self.keys == -1:
                    self.keys = None
                    print('You are not in the group. You cannot send messages!!!')
                    return 1

        try:
            if a != 0:
                print('Input 0 to go back')
                print('Input -1 to send image')
            while True:
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if mask & self.write and a in [1, 2]:
                        message = input('* ')
                        if message == '0':
                            self.keys = None
                            return 1
                        elif message == '-1':
                            while True:
                                try:
                                    filename = input('Filename of Image : ')
                                    break
                                except:
                                    continue
                            try:
                                with open(filename, "rb") as img_file:
                                    img_bin = base64.b64encode(img_file.read())
                                img_string = img_bin.decode('utf-8')
                            except:
                                print("No Such file present")

                            sock = key.fileobj
                            time = str(datetime.datetime.now())
                            # Direct message
                            if (a == 1):
                                print("Sending Direct images")
                                key_user, enc_message, public = self.encrypt.encrypt(
                                    img_string, self.keys[str(user)])
                                msg = {'type': 'img', 'time': time, 'dest': user, 'from': self.user,
                                       'message': enc_message.decode(), 'isgroup': isgroup, 'response': 0, 'key': key_user.decode()}
                                dt = datetime.datetime.now()
                                encoded = json.dumps(msg).encode()
                                with open('client{0}_log_dm.txt'.format(self.user), 'a') as f:
                                    f.write('{0},{1},{2}\n'.format(img_string, str(dt.time()), len(encoded)))
                                # self.logfile_dm.flush()
                                sock.send(encoded)
                            # Group message
                            elif (a == 2):
                                print("Sending Group Images")
                                lst_messages = []
                                for user_id in self.keys.keys():
                                    # print("Sending message ", message, "to user {0}".format(int(user_id)))
                                    key_group_user, enc_message, public = self.encrypt.encrypt(
                                        img_string, self.keys[str(user_id)])
                                    msg = {'type': 'img', 'time': time, 'dest': int(user_id), 'group': user, 'from': self.user,  # user refers to GROUP_ID over here
                                           'message': enc_message.decode(), 'isgroup': 1, 'response': 0, 'key': key_group_user.decode()}
                                    lst_messages.append(msg)
                                dt = datetime.datetime.now()
                                lst_encoded = json.dumps(lst_messages).encode()
                                with open('client{0}_log_g.txt'.format(self.user), 'a') as f:
                                    f.write('{0},{1},{2}\n'.format(lst_messages, str(dt.time()), len(lst_encoded)))

                                print(lst_messages)
                                sock.send(lst_encoded)
                            
                        else:
                            sock = key.fileobj
                            time = str(datetime.datetime.now())
                            # Direct message
                            if (a == 1):
                                key_user, enc_message, public = self.encrypt.encrypt(
                                    message, self.keys[str(user)])
                                msg = {'type': 'msg', 'time': time, 'dest': user, 'from': self.user,
                                       'message': enc_message.decode(), 'isgroup': isgroup, 'response': 0, 'key': key_user.decode()}
                                print("Sending this message : ",msg)

                                dt = datetime.datetime.now()
                                encoded = json.dumps(msg).encode()
                                with open('client{0}_log_dm.txt'.format(self.user), 'a') as f:

                                    f.write('{0},{1},{2}\n'.format(message, str(dt.time()), len(encoded)))
                                sock.send(encoded)
                            # Group message
                            elif (a == 2):
                                lst_messages = []
                                for user_id in self.keys.keys():
                                    key_group_user, enc_message, public = self.encrypt.encrypt(
                                        message, self.keys[str(user_id)])
                                    msg = {'type': 'msg', 'time': time, 'dest': int(user_id), 'group': user, 'from': self.user,  # user refers to GROUP_ID over here
                                           'message': enc_message.decode(), 'isgroup': 1, 'response': 0, 'key': key_group_user.decode()}
                                    lst_messages.append(msg)
                                dt = datetime.datetime.now()
                                lst_encoded = json.dumps(lst_messages).encode()
                                with open('client{0}_log_g.txt'.format(self.user), 'a') as f:
                                    f.write('from {0} to group {1},{2},{3},{4}'.format(self.user,user , str(dt.time()), len(lst_encoded), lst_messages)+"\n")
                                print("Sending these split messages : ",lst_messages)
                                sock.send(lst_encoded)
        

                    elif mask & self.write and a == 3:
                        # When the servers receives json with 'message' as 'create_group' it will access database and create a group
                        sock = key.fileobj
                        time = str(datetime.datetime.now())
                        print("Creating groups ---- sending message")
                        msg = {'type': 'msg', 'time': time, 'dest': participants, 'from': self.user, # sends the list of participants to the server for the database
                               'message': 'create_group', 'isgroup': 1, 'response': 0}
                        print("Creating groups ---- json created")
                        sock.send(json.dumps(msg).encode())
                        print("Creating groups ---- message sent")
                        return 1

                    elif mask & self.write and a == 4:
                        sock = key.fileobj
                        time = str(datetime.datetime.now())
                        print("Adding to groups ---- sending message")
                        msg = {'type': 'msg', 'time': time, 'group': group_id, 'dest': part_id, 'from': self.user,  # sends the id of the participant to be added
                               'message': 'add_to_group', 'isgroup': 1, 'response': 0}
                        print("Adding to groups ---- json created")
                        sock.send(json.dumps(msg).encode())
                        print("Adding to groups ---- message sent")
                        return 1

                    elif mask & self.write and a == 5:
                        sock = key.fileobj
                        time = str(datetime.datetime.now())
                        print("Removing from groups ---- sending message")
                        msg = {'type': 'msg', 'time': time, 'group': group_id, 'dest': part_id, 'from': self.user,  # sends the id of the participant to be added
                               'message': 'remove_from_group', 'isgroup': 1, 'response': 0}
                        print("Removing from groups ---- json created")
                        sock.send(json.dumps(msg).encode())
                        print("Removing from groups ---- message sent")
                        return 1

                    elif mask & self.write and a == 0:
                        sock = key.fileobj
                        time = str(datetime.datetime.now())
                        msg = {'type': 'msg', 'time': time, 'dest': 'server', 'from': self.user,
                               'message': 'close', 'isgroup': isgroup, 'response': 0}
                        sock.send(json.dumps(msg).encode())
                        sock.close()
                        return 0
        except Exception as e:
            print("Exception as ",e)
            return 1

    def Receive(self, key):
        """This function handles all the data that is received by the client

        Parameters
        ----------
        key : obj
            An object which holds the socket through which the communication happens, along with other information    
        """
        sock = key.fileobj
        receive_data = sock.recv(MAX_SIZE)
        # print(receive_data)
        # print()
        receive_data = json.loads(receive_data)
        # The following line ignores (does not print to the file) the ping message by the server to check whether the current client is online
        # if(recv_data['message']=='ping'):
        #     return
        # print(receive_data)
        for i in range(len(receive_data)):
            # print(receive_data[i], type(receive_data[i]))
            try:
                if isinstance(receive_data[i], str) or isinstance(receive_data[i], bytes):
                    receive_data[i] = json.loads(receive_data[i])
            except Exception as e:
                print('Exception in Receive [1]', e)
                
            if (receive_data[i]['type'] == 'keys'):
                self.keys = receive_data[i]['message']  
                print()
                print("Public Keys : ", self.keys)
                print()
            elif (receive_data[i]['from'] == 'server'):
                with open('group' + str(receive_data[i]['group']) + '_client' + str(self.user), 'a') as f:
                    f.write('------------------------------------\n')
                    f.write(
                        'User : ' + str(receive_data[i]['from']) + ' | time : ' + receive_data[i]['time'] + '\n')
                    f.write('\n' + receive_data[i]['message'] + '\n')
            elif (receive_data[i]['isgroup'] == 0):
                if (receive_data[i]['type'] != 'img'):
                    message = self.encrypt.decrypt(
                        receive_data[i]['message'], receive_data[i]['key'])
                    dt = datetime.datetime.now()
                    with open('client{0}_log_dm.txt'.format(self.user), 'a') as f:
                        f.write('{0},{1},{2}\n'.format(message, str(dt.time()), len(message)))
                    with open('client' + str(self.user), 'a') as f:
                        f.write('------------------------------------\n')
                        f.write(
                            'User : ' + str(receive_data[i]['from']) + ' | time : ' + receive_data[i]['time'] + '\n')
                        f.write('\n' + message + '\n')
                        f.flush()
                elif (receive_data[i]['type'] == 'img'):
                    img_recovered = self.encrypt.decrypt(
                        receive_data[i]['message'], receive_data[i]['key'])  

                    dt = datetime.datetime.now()
                    with open('client{0}_log_dm.txt'.format(self.user), 'a') as f:
                        f.write('{0},{1},{2}\n'.format(img_recovered, str(dt.time()), len(img_recovered)))

                    if not isinstance(img_recovered,bytes):
                        img_recovered = img_recovered.encode()
                    img_recovered = base64.b64decode(img_recovered)
                    f = open('img_from' + str(receive_data[i]['from']) + 'to' + str(self.user) + '.png', "wb")
                    f.write(img_recovered)
                    f.flush()
                    f.close() 
            elif (receive_data[i]['isgroup'] == 1):
                if (receive_data[i]['type'] != 'img'):
                    message = self.encrypt.decrypt(
                        receive_data[i]['message'], receive_data[i]['key'])

                    dt = datetime.datetime.now()
                    with open('client{0}_log_g.txt'.format(self.user), 'a') as f:
                        f.write('from {0} to group {1},{2},{3},{4}'.format(receive_data[i]['from'], receive_data[i]['group'], str(dt.time()), len(message), message)+"\n")
                    with open('group' + str(receive_data[i]['group']) + '_client' + str(self.user), 'a') as f:
                        f.write('------------------------------------\n')
                        f.write(
                            'User : ' + str(receive_data[i]['from']) + ' | time : ' + receive_data[i]['time'] + '\n')
                        f.write('\n' + message + '\n')
                        f.flush()
                elif (receive_data[i]['type'] == 'img'):
                    print("Received group images")
                    img_recovered = self.encrypt.decrypt(
                        receive_data[i]['message'], receive_data[i]['key'])

                    dt = datetime.datetime.now()
                    with open('client{0}_log_g.txt'.format(self.user), 'a') as f:
                        f.write('from {0} to group {1},{2},{3},{4}'.format(receive_data[i]['from'], receive_data[i]['group'], str(dt.time()), len(img_recovered),  img_recovered)+"\n")
                    if not isinstance(img_recovered,bytes):
                        img_recovered = img_recovered.encode()
                    img_recovered = base64.b64decode(img_recovered)
                    f = open('group' + str(receive_data[i]['group']) + 'img_from' + str(receive_data[i]['from']) + 'to' + str(self.user) + '.png', "wb")
                    f.write(img_recovered)
                    f.close()

    def message_send(self):
        """Reads from the selector and calls the `Send()` function if the event is to write

        Returns
        -------
        int
            0 when the user wants to exit, it keeps running until the user presses 0
        """
        while True:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if mask & self.write:
                    key = ""
                    a = self.Send(key)
                    if a == 0:
                        return 0
                    else:
                        continue

    def message_read(self):
        """Reads from the selector and calls the `Receive()` function if the event is to read

        Returns
        -------
        int
            0 when the exit flag is 1 (which never happens)
        """
        while True:
            if self.exit_flag == 1:
                return 0
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if mask & self.read:
                    self.Receive(key)

    def init_connect(self):
        """This is the function that initially connects to the server. This is before the client is registered or authenticated
        Returns
        -------
        bool
            `True` if the process 

        Raises
        ------
        SystemExit
            If the user wants to exit
        """
        events = self.selector.select(timeout=None)
        for key, mask in events:
            if mask & self.write:
                print('Choose an option.')
                print('1. Sign In')
                print('2. Sign Up')
                print('0. Exit')
                try:
                    a = int(input('Option : '))
                    if a == 1 and self.login(key):
                        return True
                    if a == 2 and self.register(key):
                        return True
                    if a == 0:
                        sock = key.fileobj
                        msg = {'type': 'close', 'user': 'close',
                               'password': 'close'}
                        sock.send(json.dumps(msg).encode())
                        print("MESSAGE SENT FOR CLOSE")
                        sock.close()
                        raise SystemExit
                    elif a == 1 or a == 2:
                        return False
                    else:
                        print('Invalid Option')
                        return False
                except SystemExit:
                    sys.exit()
                except KeyboardInterrupt:
                    print("Caught keyboard interrupt, exiting")
                    sock = key.fileobj
                    msg = {'type': 'close', 'user': 'close', 'password': 'close'}
                    sock.send(json.dumps(msg).encode())
                    print("MESSAGE SENT FOR CLOSE")
                    sock.close()
                    sys.exit()
                except:
                    print('Invalid Option')
                    return False

    def register(self, key):
        """The function that registers to the server, when the user is appearing for the first time

        Parameters
        ----------
        key : obj
            Contains information about the socket through which the communication is happening between the server and the client

        Returns
        -------
        bool
            `False` if any invalid things are entered, `True` if everything goes properly

        Raises
        ------
        SystemExit
            If the user wants to exit
        """
        try:
            user = int(input('User ID : '))
            password = input('Password : ')
        except:
            print('Invalid Username!')
            return False
        sock = key.fileobj
        self.encrypt = Encrypt()
        public_key = self.encrypt.get_public_key()
        msg = {'type': 'new', 'user': user, 'password': password,
               'sign': self.server_sign, 'public_key': public_key.decode()}
        try:
            sock.send(json.dumps(msg).encode())
        except:
            return False
        while True:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if mask & self.read:
                    sock = key.fileobj
                    recv_data = json.loads(sock.recv(MAX_SIZE))
                    try:
                        print("Response : ", recv_data['response'])
                        if recv_data['response'] == 1:
                            print(recv_data['server_message'])
                            print('1. Do you want to try a different username?')
                            print('0. Exit')
                            a = int(input('Your choice : '))
                            if a == 1:
                                self.selector.unregister(sock)
                                sock.close()
                                self.socket = socket.socket(
                                    socket.AF_INET, socket.SOCK_STREAM)
                                self.socket.connect_ex(
                                    (self.IP_S, self.PORT_S))
                                self.socket.setblocking(False)
                                self.selector.register(
                                    self.socket, self.read | self.write, data=None)
                                return False
                            elif a == 0:
                                raise SystemExit
                        elif recv_data['response'] == 0:
                            print(recv_data['server_message'])
                            self.user = user
                            self.encrypt.save_keys('client_' + str(self.user))
                            return True
                    except SystemExit:
                        sys.exit()
                    except Exception as e:
                        print('Invalid option!', e)
                        self.selector.unregister(sock)
                        sock.close()
                        self.socket = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        self.socket.connect_ex((self.IP_S, self.PORT_S))
                        self.socket.setblocking(False)
                        self.selector.register(
                            self.socket, self.read | self.write, data=None)
                        return False

    def login(self, key):
        """This function is for when a client is logging in, when the client has already been registered before

        Parameters
        ----------
        key : obj
            Contains information about the socket and data inside it

        Returns
        -------
        bool
            `True` if successful login, `False` if not

        Raises
        ------
        SystemExit
            If user wants to exit
        """
        try:
            user = int(input('User ID : '))
            password = input('Password : ')
        except:
            print('Invalid Username!')
            return False
        sock = key.fileobj
        msg = {'type': 'login', 'user': user,
               'password': password, 'sign': self.server_sign}
        sock.send(json.dumps(msg).encode())
        while True:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                if mask & self.read:
                    sock = key.fileobj
                    recv_data = json.loads(sock.recv(MAX_SIZE))
                    try:
                        if recv_data['response'] == 1:
                            print(recv_data['server_message'])
                            print('1. Retry')
                            print('0. Exit')
                            a = int(input('Your choice : '))
                            if a == 1:
                                self.selector.unregister(sock)
                                sock.close()
                                self.socket = socket.socket(
                                    socket.AF_INET, socket.SOCK_STREAM)
                                self.socket.connect_ex(
                                    (self.IP_S, self.PORT_S))
                                self.socket.setblocking(False)
                                self.selector.register(
                                    self.socket, self.read | self.write, data=None)
                                return False
                            elif a == 0:
                                raise SystemExit
                        elif recv_data['response'] == 0:
                            print(recv_data['server_message'])
                            self.user = user
                            self.encrypt = Encrypt('client_'+str(self.user))
                            return True
                    except SystemExit:
                        sys.exit()
                    except Exception as e:
                        print('Invalid option!', e)
                        self.selector.unregister(sock)
                        sock.close()
                        self.socket = socket.socket(
                            socket.AF_INET, socket.SOCK_STREAM)
                        self.socket.connect_ex((self.IP_S, self.PORT_S))
                        self.socket.setblocking(False)
                        self.selector.register(
                            self.socket, self.read | self.write, data=None)
                        return False


c = Client(IP, PORT, IP_S, PORT_S)