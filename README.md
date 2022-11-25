# FastChat

__The actual chat application files are in ```Programs``` directory and performance analysis and testing code is in ```Testing``` directory.__

Team : AAA (Anand, Atharva and Adarsh)

This project has the following main domains:
* Client
* Server
  * Loadbalancing
  * Multi-Server Setting
* Encryption
* Databasing


Client has been implemented in ```client.py```, Server in ```Server.py``` and LoadBalancer in ```loadbalancer.py```. 
Two more files : ```enc.py``` has helper classes for encryption (E2EE) and ```database.py``` has a helper class for database queries and modification.  

<br>

The tech stack used is (libraries, softwares and stuff ... :)
* ```python```
  * ```socket``` and ```selectors``` for sockets handling
  * ```rsa``` and ```Crypto``` libraries for encryption
  * ```psycopg2``` for PostgreSQL
  * ```json```, ```threading```, ```json``` and ```datetime``` for other miscellaneous stuff
* PostgreSQL for databasing
* Bash scripting for testing 


<br>

## Running the Chat

1. Setup the database in PostgreSQL. In our code the database has been named ```fastchat```. 
2. Run the load-balancer as 
```
python loadbalancer.py <LOAD BALANCER PORT> <STARTING PORT OF SERVER> <NUMBER OF SERVERS>
```
3. Spawn the servers in the following format
```
python server.py <PORT> <SERVER ID> <TOTAL NUMBER OF SERVERS>
```
Also note that the ```PORT```s and Server ```ID```s are two arithmetic progressions with difference 1. And ```ID```s are in the range 1,...,N (total number of servers).
For example, if 1,2,3 are server ```ID```s, then $P,P+1,P+2$ are the port numbers.

4. Client runs as 
```
python client.py <PORT OF CLIENT> <PORT OD LOAD BALANCER>
```

<br>

## Testing Script

For testing and performance analysis we have the following files:

* ```spawn_servers.sh```
* ```super_script.py```
* ```perform.py```
<br>

1. ```spawn_servers.py``` : It initializes the servers and load balancers. NOTE : __This script works only if gnome terminal is present__
2. ```super_script.py``` : this python code is used for performance analysis. Using this program we can test the chat application's direct messaging for 
variable number of clients and variable number of messages. We can even test it for $N$ images provided we have $N$ distinct images. Note that these are in separate files (that is image testing and message testing have different python scripts with different names). __Please note that due to the lack of time we wrote a program where we will have to modify the values of parameters and comment/uncomment code__. This script generates log files for each client in a folder. Each line of log file has the format.
```
<MESSAGE>,<TIME>,<BYTES> 
```
3. ```perform.py``` : this script uses ```pandas``` library to process the log files. This program generates a graph of latency vs message number. This program also calculates Latency and Throughput. Using this for various runs, we can generate latency and throughput for various senarios and plot them. __Due to time constraints we did not write a program for plotting all graphs in one go and manually have to extract parameters over various runs. Also even__ ```perform.py``` __has various parameters (like folder names, numbers etc) that have to be adjusted manually (this is due to lack of time)__.





  
