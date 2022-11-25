"""This file is the code for the load balancer, where clients first connect to. The load balancer has two algorithms, one being a simple round robin method to choose between servers and the other being a method that finds out the load of each server, by checking the number of connections to each server and sending the client to the one with the least number.

Attributes
----------
L_IP : str
    The IP address of the load balancer

L_PORT : int
    The port of the load balancer
    
START_PORT : int
    The starting port of all the servers, the servers will be connected to consecutive ports starting from the `START_PORT`
    
NUM_SERVERS : str
    The total number of servers running
    
SERVER_POOL : list
    A list of tuples containing the IP address and the PORTS of all the servers
    
ITER : cycle
    A cycle of the `SERVER_POOL` list
    
MAX_SIZE : int
    The max size limit for the message

"""

import sys
import socket
import selectors
import types
import json
import random
from itertools import cycle
import select
from database import *
from enc import Encrypt

MAX_SIZE = 1048576

'''PORT OF THE STARTING SERVER IS 8010
THERE ARE 5 servers : PORTS numbers are - 8010, 8011, 8012, 8013, 8014
PORT NUMBER OF THE LOADBALANCER IS 9000'''

'''Run the loadbalancer as: python3 loadbalancer.py <LOABALANCER_PORT> <PORT OF THE STARTING SERVER> <NUMBER OF SERVERS>'''
L_PORT  = int(sys.argv[1])
START_PORT = int(sys.argv[2])
NUM_SERVERS = int(sys.argv[3])
L_IP = 'localhost'
SERVER_POOL = []
for i in range(NUM_SERVERS):
    SERVER_POOL.append((L_IP, START_PORT+i))

# Iterator of the IP address and Port number of the servers
ITER = cycle(SERVER_POOL)
    

class loadbalancer(object):
    """This class is for the load balancer, and specifies the connections between the load balancer and the servers, the load balancing strategy and accepting and sending messages to the clients
    """
    
    def __init__(self, IP, PORT,algorithm):
        """Initialises the load balancer object and it's attributes

        Parameters
        ----------
        IP : str
            The IP address of the load balancer
        PORT : int
            The port of the load balancer
        algorithm : str
            Specifies the algorithm to be used while assigning servers to clients
        """
        self.IP = IP
        self.PORT = PORT
        # Number of servers to which the service has to be routed
        self.num_servers = NUM_SERVERS
        # Client server map not needed - the loadbalancer will route message to the appropriate server
        
        # To store the list of client sockets that have registered (which is equivalent to saying that the client has connected at least once with the load balancer)
        # and the corresponding loadbalancer side sockets for client sockets
        self.sockets = list()
        # To store the number of connections of the servers connected to the loadbalancer - maybe??
        self.num_connections = list()
        self.flow_table = dict() # To create one-one correspondence between the client socket and the corresponding loadbalancer side socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client_socket.setblocking(False)
        self.client_socket.bind((self.IP, self.PORT))
        self.client_socket.listen()
        self.sockets.append(self.client_socket)

        # Initializes the algorithm it uses to handle client requests
        self.algorithm = algorithm
        self.encrypt = Encrypt()
        self.encrypt.save_keys('server_keys')

        self.Database = CentralDatabase()

        # Initializing the numclients table for tallying the number of clients connected to the respective servers
        # self.Database.init_numclients(NUM_SERVERS)
        
    def handle(self):
        """This function handles the events regarding the load balancer through a selector, by handling the read and write events separately
        """
        while True:
            read_list, write_list, exception_list = select.select(self.sockets, [], [])
            for sock in read_list:
                # new connection
                if sock == self.client_socket:
                    self.accept_connection()
                    break
                
          
    def accept_connection(self):
        """This function accepts a connection from a client and then forwards it to a particular server (based on the algorithm) with a sign, to verify that it was in fact the load balancer that sent him to that server
        """
        client_socket, client_addr = self.client_socket.accept()
        print ("client connected: %s <==> %s" % (client_addr, self.client_socket.getsockname()))

        # select a server that forwards packets to
        server_ip, server_port = self.select_server(SERVER_POOL, self.algorithm)
        if server_ip == 'localhost':
            server_ip = '127.0.0.1'
        
        try:
            sign = self.encrypt.RSA_sign(server_ip+str(server_port))
            msg = {'server_ip': server_ip, 'server_port': server_port, 'sign' : sign.decode()}
            print("Server port and address sent to client: ", client_addr)
            msg = json.dumps(msg)
            client_socket.send(msg.encode())
            self.close_conn(client_socket)
        except:
            print("Exception occured....closing socket")
            self.close_conn(client_socket)

    def close_conn(self, sock):
        """This function closes the connection from the load balancer between the load balancer and the client

        Parameters
        ----------
        key : obj
            Contains information about the socket between the client and the server, and also the data that will be communicated through that socket
        """
        print ('client %s has disconnected' % (sock.getpeername(),))
        print ('='*41+'flow end'+'='*40)
        sock.close()  # close connection with client

    def select_server(self, server_list, algorithm):
        """This determines which algorithm to use in order to select the server for the client to go to.

        Parameters
        ----------
        server_list : list
            The list of servers that are running
        algorithm : str
            A string with the algorithm name

        Returns
        -------
        tuple
            Returns a tuple of IP, PORT for the server to connect to

        Raises
        ------
        Exception
            When the algorithm is not recognised by the load balancer
        """
        if algorithm == 'random':
            return random.choice(server_list)
        elif algorithm == 'round robin':
            return self.round_robin(ITER)
        elif algorithm == 'minimum connect':
            return self.min_conn()
        else:
            raise Exception('Loadbalancer does not know the algorithm: %s' % algorithm)

    
    # Function to return the next server's IP address and the port number
    def round_robin(self, iter):
        """Picks the next server in the cycle of servers

        Parameters
        ----------
        iter : iterable
            The last tuple that had gotten assigned

        Returns
        -------
        tuple
            Returns a tuple of IP, PORT for the server to connect to, in this case, it is the next in the cycle of servers
        """
        # round_robin([A, B, C, D]) --> A B C D A B C D A B C D ...
        return next(iter)

    # Function to return the IP address and port number of next server
    def min_conn(self):
        """Queries the database for the server with the least number of connections

        Returns
        -------
        tuple
            Returns a tuple of IP, PORT for the server to connect to, in this case, it is the one with the least number of connections
        """
        server_id = self.Database.get_min_numclients()
        for i in range(len(SERVER_POOL)):
            if (SERVER_POOL[i][1] == server_id + START_PORT - 1):
                return SERVER_POOL[i]
        return SERVER_POOL[0]


if __name__ == '__main__':
    try:
        L = loadbalancer('localhost', L_PORT, 'minimum connect') # Making an object of the loadbalancer to run it
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        print(next(ITER))
        L.handle()
    except KeyboardInterrupt:
        print ("Ctrl C - Stopping load_balancer")
        sys.exit(1)