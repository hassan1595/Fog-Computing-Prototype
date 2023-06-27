import pickle as pk
import time
import zmq
import numpy as np
from lib.pca import PCA





# parameters
HOST = "0.0.0.0" # accepts connections from all clients
PORT = 4000  # The port used by the server
TIMEOUT = 10 # Time out in seconds before a messeage is retransmitted
buffer_max_size = 100 # maximum buffer size to store messages that not yet received by other components
sleep_time = 0.5 # sleep time of the server before the next message poll

# buffer to store sent messages in case of retransmission
buffer = []
# store the awaited id of the acknowledgments
acks = []


context = zmq.Context()
server_socket = context.socket(zmq.ROUTER)
server_socket.bind("tcp://{}:{}".format(HOST, PORT))
poll = zmq.Poller()
poll.register(server_socket, zmq.POLLIN)

while True:
    
    #  polls to check received messages
    sockets = dict(poll.poll(1000))
    if server_socket in sockets:
        if sockets[server_socket] == zmq.POLLIN:
            _id = server_socket.recv()
            obj_b = server_socket.recv()
            obj = pk.loads(obj_b)

            # client sent data
            if "data" in obj:

                print(f'\nrecieved data from client {_id}\n')

                # add result to buffer in case of retransmission
                buffer.append({"id" : obj["id"], "data": obj["data"], "socket_id": _id})
                acks.append({"id" : obj["id"], "time": time.time()})

                # sent ack to client
                ack_obj_b = pk.dumps({"ack" : obj["id"]})                
                server_socket.send(_id, zmq.SNDMORE)
                server_socket.send(ack_obj_b)


                # apply pca to data
                pca = PCA(obj["data"])
                result = pca.project(obj["data"],2)
                result_b = pk.dumps({"id": obj["id"], "result": result, "pca": pca.U[:,:2].T})

                # send result to client
                server_socket.send(_id, zmq.SNDMORE)
                server_socket.send(result_b)
                print(f'\nsent result to client {_id}\n')

            # client sent ack to state they received a result
            elif "ack" in obj:
                print(f'\ngot ack of id {obj["ack"]} from client {_id}\n')

                # delete result from buffer because client already received it
                acks = [ack for ack in acks if ack["id"] != obj["ack"]]
                buffer = [elem for elem in buffer if elem["id"] != obj["ack"]]


    # check for time out of the latest message and retranssmit if necessary  
    if len(acks):
        if  time.time() - acks[0]["time"]  > TIMEOUT:

            print("\ntime out happened\n")
            pca = PCA(buffer[0]["data"])
            result = pca.project(buffer[0]["data"],2)
            result_b = pk.dumps({"id": buffer[0]["id"], "result": result, "pca": pca.U[:,:2].T})
            server_socket.send(buffer[0]["socket_id"], zmq.SNDMORE)
            server_socket.send(result_b)
            print(f'\nretranssmited data to client {buffer[0]["socket_id"]}')

            
    time.sleep(sleep_time)




