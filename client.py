import numpy as np
import pickle as pk
import time
import zmq 
import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
import os
import shutil



def simulator_sensors(size, sleep_time = 1):

    while(True):
        temperature = np.random.uniform(10, 40, size)  # Simulated temperature in Celsius
        humidity = np.random.uniform(20, 70, size)     # Simulated humidity in relative humidity
        wind = np.random.uniform(10, 150, size)     # Simulated wind speed in km/h
        pressure = np.random.uniform(80, 150, size) # Simulated pressure in Pa
        yield np.array([temperature, humidity, wind, pressure]).T
        time.sleep(sleep_time)




# sends sensor data to server and make sure that they are recieved by the server

def sender_thread(size, sleep_time):

    shutil.rmtree('plots', ignore_errors= True)
    os.makedirs("plots")

    HOST = "34.107.5.115"  # The server's IP address
    PORT_1 = 4000 # The port used by the server
    TIMEOUT = 10 # Time out in seconds before a messeage is retransmitted

    buffer_max_size = 100
    buffer = []
    acks = []
    context = zmq.Context()
    send_socket = context.socket(zmq.DEALER)
    send_socket.connect("tcp://{}:{}".format(HOST, PORT_1))
    poll = zmq.Poller()
    poll.register(send_socket, zmq.POLLIN)

    counter = 0



    for data in simulator_sensors(size, sleep_time):

        data_preprocessed = (data - data.mean(axis = 0))/data.std(axis = 0)
        full_data = {"id": counter , "data" : data_preprocessed}
        full_data_b = pk.dumps(full_data)
        buffer.append({"id": counter, "data":full_data_b})
        acks.append({"id" : counter, "time": time.time() })
        if len(buffer) > buffer_max_size:
            buffer.pop(0)
            acks.pop(0)
        

        send_socket.send(full_data_b)
        print(f'send data of id {counter}')
        counter = (counter +1) % buffer_max_size


        # checks notification from server
        sockets = dict(poll.poll(1000))
        if send_socket in sockets:
            if sockets[send_socket] == zmq.POLLIN:
                obj_b = send_socket.recv()
                obj = pk.loads(obj_b)

                if "ack" in obj:
                    print(f'got ack of id {obj["ack"]}')
                    acks = [ack for ack in acks if ack["id"] != obj["ack"]]
                    buffer = [elem for elem in buffer if elem["id"] != obj["ack"]]

                elif "result" in obj:
                    print(f'got result of id {obj["id"]}')
                    send_socket.send(pk.dumps({"ack" : obj["id"]}))

                    fig, ax = plt.subplots()

                    ax.scatter(*obj["result"].T, c = "red")
                    ax.set_title("Dimentionality reduction using PCA", fontsize = 17)

                    ax.set_xlabel(f'{obj["pca"][0][0]:.2f}*temperature + {obj["pca"][0][1]:.2f}*humidity + {obj["pca"][0][2]:.2f}*wind + {obj["pca"][0][3]:.2f}*pressure', fontsize = 10)
                    ax.set_ylabel(f'{obj["pca"][1][0]:.2f}*temperature + {obj["pca"][1][1]:.2f}*humidity + {obj["pca"][1][2]:.2f}*wind + {obj["pca"][1][3]:.2f}*pressure', fontsize = 10)
                    ax.grid()
                    fig.savefig(f'plots/plot_{obj["id"]}.png')


        if len(acks):

            if  time.time() - acks[0]["time"]   > TIMEOUT:
                print(f'send data of id {buffer[0]["id"]}')
                send_socket.send(buffer[0]["data"])





sender_thread(size = 50, sleep_time = 3)
