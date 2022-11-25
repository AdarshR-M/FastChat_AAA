from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt

no_of_messages = 100        # Number of messages that have been sent
N = 15                      # Number of clients

root = '20_100_refined_1/'  # Relative path of the directory that contains the log files

L = []
for i in range(1, N+1):
    try:
        filename = root + 'client'+str(i)+'_log_dm.txt'
        df = pd.read_csv(filename, index_col=None, header = None)
        L.append(df)
    except:
        continue
    
frame = pd.concat(L, axis=0, ignore_index=True)
frame = frame.sort_values(0)
print(frame)

frame[1] = frame[1].apply(lambda x : datetime.strptime(x, '%H:%M:%S.%f'))

frame[1] = frame[1].apply(lambda x : x.time())

list_id = list(frame[0])
list_time = list(frame[1])
list_bytes = list(frame[2])

max_bytes = max(list_bytes)
min_bytes = min(list_bytes)
avg_bytes = (max_bytes + min_bytes)/2


final_lst = []
for i in range(len(list_id)):
    if (i+1 < len(list_id) and list_id[i] == list_id[i+1]):
        final_id = list_id[i]
        time_diff = (datetime.combine(date.today(), list_time[i+1]) - datetime.combine(date.today(), list_time[i])).total_seconds()*1000
        if time_diff < 0 :
            time_diff = -1*time_diff
        final_bytes = max(list_bytes[i],list_bytes[i+1])
        tup = (final_id, time_diff, final_bytes)
        final_lst.append(tup)
        
print(final_lst)
print(len(final_lst))



max_time_send = list_time[0]
min_time_send = list_time[0]
max_time_recv = list_time[0]
min_time_recv = list_time[0]
total_bytes = 0

for i in range(len(list_id)):
    if (i+1 < len(list_id) and list_id[i] == list_id[i+1]):
        if (list_bytes[i] > avg_bytes):
            max_time_send = list_time[i]
            min_time_send = list_time[i]
            max_time_recv = list_time[i+1]
            min_time_recv = list_time[i+1]
            break
        else:
            max_time_send = list_time[i+1]
            min_time_send = list_time[i+1]
            max_time_recv = list_time[i]
            min_time_recv = list_time[i]
            break
            

for i in range(len(list_id)):
    if (i+1 < len(list_id) and list_id[i] == list_id[i+1]):
        if (list_bytes[i] > avg_bytes):
            max_time_send = max(max_time_send, list_time[i])
            min_time_send = min(min_time_send, list_time[i])
            max_time_recv = max(max_time_recv, list_time[i+1])
            min_time_recv = min(min_time_recv, list_time[i+1])
            total_bytes+=list_bytes[i]
        if (list_bytes[i] < avg_bytes):
            max_time_send = max(max_time_send, list_time[i+1])
            min_time_send = min(min_time_send, list_time[i+1])
            max_time_recv = max(max_time_recv, list_time[i])
            min_time_recv = min(min_time_recv, list_time[i])
            total_bytes+=list_bytes[i+1]
print(max_time_recv, max_time_send, min_time_recv, min_time_send, total_bytes)
             
latency = sum(elt[1] for elt in final_lst)/len(final_lst)

input_time = (datetime.combine(date.today(), max_time_recv) - datetime.combine(date.today(), min_time_recv)).total_seconds()/1000
out_time = (datetime.combine(date.today(), max_time_send) - datetime.combine(date.today(), min_time_send)).total_seconds()/1000


print('in time', input_time)
print('out time', out_time)

input_throughput = no_of_messages*max_bytes/(1000000*input_time)
output_throughput = len(final_lst)*max_bytes/(1000000*input_time)

print('Input Throughput', input_throughput)
print('Output Throughput', output_throughput)

print('Latency',latency)

Latency_List = []
Message_Number = []

for x in final_lst:
    Message_Number.append(x[0])
    Latency_List.append(x[1])
    
plt.figure(figsize=(20,15))
plt.plot(Message_Number,Latency_List, linewidth=3.0)
plt.xlabel('Message Number', fontsize = 24)
plt.ylabel('Latency (ms)', fontsize = 24)
plt.title('Latency vs Message Number for 100 messages, 20 clients, 5 servers, 10 ms', fontsize = 28)
plt.xticks(fontsize=24)
plt.yticks(fontsize=24)
plt.savefig('100_20_5_10.png')

    
    
         

