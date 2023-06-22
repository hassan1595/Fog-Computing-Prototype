import pickle as pk
import time
import zmq
import numpy as np
from lib.pca import PCA





# parameters
buffer_max_size = 100 # maximum buffer size to store messages that not yet received by other components
TIMEOUT = 10 # Time out in seconds before a messeage is retransmitted
HOST = "0.0.0.0" # accepts connections from all clients
PORT = 4000  # The port used by the server
sleep_time = 0.5 # sleep time of the server before the next message poll


context = zmq.Context()
recv_socket = context.socket(zmq.ROUTER)
recv_socket.bind("tcp://{}:{}".format(HOST, PORT))
poll = zmq.Poller()
poll.register(recv_socket, zmq.POLLIN)

# buffer to store sent messages in case of retransmission
buffer = []
# store the awaited id of the acknowledgments
acks = []


while True:
    
    #  polls to check received messages
    sockets = dict(poll.poll(1000))
    if recv_socket in sockets:
        if sockets[recv_socket] == zmq.POLLIN:
            _id = recv_socket.recv()
            obj_b = recv_socket.recv()
            obj = pk.loads(obj_b)

            # client sent data
            if "data" in obj:
                ack_obj_b = pk.dumps({"ack" : obj["id"]})

                # sent ack to client
                recv_socket.send(_id, zmq.SNDMORE)
                recv_socket.send(ack_obj_b)

                # apply pca to data
                pca = PCA(obj["data"])
                result = pca.project(obj["data"],2)
                result_b = pk.dumps({"id": obj["id"], "result": result, "pca": pca.U[:,:2].T})

                # add result to buffer in case of retransmission
                buffer.append({"id" : obj["id"], "result": result_b})
                acks.append({"id" : obj["id"], "time": time.time()})


                recv_socket.send(_id, zmq.SNDMORE)
                recv_socket.send(result_b)

            # client sent ack to state they received a result
            elif "ack" in obj:
                print(f'got ack of id {obj["ack"]}')

                # delete result from buffer because client already received it
                acks = [ack for ack in acks if ack["id"] != obj["ack"]]
                buffer = [elem for elem in buffer if elem["id"] != obj["ack"]]


            print("sent")

    # check for time out of the latest message and retranssmit if necessary  
    if len(acks):
        if  time.time() - acks[0]["time"]  > TIMEOUT:
            recv_socket.send(_id, zmq.SNDMORE)
            recv_socket.send(buffer[0]["result"])

            
    time.sleep(sleep_time)




