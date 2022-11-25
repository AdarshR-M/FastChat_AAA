#!/bin/bash
# Run the script as ./spawn_servers.sh <LOADBALANCER PORT> <INITIAL_PORT> <NUMBER OF SERVERS> <NUMBER OF CLIENTS>
gnome-terminal -- sh -c "bash -c \"python3 loadbalancer.py $1 $2 $3; exec bash\""
sleep 1
b=1
for (( c=$2; c<$2+$3; c++ ))
do 
    gnome-terminal -- sh -c "bash -c \"python3 server.py $c $b $3; exec bash\""
    b=$((b+1))
    # xterm -e "python3 server.py $c" &
done

