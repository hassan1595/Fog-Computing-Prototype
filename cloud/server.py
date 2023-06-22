import pickle as pk
import time
import zmq
import numpy as np
import scipy.linalg as la
import matplotlib.pyplot as plt
import os
import shutil
from lib.pca import PCA




# parameters
buffer_max_size = 100
TIMEOUT = 10
HOST = "0.0.0.0" # accepts connections from all clients
PORT_1 = 4000  # The port used by the server


context = zmq.Context()
recv_socket = context.socket(zmq.ROUTER)
recv_socket.bind("tcp://{}:{}".format(HOST, PORT_1))
poll = zmq.Poller()
poll.register(recv_socket, zmq.POLLIN)
buffer = []
acks = []


while True:
    
    sockets = dict(poll.poll(1000))
    if recv_socket in sockets:
        if sockets[recv_socket] == zmq.POLLIN:
            _id = recv_socket.recv()
            obj_b = recv_socket.recv()
            obj = pk.loads(obj_b)

            if "data" in obj:
                ack_obj_b = pk.dumps({"ack" : obj["id"]})
                recv_socket.send(_id, zmq.SNDMORE)
                recv_socket.send(ack_obj_b)



                pca = PCA(obj["data"])
                result = pca.project(obj["data"],2)
                result_b = pk.dumps({"id": obj["id"], "result": result, "pca": pca.U[:,:2].T})

                buffer.append({"id" : obj["id"], "result": result_b})
                acks.append({"id" : obj["id"], "time": time.time()})


                recv_socket.send(_id, zmq.SNDMORE)
                recv_socket.send(result_b)

            elif "ack" in obj:
                print(f'got ack of id {obj["ack"]}')
                acks = [ack for ack in acks if ack["id"] != obj["ack"]]
                buffer = [elem for elem in buffer if elem["id"] != obj["ack"]]


            print("sent")

    if len(acks):
        if  time.time() - acks[0]["time"]  > TIMEOUT:
            recv_socket.send(_id, zmq.SNDMORE)
            recv_socket.send(buffer[0]["result"])

            
    # process the sensor data
    # send back processed data




