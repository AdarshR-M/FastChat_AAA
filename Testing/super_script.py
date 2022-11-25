import pexpect
import time
import random
import sys
import numpy as np
from numpy.random import default_rng

rng = default_rng(3)

# Run the script as "python3 super_script.py <NUM_CLIENTS> <NUM_MESSAAGES>"
NUM_CLIENTS =  int(sys.argv[1])# Can vary the number of clients in each run
IMG_FILE_1 = 'corgi.png' # 1 kB image used for testing
NUM_MSGS = int(sys.argv[2]) # Can vary the number of random messages in each run
ALGORITHM = int(sys.argv[3])

clients = [None] * NUM_CLIENTS

####################################################################################################################
#ALGORITHM = 1 # Delay between messages is constant
# ALGORITHM = 2 # Delay between messages is sampled from exponential distribution
# ALGORITHM = 3 # Delay between messages is sampled from Gaussian Distribution
####################################################################################################################


for i in range(NUM_CLIENTS):
    clients[i] = pexpect.spawn("python3 client.py {0} 9000".format(2000 + i))
    clients[i].expect("Option :.*")  # End of echoed command
    print(clients[i].before.decode())
    print("----------------------------------------------------------------------")
time.sleep(0.1)

# Registering all clients
for i in range(NUM_CLIENTS):
    clients[i].sendline('2')
    clients[i].sendline(str(i+1)) # username
    clients[i].sendline(str(i+1)) # password
time.sleep(5/8*NUM_CLIENTS)
# Randomly sending messages between all the clients
lst = [i for i in range(NUM_CLIENTS)]
if ALGORITHM == 1:
    delay = [0.01] * NUM_CLIENTS
elif ALGORITHM == 2:
    delay = rng.exponential(0.012, NUM_CLIENTS)
elif ALGORITHM == 3:
    delay = abs(rng.normal(0.01,0.1, NUM_CLIENTS))

for i in range(NUM_MSGS):
    a = random.sample(lst,2)
    sender = a[0]
    receiver = a[1]
    clients[sender].sendline('1')
    clients[sender].sendline(str(receiver+1))
    clients[sender].sendline("{0}".format(i+1))
    time.sleep(delay[i])
    clients[sender].sendline('0')
    print("Message sent from user {0} to user {1}".format(sender+1, receiver+1))
time.sleep(5/8*NUM_CLIENTS)
print("After the messages")
# Closing all the users

for i in range(NUM_CLIENTS):
    # clients[i].expect("0. Exit")
    clients[i].sendline("0")
    time.sleep(1)
    done = True
print("Hi")

time.sleep(10)

print("Bye")

