#!/usr/bin/python
"""This file is a collection of functions to access and modify the postgreSQL database `fastchat`.

We have used the package psycopg2, which provides us a connector through which we are able to query, modify and change the database.
"""
import psycopg2

def list_to_postgre_array(lst):
    """Converts a Python list into a PostgreSQL array

    Parameters
    ----------
    lst : list
        Contains the list elements to be converted into a PostgreSQL array

    Returns
    -------
    str
        A PostgreSQL array in string format
    """
    arr_str = '{'
    for i in range(len(lst)):
        arr_str+=str(lst[i])+','
    arr_str = arr_str.rstrip(',')    
    arr_str+='}'
    return arr_str

def postgre_array_to_list(arr_str):
    """Converts a PostgreSQL array into a Python list

    Parameters
    ----------
    arr_str : str
        PostgreSQL array in string format

    Returns
    -------
    list
        List of elements in the PostgreSQL array
    """
    s = arr_str.strip('{')
    s = s.strip('}')
    lst = s.split(',')
    return lst

class CentralDatabase:
    """Class for the Central Database, to be accessed by all the servers
    """
    def __init__(self):
        """Initialising the Central Database, only accessible by the servers
        
        Creates 5 tables in the database, which serve the following functions: 
        
        messages : Table to store unread messages for direct chats
        users : Table to store the details of registered users
        groups : Table to store information about all the groups
        groupmessages : Table to store unread group messages
        numclients : Stores the number of clients which are connected to each server
        
        """

        self.conn = psycopg2.connect("dbname=fastchat user=atharvat") #Connector object to connect with the database
        cur = self.conn.cursor()
        cur.execute("DROP TABLE IF EXISTS messages;")
        cur.execute("DROP TABLE IF EXISTS users;")
        cur.execute("DROP TABLE IF EXISTS groups;")
        cur.execute("DROP TABLE IF EXISTS groupmessages;")
        cur.execute("DROP TABLE IF EXISTS numclients;")
        
        cur.execute('''CREATE TABLE IF NOT EXISTS messages
        (SENDER_ID    INT    NOT NULL,
        RECEIVER_ID   INT     NOT NULL,
        TIME          TEXT     NOT NULL,
        MESSAGE       TEXT     NOT NULL);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users
        (USER_ID    INT   PRIMARY KEY  NOT NULL,
        PASSWORD    TEXT  NOT NULL,
        SERVER_ID   INT   NOT NULL,
        PUBLIC_KEY  TEXT  NOT NULL);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS groups
        (GROUP_ID    SERIAL PRIMARY KEY,
        PARTICIPANTS INT ARRAY  NOT NULL,
        ADMIN_ID INT  NOT NULL);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS groupmessages
        (SENDER_ID  INT  NOT NULL,
        GROUP_ID    INT  NOT NULL,
        TIME        TEXT NOT NULL,
        MESSAGE     TEXT NOT NULL,
        RECEIVER_ID INT  NOT NULL);''')
        cur.execute('''CREATE TABLE IF NOT EXISTS numclients
        (SERVER_ID  INT PRIMARY KEY  NOT NULL,
        NUM_CLIENTS INT NOT NULL);''')
        # If not connected to any server, the server_id will be -1
        self.conn.commit()

    #Added key attribute, made password a string
    def insert_newuser(self, user_id, password, server_id, public_key):
        """Inserts a new user into the user table, if the user did not exist previously

        Parameters
        ----------
        user_id : int
            The user ID of the user to be inserted
        password : str
            The encrypted password of the user
        server_id : int
            The server ID of the server that the user is connected to
        public_key : str
            The public key of the user

        Returns
        -------
        bool
            `True` if the user wasn't already present, and `False` if it was already present
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT USER_ID FROM users;''')
        output = cur.fetchall()

        if ((user_id,) not in output):
            cur.execute('''INSERT INTO users (USER_ID, PASSWORD, SERVER_ID, PUBLIC_KEY)
            VALUES ({0},'{1}',{2},'{3}');'''.format(user_id, password, server_id, public_key))
            self.conn.commit()
            return True  # if succesfully inserted
        else:
            return False  # unsuccessful insertion
        
    def fetch_key(self, user_id):
        """Gets the public key of a given user

        Parameters
        ----------
        user_id : int
            Contains the user ID of the user

        Returns
        -------
        str
            Public Key of the user
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT PUBLIC_KEY FROM users WHERE USER_ID = {0};'''.format(user_id))
        key = cur.fetchall()
        return key[0][0]
    
    def fetch_group_keys(self, group_id, user_id):
        """Gets the public keys of all users in a group except the given user (Checks whether they're in the group or not)

        Parameters
        ----------
        group_id : int
            The group ID of the group
        user_id : int
            The user ID of the user to be excluded

        Returns
        -------
        `dict` or `int`
            A dictionary with keys being the user IDs and values being the public keys. 
            Returns -1 if the user isn't present in the group
        """
        cur = self.conn.cursor()
        participants = self.group_participants(group_id)
        if (user_id not in participants):
            return -1
        else:
            participants.remove(user_id)
        dict1 = dict()
        for id in participants:
            key = self.fetch_key(id)
            dict1[id] = key
            
        return dict1
        
    #Returns the group ID of the created group, -1 if a participant isn't registered
    def create_group(self, admin_id, participants):
        """Creates a group with an admin and participants 

        Parameters
        ----------
        admin_id : int
            The admin user ID
        participants : :obj:`list` of :obj:`int`
            The list of participants to be added in the group

        Returns
        -------
        int
            Returns the ID of the group created, -1 if a participant in the list isn't registered
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT USER_ID FROM users''')
        a = cur.fetchall()
        for i in range(len(participants)):
            tup = (participants[i],)
            if tup not in a:
                return -1
        arr_str = list_to_postgre_array(participants)
        cur.execute('''INSERT INTO groups (PARTICIPANTS, ADMIN_ID)
        VALUES ('{0}',{1});'''.format(arr_str,admin_id))
        self.conn.commit()
        cur.execute('''SELECT GROUP_ID FROM groups ORDER BY GROUP_ID;''')
        lst_ids = cur.fetchall()
        return lst_ids[-1][0]
    
    def group_participants(self, group_id):
        """Gets all the participants of a group

        Parameters
        ----------
        group_id : int
            The group ID of the group

        Returns
        -------
        :obj:`list` of :obj:`int`
            List of participant IDs in the group
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT PARTICIPANTS FROM groups WHERE GROUP_ID = {0}'''.format(group_id))
        lst = cur.fetchall()[0][0]
        return lst
        

    def change_server(self, user_id, server_id):
        """Change the server of the user in the users table

        Parameters
        ----------
        user_id : int
            The user ID of the user
        server_id : int
            The server ID to be updated to
        """
        cur = self.conn.cursor()
        cur.execute('''UPDATE users
                        SET SERVER_ID = {1}
                        WHERE USER_ID = {0};
                        '''.format(user_id, server_id))
        self.conn.commit()

    def check_server(self, user_id):
        """_summary_

        Parameters
        ----------
        user_id : int
            The user ID of the user

        Returns
        -------
        int
            The server that the user is conencted to, -1 if offline and -2 if not registered
        """
        cur = self.conn.cursor()
        cur.execute(
            '''SELECT SERVER_ID FROM users WHERE USER_ID = {0};'''.format(user_id))
        a = cur.fetchall()
        print("Servers : ", a)
        if (a == []):
            return -2  # -2 is returned if the user has not been registered yet
        return a[0][0]

    #Users table got modified, so output would have an extra key
    def displayallusers(self):
        """Prints the details of all users
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM users;''')
        output = cur.fetchall()
        print(output)

    def check_user(self, user_id):
        """Checks whether a user is registered or not

        Parameters
        ----------
        user_id : int
            The user ID of the user

        Returns
        -------
        bool
            `True` if the user is registered and `False` if not
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT USER_ID FROM users 
        WHERE USER_ID = '''+str(user_id)+''';''')
        output = cur.fetchall()
        print("Check Server Function's output : ", output)
        if ((user_id,) in output):
            return True  # user is present in the database
        else:
            return False  # user id is not present in the database

    #Password got updated to a string
    def check_cred(self, user_id, password):
        """Checks whether the credentials supplied by the user are correct

        Parameters
        ----------
        user_id : int
            The user ID of the user
        password : str
            The password (encrypted) of the user

        Returns
        -------
        bool
            `True` if the credentials are valid and `False` if the credentials aren't
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT USER_ID FROM users 
        WHERE USER_ID = '''+str(user_id)+''' AND PASSWORD = '{0}' '''.format(password)+''';''')
        output = cur.fetchall()

        if ((user_id,) in output):
            return True  # user is present in the database
        else:
            return False  # user id is not present in the database

    #Adding key into the record in the database
    # The message is now a json message
    def insert_message(self, sender_id, receiver_id, datetime, message):
        """Inserts a direct message into the message database, only when the receiver is offline

        Parameters
        ----------
        sender_id : int
            The user ID of the sender
        receiver_id : int
            The receiver ID of the user
        datetime : str
            The datetime string of the message
        message : _type_
            The direct text message to be sent

        Returns
        -------
        bool
            `True` if the receiver is registered and `False` if not
        """
        cur = self.conn.cursor()
        #### ADD CODE TO CHECK WHETHER RECEIVER IS IN THE DATABASE #####
        if (self.check_user(receiver_id)):
            cur.execute('''INSERT INTO messages (SENDER_ID,RECEIVER_ID,TIME,MESSAGE)
            VALUES ({0},{1},'{2}','{3}');'''.format(sender_id, receiver_id, datetime, message))
            self.conn.commit()
            return True
        else:
            return False

    #Displays an extra key column as well
    # Message is now a json
    def displayallmessage(self):
        """Displays all the messages stored in the tables messages
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM messages;''')
        output = cur.fetchall()
        print(output)
      
    # Changed groupmessages to contain a single receiver_id instead of an array of unread participants 
    # message to be inserted is now a json
    # def check_group_message(self, sender_id, receiver_id, datetime, group_id, message, key):
    #     cur = self.conn.cursor()
    #     cur.execute('''SELECT * FROM groupmessages WHERE SENDER_ID = {0} AND TIME = '{1}' AND GROUP_ID = {2} AND MESSAGE = '{3}' AND RECEIVER_ID = {4} AND KEY = '{5}';'''.format(sender_id, datetime, group_id, message, receiver_id, key))
    #     a = cur.fetchall()
    #     if (len(a) == 0):
    #         return False
    #     else:
    #         return True
    
    # Adding key column to record, removing participants column
    # message is a json message
    def insert_group_message(self, sender_id, receiver_id, datetime, group_id, message):
        """Inserts an group message into the groupmessage table, only when unread by a receiver

        Parameters
        ----------
        sender_id : int
            The user ID of the sender
        receiver_id : int
            The user ID of the receiver who is offline
        datetime : str
            The datetime string of the message
        group_id : int
            The user ID of the sender
        message : str
            The unread group message to the offline receiver

        Returns
        -------
        bool
            `True` if inserting works and `False` otherwise
        """
        cur = self.conn.cursor()
        #### ADD CODE TO CHECK WHETHER RECEIVER IS IN THE DATABASE #####
        print("Inserting {0} into groupmessages table".format(message))
        cur.execute('''INSERT INTO groupmessages (SENDER_ID,GROUP_ID,TIME,MESSAGE,RECEIVER_ID)
        VALUES ({0},{1},'{2}','{3}',{4});'''.format(sender_id, group_id, datetime, message, receiver_id))
        self.conn.commit()
        return True
        
    # Displays receiver_id and not participants array
    # message is a json message
    def displayallgroupmessage(self):
        """Print all the unread group messages
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM groupmessages;''')
        output = cur.fetchall()
        print(output)

    # Will show the key as well, the output will contain the key
    # Messages will be json
    # output is of the form of a list of tuples of the form (sender_id, receiver_id, time, json_message, key)
    def show_message(self, receiver_id):
        """Returns the unread messages from the messages table, with the given receiver ID. Also deletes those messages from the table

        Parameters
        ----------
        receiver_id : int
            The user ID of the receiver who is offline

        Returns
        -------
        :obj:`list` of :obj:`tup`
            Returns the row of the database with the correct receiver ID
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM messages 
        WHERE RECEIVER_ID = '''+str(receiver_id)+''';''')
        output = cur.fetchall()
        # Delete the message only after confirmation that the messages have been delivered
        cur.execute('''DELETE from messages
        WHERE RECEIVER_ID = '''+str(receiver_id)+''';''')
        self.conn.commit()
        # Return all the messages to be shown to the user
        return (output)
    
    # Will not display participants, instead an additional key and receiver_id
    # Will display json messages
    def show_group_message(self, receiver_id):
        """Returns the unread group messages from the groupmessages table, with the given receiver ID. Also deletes those messages from the table

        Parameters
        ----------
        receiver_id : int
            The user ID of the receiver who is offline

        Returns
        -------
        :obj:`list` of :obj:`tup`
            Returns the row of the database with the correct receiver ID
        """
        cur = self.conn.cursor()
        print("I'm inside show_group_message, querying")
        cur.execute('''SELECT * FROM groupmessages 
        WHERE RECEIVER_ID = {0};'''.format(int(receiver_id)))
        output = cur.fetchall()
        # Delete the message only after confirmation that the messages have been delivered
        print("I'm deleting from show_group_message")
        cur.execute('''DELETE from groupmessages
        WHERE RECEIVER_ID = '''+str(receiver_id)+''';''')
        self.conn.commit()
        # Return all the messages to be shown to the user
        return (output)

    # def return_min_conn(self, num_servers):
    #     cur = self.conn.cursor()
    #     cur.execute('''SELECT server_id FROM users
    #         GROUP BY server_id
    #         ORDER BY COUNT(server_id);''')
    #     a = cur.fetchall()
    #     if (len(a) < num_servers):
    #         for i in range(1,num_servers+1):
    #             tup = (i,)
    #             if tup not in a:
    #                 return i
    #     else:
    #         return a[0][0]
    #     return a

    #server_pool contains the (server_ip, server_port) of all the servers
    def init_numclients(self, num_servers): 
        """Initializes the table numclients which maintains the tally of number of clients per server vs the corresponding ip and port number. Sets all values to 0

        Parameters
        ----------
        num_servers : int
            The number of servers running

        Returns
        -------
        bool
            `True` if it initialises correctly, else `False`
        """
        cur = self.conn.cursor()
        try:
            for i in range(num_servers):
                cur.execute('''INSERT INTO numclients (SERVER_ID, NUM_CLIENTS)
                    VALUES ({0},{1});'''.format(i+1, 0))
                print("In insert numclients")
                self.conn.commit()
            return True
        except Exception as e:
            print("ERROR INITIALIZING THE NUMCLIENTS TABLE!!", e)
            return False
        
    # increase = 1 if client joins the server, -1 if the client leavs the server
    def update_numclients(self, server_ID, increase): 
        """Updates the table numclients when user comes online or goes offline

        Parameters
        ----------
        server_ID : int
            ID of the server to be updated
        increase : int
            Either +1 or -1 depending on whether a user is going offline or coming online

        Returns
        -------
        bool
            `True` if there is no error, else `False` if the server itself isn't in the table to begin with
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT SERVER_ID FROM numclients;''')
        output = cur.fetchall()
        if (server_ID,) not in output:
            return False
        else:
            try:
                cur.execute('''UPDATE numclients
                SET NUM_CLIENTS = NUM_CLIENTS + {0}
                WHERE SERVER_ID = {1};'''.format(increase, server_ID))
                self.conn.commit()
                print("TABLE UPDATED!!!!!!!!!!!!!!!!!!!!!!!!!")
                return True
            except:
                print("Error occured in the updation of database!!")
                return False


    def get_min_numclients(self):
        """Selects the server with the least number of clients connected to it

        Returns
        -------
        int
            Server ID of the required server
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT SERVER_ID FROM numclients
             ORDER BY NUM_CLIENTS;''')
        a = cur.fetchall()
        return a[0][0]

    
    def del_participant(self, part_id, admin_id, group_id):
        # Deletes the participant from the group iff he is not an the admin of the group
        # Should handle the case of part_id == admin_id before this function call, will be easier
        # Returns 1 if everything is normal
        # Returns -1 if the user isn't an admin of the group specified
        # Returns -2 if the participant isn't in the group 
        # Returns -3 if the group ID does not exist
        # ANAND
        """Deletes a participant from a group, on the admin's request

        Parameters
        ----------
        part_id : int
            The ID of the participant to be removed
        admin_id : int
            The ID of the person trying to remove the participant
        group_id : _type_
            The group from which the participant is to be removed

        Returns
        -------
        int
            -1, if the person trying to remove a participant is not the admin of the group
            -2, if the person to be removed isn't part of the group
            -3, if the group doesn't exist
            1, otherwise
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT admin_id, participants FROM groups WHERE group_id = {0}'''.format(group_id))
        a = cur.fetchall()
        if (len(a) == 0):
            return -3
        actual_admin_id = a[0][0]
        if (actual_admin_id != admin_id):
            return -1
        if part_id not in a[0][1]:
            return -2
        cur.execute('''UPDATE groups
                    SET PARTICIPANTS = array_remove(PARTICIPANTS,{0})
                    WHERE group_id = {1};'''.format(part_id, group_id))
        self.conn.commit()
        return 1

    def add_participant(self, part_id, admin_id, group_id):
        # Adds the participant to the group iff he is not present in the group
        # Returns 1 if everything is normal
        # Returns -1 if the user isn't an admin of the group specified
        # Returns -2 if the participant is in the group 
        # Returns -3 if the group ID does not exist
        # Returns -4 if the user ID does not exist
        # ANAND
        """Adds a participant from a group, on the admin's request

        Parameters
        ----------
        part_id : int
            The ID of the participant to be added
        admin_id : int
            The ID of the person trying to add the participant
        group_id : _type_
            The group to which the participant is to be added

        Returns
        -------
        int
            -1, if the person trying to add a participant is not the admin of the group
            -2, if the person to be added isn't part of the group
            -3, if the group doesn't exist
            -4, if the user to be added doesn't exist
            1, otherwise
        """
        cur = self.conn.cursor()
        cur.execute('''SELECT admin_id, participants FROM groups WHERE group_id = {0}'''.format(group_id))
        a = cur.fetchall()
        if (len(a) == 0):
            return -3
        actual_admin_id = a[0][0]
        if (actual_admin_id != admin_id):
            return -1
        if part_id in a[0][1]:
            return -2
        cur.execute('''SELECT user_id FROM users WHERE user_id = {0}'''.format(part_id))
        a = cur.fetchall()
        if (len(a) == 0):
            return -4
        cur.execute('''UPDATE groups
                    SET participants = participants || '{0}' 
                    WHERE group_id = {1};'''.format(list_to_postgre_array([part_id]),group_id))
        self.conn.commit()
        return 1

    def close_connection(self):
        """Closes the connection between the python script and the postgreSQL database
        """
        self.conn.close()
        print("Connection closed")

# D = CentralDatabase()
# #
# print(D.insert_newuser(2, 2))
# print(D.insert_newuser(1, 1))
# print(D.check_user(3))
# print(D.check_cred(2,2))
# output = D.displayallusers()
# print(output)

# D.insert_message(1,2,"31122022","Hello How are you?")
# D.displayallmessage()
# output = D.show_message(2)
# print(output)
# D.displayallmessage()
# #
# #
# D.displayallmessage()
# D.displayallusers()
# D.close_connection()
