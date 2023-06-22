import numpy as np
import pickle as pk
import time
import zmq 
import numpy as np
import os
import shutil

# parameters
HOST = "34.107.5.115"  # The server's IP address
PORT = 4000 # The port used by the server
TIMEOUT = 10 # Time out in seconds before a messeage is retransmitted
buffer_max_size = 100 # maximum buffer size to store messages that not yet received by other components
size = 50 # size of the sent data (sensor data)
sleep_time = 3 # sleep time of the client before generating the next sensor data

# buffer to store sent messages in case of retransmission
buffer = []
# store the awaited id of the acknowledgments
acks = []

def simulator_sensors(size, sleep_time = 1):
    """
    generates sensor data indefinatley

    :size: size of the sensor data
    :sleep_time: sleep time before generating the next sensor data

    """ 
    while(True):
        temperature = np.random.uniform(10, 40, size)  # Simulated temperature in Celsius
        humidity = np.random.uniform(20, 70, size)     # Simulated humidity in relative humidity
        wind = np.random.uniform(10, 150, size)     # Simulated wind speed in km/h
        pressure = np.random.uniform(80, 150, size) # Simulated pressure in Pa
        yield np.array([temperature, humidity, wind, pressure]).T
        time.sleep(sleep_time)




# recreate folder to store plots
shutil.rmtree('plots', ignore_errors= True)
os.makedirs("plots")



context = zmq.Context()
send_socket = context.socket(zmq.DEALER)
send_socket.connect("tcp://{}:{}".format(HOST, PORT))
poll = zmq.Poller()
poll.register(send_socket, zmq.POLLIN)

counter = 0



for data in simulator_sensors(size, sleep_time):

    #  preprocess data
    data_preprocessed = (data - data.mean(axis = 0))/data.std(axis = 0)
    full_data = {"id": counter , "data" : data_preprocessed}
    full_data_b = pk.dumps(full_data)
    buffer.append({"id": counter, "data":full_data_b})
    acks.append({"id" : counter, "time": time.time() })

    # overwrite buffer if reached its maximum size
    if len(buffer) > buffer_max_size:
        buffer.pop(0)
        acks.pop(0)


    # sent data with its id to server
    send_socket.send(full_data_b)
    print(f'send data of id {counter}')
    counter = (counter +1) % buffer_max_size


    # polls to check received messages
    sockets = dict(poll.poll(1000))
    if send_socket in sockets:
        if sockets[send_socket] == zmq.POLLIN:
            obj_b = send_socket.recv()
            obj = pk.loads(obj_b)

            # server sent ack to state they received data.
            if "ack" in obj:
                print(f'got ack of id {obj["ack"]}')

                # delete data from buffer because server already received it
                acks = [ack for ack in acks if ack["id"] != obj["ack"]]
                buffer = [elem for elem in buffer if elem["id"] != obj["ack"]]

            # server sent result
            elif "result" in obj:
                print(f'got result of id {obj["id"]}')
                # sent ack to server
                send_socket.send(pk.dumps({"ack" : obj["id"]}))

                # plots result and save it
                fig, ax = plt.subplots()

                ax.scatter(*obj["result"].T, c = "red")
                ax.set_title("Dimentionality reduction using PCA", fontsize = 17)

                ax.set_xlabel(f'{obj["pca"][0][0]:.2f}*temperature + {obj["pca"][0][1]:.2f}*humidity + {obj["pca"][0][2]:.2f}*wind + {obj["pca"][0][3]:.2f}*pressure', fontsize = 10)
                ax.set_ylabel(f'{obj["pca"][1][0]:.2f}*temperature + {obj["pca"][1][1]:.2f}*humidity + {obj["pca"][1][2]:.2f}*wind + {obj["pca"][1][3]:.2f}*pressure', fontsize = 10)
                ax.grid()
                fig.savefig(f'plots/plot_{obj["id"]}.png')


    # check for time out of the latest message and retranssmit if necessary             
    if len(acks):
        if  time.time() - acks[0]["time"]   > TIMEOUT:
            print(f'send data of id {buffer[0]["id"]}')
            send_socket.send(buffer[0]["data"])



