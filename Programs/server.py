"""This file is the file on the server's side of things. It handles all the actions of the server, including sending and receiving messages, communicating with other servers, looking at the database, etc

Attributes
----------
IP : str
    The IP address of the server

PORT : int
    The port of the server
    
ID : int
    The server ID of the server (should be in sequence, the first server to be created must have ID 1, and so on)
    
N : int
    The number of servers that are to be created
    
MAX_SIZE : int
    The max size limit for the message

"""
import sys
import socket
import selectors
import types
import json
import datetime
from database import *
from enc import Encrypt
import base64
import hashlib

# PORT = 24375
# Changing the port so that every time the old port need not be freed
PORT = int(sys.argv[1])
IP = '127.0.0.1'
ID = int(sys.argv[2])
N = int(sys.argv[3])


'''
    Tags:
         msg - normal message
         reply - server reply
         rw - read/write state
'''

MAX_SIZE = 1048576

class Server(object):

    def __init__(self, IP, PORT, ID, N):
        """This is the initialisation function, to set all the class variables of the class Server

        Parameters
        ----------
        IP : str
            The IP address of the server
        PORT : int
            The port of this server
        ID : int
            The ID of the server
        N : int
            The ID of the server
        """
        self.IP = IP
        self.PORT = PORT
        self.ID = ID
        self.N = N
        self.encrypt = Encrypt('server_keys')
        # self.context = ssl.create_default_context()
        self.client_sockets = dict()
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind_listener()
        self.selector = selectors.DefaultSelector()
        self.server_selector = selectors.DefaultSelector()
        self.read = selectors.EVENT_READ
        self.write = selectors.EVENT_WRITE
        self.selector.register(self.listening_socket, self.read, data=None)
        self.server_sockets = {self.ID: self.listening_socket}
        self.server_sock = []
        self.Database = CentralDatabase()
        self.Database.init_numclients(N)
        self.connect_servers()

        # Later change to a database
        # self.user_pass = dict()
        # Creating the database object to access the common database
        self.handle_events()

        # Initializing the numclients table for tallying the number of clients connected to the respective servers
        

    def bind_listener(self, *args):
        """This binds the listening socket to the port and IP of the server, and sets the setblocking parameter to `False` 
        """
        if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], int):
            self.IP = args[0]
            self.PORT = args[1]
        self.listening_socket.bind((self.IP, self.PORT))
        self.listening_socket.listen()
        # self.listening_socket = self.context.wrap_socket(self.listening_socket, server_side=True)
        self.listening_socket.setblocking(False)

    def connect_servers(self):
        """This function establishes connections between each pair of servers
        """
        for i in range(1, self.ID):
            if self.ID == 1:
                break
            port = self.PORT - self.ID + i
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect_ex((self.IP, port))
            sock.setblocking(False)
            self.server_sock.append(sock)
            # sock.send(str(self.ID).encode())
            data = types.SimpleNamespace(ID = i, server_name = self.ID, message = '', status = '')
            self.server_selector.register(sock, self.read | self.write, data = data)
        while len(self.server_sock) < self.N-1:
            events = self.selector.select(timeout=None)
            for key, mask in events:
                sock = key.fileobj
                if mask & self.read and key.data == None:
                    conn, addr = sock.accept()
                    print(f"Accepted connection from {addr}")
                    Id = self.ID # int(conn.recv(1024).decode())#addr[1]-self.PORT+self.ID
                    # print(Id)
                    # self.server_sockets[Id] = conn
                    self.server_sock.append(conn)
                    data = types.SimpleNamespace(ID = Id, server_name = self.ID, message = '', status = '')
                    self.server_selector.register(conn, self.read | self.write, data = data)
        n = 0
        x = 0
        while x < self.N-1 or n < self.N-1:
            events = self.server_selector.select(timeout=None)
            for key, mask in events:
                if mask & self.read:
                    sock = key.fileobj
                    d = key.data
                    Id = int(sock.recv(1024).decode())
                    self.server_sockets[Id] = sock
                    data = types.SimpleNamespace(ID = Id, server_name = self.ID, message = '', status = d.status)
                    self.server_selector.modify(sock, self.read | self.write, data = data)
                    n += 1
                if mask & self.write:
                    if key.data.status != 'none':
                        sock = key.fileobj
                        data = key.data
                        sock.send(str(self.ID).encode())
                        data = key.data
                        data = types.SimpleNamespace(ID = data.ID, server_name = self.ID, message = '', status = 'none')
                        self.server_selector.modify(sock, self.read | self.write, data = data)
                        x += 1
        #print(self.server_sockets)
        print("All servers are inter-connected")

    def register_client(self, key, details):
        """This function takes care of the registration of the client (for the first time only, after that it is authentication)

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        details : dict
            Is a JSON object which has the information about the message sent by the client to the server, namely, the user and the encrypted password
        """
        sock = key.fileobj
        data = key.data
        try:
            if (not self.Database.check_user(details['user'])):
                # Commenting out the following line because no need to use dictionary - using database instead
                # self.user_pass[details['user']] = details['password']

                # Need to put the appropriate server ID as the third parameter
                pasw = details['password']
                if not isinstance(pasw, bytes):
                    pasw = pasw.encode()
                pasw = base64.b64encode(hashlib.sha256(pasw).digest()).decode()
            
                output = self.Database.insert_newuser(
                    details['user'], pasw , self.ID, details['public_key'])
                if (output == True):
                    print("User Registered successfully!!")
                else:
                    print("User registration unsuccessful")

                msg = {'type': 'server reply',
                    'server_message': 'Registered and Connected', 'response': 0}
                self.client_sockets[details['user']] = sock

                # Commenting out the following line because no need to use dictionary - using database instead
                # self.user_pass[details['user']] = details['password']
                msg = json.dumps(msg)
                data = types.SimpleNamespace(addr=data.addr, status='reply', response=0,
                                            user=details['user'], server_name=self.ID, message=msg)
                self.selector.modify(sock, self.read | self.write, data=data)
            else:
                msg = {'type': 'server reply',
                    'server_message': 'User already present! Choose different username', 'response': 1}
                msg = json.dumps(msg)
                data = types.SimpleNamespace(addr=data.addr, status='reply', response=1,
                                            user=details['user'], server_name=self.ID, message=msg)
                self.selector.modify(sock, self.read | self.write, data=data)
        except Exception as e:
            print("Exception in register client ", e)

    def authenticate_client(self, key, mask):
        """This function authenticates the client if it has already been registered, with it's password and ID

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        mask : obj
            Gives information about what type of operation must be performed, whether it is a read operation or a write operation

        Raises
        ------
        KeyError
            If the username and password don't match the records
        """
        sock = key.fileobj
        data = key.data
        recv_data = json.loads(sock.recv(MAX_SIZE))
        try:
            if(recv_data['user']=='close'):
                self.Database.update_numclients(self.ID, -1)
                self.selector.unregister(sock)
                # Updates the num clients table 
                print('Deregistered before registering')
                sock.close()
                return
                
            user = recv_data['user']
            pasw = recv_data['password']
            if not isinstance(pasw, bytes):
                pasw = pasw.encode()
            pasw = base64.b64encode(hashlib.sha256(pasw).digest()).decode()
            sign = recv_data['sign']
            M = self.IP + str(self.PORT)
            if not self.encrypt.RSA_verify(M, sign):
                self.selector.unregister(sock)
                print('Malicious attempt..., Closing socket')
                sock.close()
                return
            # To throw an error if the user, password do not match the records in database
            if (not self.Database.check_cred(user, pasw)):
                raise KeyError

            # If the message is for logging into the account
            if self.Database.check_cred(user, pasw) and recv_data['type'] == 'login':
                self.client_sockets[user] = sock
                self.Database.change_server(user, self.ID)
                msg = {'type': 'server reply',
                       'server_message': 'Succesful Login!', 'response': 0}
                msg = json.dumps(msg)
                data = types.SimpleNamespace(addr=data.addr, status='reply', response=0,
                                             user=user, server_name=self.ID, message=msg)
                self.selector.modify(sock, self.read | self.write, data=data)

            # If the message is for registering a new user
            elif recv_data['type'] == 'new':
                self.register_client(key, recv_data)
            # (Redundant) If the user, password is not present in the database
            elif recv_data['type'] == 'login':
                msg = {'type': 'server reply',
                       'server_message': 'Invalid Login! Authentication failed.', 'response': 1}
                msg = json.dumps(msg)
                data = types.SimpleNamespace(addr=data.addr, status='reply', response=1,
                                             user=user, server_name=self.ID, message=msg)
                self.selector.modify(sock, self.read | self.write, data=data)
        except Exception as e:
            # If the message is for registering a new user
            if recv_data['type'] == 'new':
                self.register_client(key, recv_data)
            # If the user, password is not present in the database
            elif recv_data['type'] == 'login':
                print("Exception occured in authenticate client", e)
                msg = {'type': 'server reply',
                       'server_message': 'Invalid Login! Authentication failed.', 'response': 1}
                msg = json.dumps(msg)
                data = types.SimpleNamespace(addr=data.addr, status='reply', response=1,
                                             user=user, server_name=self.ID, message=msg)
                self.selector.modify(sock, self.read | self.write, data=data)

    def accept_wrapper(self, sock):
        """This function accepts the initial condition from the client, before it is authenticated by the server. It also calls the function to update the numclients table, which gives us an idea on the load of the servers

        Parameters
        ----------
        sock : obj
            The socket used for communication between client and server, before authentication
        """
        conn, addr = sock.accept()
         # Updates the num clients table
        self.Database.update_numclients(self.ID , 1)
        print(f"Accepted connection from {addr}")
        # Code to send pending messages to the user
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, status='auth', response=0,
                                     user='', server_name=self.ID, message='')
        self.selector.register(conn, self.read | self.write, data=data)

    def server_messages(self):
        """This function is used to send messages between servers, since all the servers are connected to each other. This is essential to be able to send messages between two clients who are not connected to the same server
        """
        events = self.server_selector.select(timeout=None)
        for key, mask in events:
            if mask & self.read:
                sock = key.fileobj
                serverID = key.data
                message = sock.recv(MAX_SIZE)
                if str(message) != '':
                    print("Server Message : ", message)
                RD = json.loads(message)

                for recv_data in RD:
                    try:
                        if isinstance(recv_data, str) or isinstance(recv_data, bytes):
                            recv_data = json.loads(recv_data)
                    except Exception as e:
                        print('Exception in server_messages [1]', e)
                    if recv_data['dest'] in self.client_sockets.keys():
                        sock = self.client_sockets[recv_data['dest']]
                        KEY = self.selector.get_key(sock)
                        data_n = KEY.data
                        print(recv_data)
                        msg = recv_data
                        # if (recv_data['isgroup'] == 0):
                        #     msg = {'type': 'msg', 'dest': recv_data['dest'], 'from': recv_data['from'],
                        #        'message': recv_data['message'], 'time': recv_data['time'], 'isgroup': recv_data['isgroup'], 'response': 0, 'key' : recv_data['key']}
                        # else:
                        #     msg = {'type': 'msg', 'dest': recv_data['dest'], 'from': recv_data['from'], 'group': recv_data['group'],
                        #        'message': recv_data['message'], 'time': recv_data['time'], 'isgroup': recv_data['isgroup'], 'response': 0, 'key' : recv_data['key']}
                        if data_n.message == '':
                            data_n.message = []
                        data_n.message.append(msg)
                        data_n.status = 'rm'
                        self.selector.modify(
                            sock, self.read | self.write, data=data_n)
                    else:
                        # store in database
                        a = 1
            elif mask & self.write and key.data.status == 'msg':
                sock = key.fileobj
                data = key.data
                sock.send(json.dumps(data.message).encode())
                data_n = data
                data_n.status = 'none'
                data_n.message = ''
                self.server_selector.modify(
                    sock, self.read | self.write, data=data_n)

    def handle_events(self):
        """This is the function that handles the different events that can occur. It first reads from the selector, and then depending on the event, it decides to receive or send messages.
        """
        try:
            while True:
                self.server_messages()
                events = self.selector.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    elif mask & self.read:
                        self.service_connection(key, mask)
                    elif mask & self.write and key.data.status == 'reply':
                        self.reply(key)
                    elif mask & self.write and key.data.status == 'rm':
                        self.forward(key)

        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self.selector.close()

    def reply(self, key):
        """This function is used to only send messages to the client, and modify the socket to it's next state, which could either be a read state or both read and write state. This function also is responsible for querying from the table for unread messages, which would then be delivered to the respective clients

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        """
        print("Inside the reply function")
        sock = key.fileobj
        data = key.data
        print(data.message)
        sock.send(data.message.encode())
        data_message = json.loads(data.message)
        if (type(data_message) == dict and data_message['server_message'] == 'Succesful Login!'):
            print("The user is {0}".format(int(data.user)))
            unread_messages = self.Database.show_message(int(data.user))
            unread_group_messages = self.Database.show_group_message(int(data.user))
            print("Querying from tables inside the reply function")
            if (unread_messages or unread_group_messages):
                print("Sending unsent messages")
                lst_unread = []
                for message in unread_messages:
                    #msg_unread = {'type': 'msg', 'from': message[0], 'message': message[3], 'time': message[2], 'isgroup': 0, 'response': 0}
                    # sock.send(json.dumps(msg_unread).encode())
                    msg_unread = message[3]
                    lst_unread.append(msg_unread)
                for message in unread_group_messages:
                    #msg_unread = {'type': 'msg', 'from': message[0], 'group': message[1], 'message': message[3], 'time': message[2], 'isgroup': 1, 'response': 0}
                    msg_unread = message[3]
                    lst_unread.append(msg_unread)
            
                data = types.SimpleNamespace(addr=data.addr, status='rm', response=0,
                                             user=data.user, server_name=self.ID, message=lst_unread)
                self.selector.modify(sock, self.read | self.write, data=data)
            else:
                data = types.SimpleNamespace(addr=data.addr, status='msg', response=0,
                                             user=data.user, server_name=self.ID, message='')
                self.selector.modify(sock, self.read | self.write, data=data)
        elif data.response == 1:
            self.selector.unregister(sock)
            sock.close()
            # Updates the num clients table 
            self.Database.update_numclients(self.ID, -1)
            print('Deregistered')
        else:
            data = types.SimpleNamespace(addr=data.addr, status='msg', response=0,
                                         user=data.user, server_name=self.ID, message='')
            self.selector.modify(sock, self.read | self.write, data=data)

    def forward(self, key):
        """This function forwards the messages that have been generated with both a read and write status to the client directly, and then updates the socket back to an empty message

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        """
        sock = key.fileobj
        data = key.data
        msg = json.dumps(data.message)
        print("Forwarding message :", msg)
        sock.send(msg.encode())
        data.status = 'msg'
        data.message = ''
        self.selector.modify(sock, self.read | self.write, data=data)

    def create_group(self, key, details):
        """Create a group with the list of participants and the admin of the group to be formed

        Parameters
        ----------
        key : obj
            Contains information about the socket through which the request came from, so can be used to find the admin of the new group.
        details : _type_
            The message, which contains information on the new participants of the group.
        """
        participants = details['dest'].split(',')
        participants = [int(s) for s in participants] 
        print("Integer array of participants (without the admin) : ",participants)
        sock = key.fileobj
        data = key.data
        participants.insert(0, data.user)
        print("Here before creation of group")
        print("New participants (with admin) :", participants)
        group_id = self.Database.create_group(data.user, participants)
        print("Group ID: ", group_id)
        try:
            if (group_id == -1):  # Send message to client later
                print("List of Participants not valid")
            else:
                msg = {'type': 'msg', 'dest': data.user, 'from': 'server', 'message': 'You have successfully created the group: ' +
                str(group_id), 'group': group_id, 'time': str(datetime.datetime.now()), 'isgroup': 1, 'response': 0}
                if data.message == '':
                    data.message = []
                data.message.append(msg)
                if data.response == 1:
                    ################################################### REQUIRES CLARIFICATION (WHAT TO "HANDLE LATER"?)#####################################################
                    # handle later
                    a = 1
                data.status = 'rm'
                print(data)
                participants.remove(data.user)
                self.selector.modify(sock, self.read | self.write, data=data)
                for part_id in participants:
                    dest_server = self.Database.check_server(part_id)
                    if (dest_server == -2):
                        print("User ", part_id,
                            "has not registered time 1")
                    elif dest_server == -1:
                        msg = {'type': 'msg', 'from': 'server', 'group': group_id, 'dest': part_id,
                        'message': "You have been added to group {1} by {0}".format(data.user, group_id), 'time': str(datetime.datetime.now()), 'isgroup': 1, 'response': 0}
                        self.Database.insert_group_message(
                            data.user, part_id, str(datetime.datetime.now()), group_id, json.dumps(msg))
                        print("Entered the message for user ",
                            part_id, "stored in database")
                        self.Database.displayallgroupmessage()
                    elif dest_server == self.ID:
                        msg = {'type': 'msg', 'from': 'server', 'group': group_id, 'dest': part_id,
                            'message': "You have been added to group {1} by {0}".format(data.user, group_id), 'time': str(datetime.datetime.now()), 'isgroup': 1, 'response': 0}
                        # data_send = types.SimpleNamespace(addr=data.addr, status = 'msg', response = 1,
                        #                              user = data.user, server_name = self.ID, message = '')
                        sock = self.client_sockets[part_id]
                        key = self.selector.get_key(sock)
                        data_n = key.data
                        if data_n.message == '':
                            data_n.message = []
                        data_n.message.append(msg)
                        if data_n.response == 1:
                            ################################################### REQUIRES CLARIFICATION (WHAT TO "HANDLE LATER"?)#####################################################
                            # handle later
                            a = 1
                        data_n.status = 'rm'
                        print(data_n)
                        self.selector.modify(
                            sock, self.read | self.write, data=data_n)
                    elif dest_server > 0:
                        msg = {'type': 'msg', 'from': 'server', 'group': group_id, 'dest': part_id,
                            'message': "You have been added to group {1} by {0}".format(data.user, group_id), 'time': str(datetime.datetime.now()), 'isgroup': 1, 'response': 0}
                        sock = self.server_sockets[dest_server]
                        key = self.server_selector.get_key(sock)
                        data_n = key.data
                        if data_n.message == '':
                            data_n.message = []
                        data_n.message.append(msg)
                        data_n.status = 'msg'
                        print(data_n)
                        self.server_selector.modify(
                            sock, self.read | self.write, data=data_n)

        except Exception as e:
            print('Some exception occured', e)


    def group_chat(self, key, details):
        """This function is responsible for sending group chat messages between two clients, by handling messages between servers and also between clients and servers

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        details : dict
            A JSON object which contains the encrypted message to be sent to members of the group
        """
        sock = key.fileobj
        data = key.data
        # get a list of users from the database for the given group id except the admin
        participants = self.Database.group_participants(details['group'])
        print("Participants: ",participants)
        if not details['from'] in participants:
            print("Sender not part of the group. Not sending the message.")
            return
        # Removing the sender from the participants list
        try:
            participants.remove(details['from'])
        except:
            a = 1
            # send to the respective server
        part_id = details['dest']
        try:
            print("Participant ID: ", part_id)
            dest_server = self.Database.check_server(part_id)
            if dest_server == -2:
                print("User ", part_id,
                    "has not registered time 1")
            elif dest_server == -1:
                self.Database.insert_group_message(
                    data.user, part_id, details['time'], details['group'], json.dumps(details))
                print("The message is : ",  details['message'])
                print("Entered the message for user ",
                    part_id, "stored in database")
                self.Database.displayallgroupmessage()
            elif dest_server == self.ID:
                print("Same destination server")
                # msg = {'type': 'msg', 'from': data.user, 'group': details['group'],
                #     'message': details['message'], 'time': details['time'], 'isgroup': 1, 'response': 0}
                msg = details
                # data_send = types.SimpleNamespace(addr=data.addr, status = 'msg', response = 1,
                #                              user = data.user, server_name = self.ID, message = '')
                sock = self.client_sockets[part_id]
                key = self.selector.get_key(sock)
                data_n = key.data
                if data_n.message == '':
                    data_n.message = []
                data_n.message.append(msg)
                if data_n.response == 1:
                    ################################################### REQUIRES CLARIFICATION (WHAT TO "HANDLE LATER"?)#####################################################
                    # handle later
                    a = 1
                data_n.status = 'rm'
                print(data_n)
                self.selector.modify(
                    sock, self.read | self.write, data=data_n)
            elif dest_server > 0:
                print("Different destination server")
                # msg = {'type': 'msg', 'dest': part_id, 'from': data.user, 'group': details['group'],
                #     'message': details['message'], 'time': details['time'], 'isgroup': 1, 'response': 0}
                msg = details
                sock = self.server_sockets[dest_server]
                key = self.server_selector.get_key(sock)
                data_n = key.data
                if data_n.message == '':
                    data_n.message = []
                data_n.message.append(msg)
                data_n.status = 'msg'
                print(data_n)
                self.server_selector.modify(
                    sock, self.read | self.write, data=data_n)
        except Exception as e:
            print("Some exception occurred inside group_chat function: ", e)
    
    def add_to_group(self, part_id, admin_id, group_id, key):
        """This is a function for user `admin_id` to add user `part_id` into the group `group_id`

        Parameters
        ----------
        part_id : int
            The ID of the participant to be added
        admin_id : int
            The ID of the person who is adding the participant
        group_id : int
            The ID of the group to be added
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket. In this case, we use it to forward a confirmation message about the addition into the group
        """
        check = self.Database.add_participant(part_id, admin_id, group_id)
        if check == -1:
            print("The user {0} isn't an admin of the group {1}".format(admin_id, group_id))
        elif check == -2:
            print("The participant {0} is already in the group {1}".format(part_id, group_id))
        elif check == -3:
            print("The group {0} does not exist".format(group_id))
        elif check == -4:
            print("The user {0} does not exist".format(part_id))
        elif check == 1:
            time = str(datetime.datetime.now())
            msg = {'type': 'msg', 'time': time, 'group': group_id, 'from': admin_id,  
                                        'message': "{0} has been added to the group".format(part_id), 'isgroup': 1, 'response': 0}
            self.group_chat(key,msg)


    def remove_from_group(self, part_id, admin_id, group_id, key):
        """This is a function for user `admin_id` to remove user `part_id` from the group `group_id`

        Parameters
        ----------
        part_id : int
            The ID of the participant to be removed
        admin_id : int
            The ID of the person who is removing the participant
        group_id : int
            The ID of the group to be removed
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket. In this case, we use it to forward a confirmation message about the removal from the group
        """
        check = self.Database.del_participant(part_id, admin_id, group_id)
        if (check == -1):
            print("The user {0} isn't an admin of the group {1}".format(admin_id, group_id))
        elif check == -2:
            print("The participant {0} isn't in in the group {1}".format(part_id, group_id))
        elif check == -3:
            print("The group {0} does not exist".format(group_id))
        elif check == 1:
            time = str(datetime.datetime.now())
            msg = {'type': 'msg', 'time': time, 'group': group_id, 'from': admin_id,  
                                        'message': "{0} has been removed from the group".format(part_id), 'isgroup': 1, 'response': 0}
            self.group_chat(key,msg)
            
    def get_keys(self, details):
        """Get a dictionary containing a single key value pair of the user and his public key

        Parameters
        ----------
        details : dict
            The message attribute of this dict contains the user id of the user

        Returns
        -------
        dict
            dict with a single key value pair of the user and his public key
        """
        if details['isgroup'] == 0:
            key = self.Database.fetch_key(details['message'])
            return {details['message'] : key}
        
    def get_group_keys(self, details, user_id):
        """Get a dictionary containing key value pairs of all members of a group and their public keys 

        Parameters
        ----------
        details : dict
            The message attribute of this dict contains the group id of the group
        user_id : int
            The user id to be excluded from the dict (he's querying for the other keys)

        Returns
        -------
        dict
            dict with key value pairs of the participants of the group and their public keys (except the one of the user_id)
        """
        if details['isgroup'] == 1:
            dict1 = self.Database.fetch_group_keys(details['message'], user_id)
            return dict1
    
    def message(self, key):
        """This is a function to accept a message from a client, and then handle the following events appropriately, like which server to redirect the message to, etc. It also calls the group chat functions

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket.
        """
        sock = key.fileobj
        data = key.data
        recv_data = json.loads(sock.recv(MAX_SIZE))
        print("List of online clients with their sockets : ", self.client_sockets)
        print("INSIDE MESSAGE")
        try:
            print("Data received : ", recv_data)
            if (isinstance(recv_data,list)):
                for msg in recv_data:
                    if isinstance(msg,str) or isinstance(msg,bytes):
                        msg = json.loads(msg)
                    # if recv_data['isgroup'] == 1 and recv_data['message'] == 'add_to_group':
                    #     print(recv_data)
                    #     self.add_to_group(recv_data['dest'], data.user, recv_data['group'],key)
                    # elif recv_data['isgroup'] == 1 and recv_data['message'] == 'remove_from_group':
                    #     print(recv_data)
                    #     self.remove_from_group(recv_data['dest'], data.user, recv_data['group'],key)
                    # elif recv_data['isgroup'] == 1 and recv_data['message'] == 'create_group':
                    #     print(recv_data)
                    #     self.create_group(key, recv_data)
                    if msg['isgroup'] == 1 and msg['message'] != 'create_group':
                        print("BEFORE GROUP CHAT FUNCTION")
                        self.group_chat(key, msg)
                        print("Group chat funct done")
            elif recv_data['type'] == 'keys':
                if recv_data['isgroup'] == 0:
                    keys = self.get_keys(recv_data)
                else:
                    keys = self.get_group_keys(recv_data, data.user)
                print("The keys are : ", keys)
                msg = {'type': 'keys', 'from' :'server', 'message' : keys, 
                      'isgroup' : recv_data['isgroup'], 'response' : 0}
                data_n = data
                if data_n.message == '':
                    data_n.message = []
                data_n.message.append(msg)
                data_n.status = 'rm'
                self.selector.modify(sock, self.read | self.write, data = data_n)
            elif recv_data['isgroup'] == 1 and recv_data['message'] == 'add_to_group':
                print(recv_data)
                self.add_to_group(recv_data['dest'], data.user, recv_data['group'],key)
            elif recv_data['isgroup'] == 1 and recv_data['message'] == 'remove_from_group':
                print(recv_data)
                self.remove_from_group(recv_data['dest'], data.user, recv_data['group'],key)
            elif recv_data['isgroup'] == 1 and recv_data['message'] == 'create_group':
                print(recv_data)
                self.create_group(key, recv_data)
            else:
                if recv_data['dest'] == 'server' and recv_data['message'] == 'close':
                    print("HI! INSIDE CLOSE FUNCTION ")
                    pending_messages = data.message
                    for msg1 in pending_messages:
                        print("Entered the for loop inside close function")
                        self.Database.insert_message(
                            msg1['from'], data.user, msg1['time'], json.dumps(msg1))
                        print("Entered the message for user ",
                                data.user, "stored in database")
                        self.Database.displayallmessage()

                    ########################################### CLARIFICATION REQUIRED - pending_messages is empty ###########################################################
                    print("Pending Messages")
                    # print(pending_messages)
                    self.Database.change_server(data.user, -1)
                    self.Database.update_numclients(self.ID, -1)
                    self.client_sockets.pop(data.user)
                    self.selector.unregister(sock)
                    # Updates the num clients table 
                    print('Deregistered ' + str(data.user))
                    sock.close()
                else:
                    dest_server = self.Database.check_server(recv_data['dest'])
                    if (dest_server == -2):
                        print("User ", recv_data['dest'],
                                "has not registered time 1")
                    elif dest_server == -1:
                        self.Database.insert_message(
                            data.user, recv_data['dest'], recv_data['time'], json.dumps(recv_data))
                        print("Entered the message for user ",
                                recv_data['dest'], "stored in database")
                        self.Database.displayallmessage()
                    elif dest_server == self.ID:
                        msg = recv_data
                        # data_send = types.SimpleNamespace(addr=data.addr, status = 'msg', response = 1,
                        #                              user = data.user, server_name = self.ID, message = '')
                        sock = self.client_sockets[recv_data['dest']]
                        key = self.selector.get_key(sock)
                        data_n = key.data
                        if data_n.message == '':
                            data_n.message = []
                        data_n.message.append(msg)
                        if data_n.response == 1:
                            ################################################### REQUIRES CLARIFICATION (WHAT TO "HANDLE LATER"?)#####################################################
                            # handle later
                            a = 1
                        data_n.status = 'rm'
                        print(data_n)
                        self.selector.modify(
                            sock, self.read | self.write, data=data_n)
                    elif dest_server > 0:
                        msg = recv_data
                        print("Destination server:",dest_server)
                        sock = self.server_sockets[dest_server]
                        key = self.server_selector.get_key(sock)
                        data_n = key.data
                        if data_n.message == '':
                            data_n.message = []
                        data_n.message.append(msg)
                        data_n.status = 'msg'
                        self.server_selector.modify(
                            sock, self.read | self.write, data=data_n)

        except Exception as e:
            print('Some exception occured', e)

    def service_connection(self, key, mask):
        """This function handles events that are only about receiving messages (or images) from clients or servers. There is a separate section to deal with messages that are about authentication

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket.
        mask : obj
            Contains information about the operation to be performed, whether it is to receive data or to send data
        """
        try:
            if key.data.status == 'auth':       # authenticate user
                self.authenticate_client(key, mask)
            elif key.data.status == 'msg' or key.data.status == 'img':
                self.message(key)
        except:
            return


S = Server(IP, PORT, ID, N)