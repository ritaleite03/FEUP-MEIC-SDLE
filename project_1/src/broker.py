import json
import threading
import zmq
import random
import hashlib
from sys import argv
from server import Server


servers_hash_socket = {}
servers_hash_port = {}
servers_hash = []

# if no answer from server in timeout ms, server is down
def server_alive(server_socket, timeout = 2000):
    try:
        # tries to ping server
        server_socket.send(b"ping")
        server_socket.setsockopt(zmq.RCVHWM, 1)  # pending messages
        response = server_socket.recv(flags=zmq.NOBLOCK)
        return True  # alive
    except zmq.Again:
        return False  # down



def broker(number_servers, number_neighbours):
    
    # create socket
    context = zmq.Context()
    client_socket = context.socket(zmq.REP)
    client_socket.bind("tcp://*:5555")
    
    # create ring
    for i in range(number_servers):    
        port = 5556 + i
        server_socket = context.socket(zmq.REQ)
        server_socket.connect(f"tcp://localhost:{port}")
        for j in range(5):
            server_partion = "server_" + str(port) + "_" + str(j)
            hash = hashlib.sha256(server_partion.encode()).hexdigest()
            servers_hash.append(hash)
            servers_hash_port[hash] = port
            servers_hash_socket[hash] = server_socket

        # Start each server in a new thread
        server = Server(port, number_servers, number_neighbours)
        thread = threading.Thread(target=server.run)
        thread.start()

    # order hashes
    servers_hash.sort()
    
    while True:
        
        message = json.loads(client_socket.recv().decode())
        hash_message_word =hashlib.sha1(message["url"].encode()).hexdigest()
        
        choosen_server_hash = servers_hash[0]
        chosen_server_index = 0
        for i in range(len(servers_hash)):
            if hash_message_word <= servers_hash[i]:
                choosen_server_hash = servers_hash[i]
                choosen_server_hash = i
                break            
        
        if server_alive(server_socket):
            # send request to server
            print(f"Incoming to server {servers_hash_port[choosen_server_hash]}")
            server_socket = servers_hash_socket[choosen_server_hash]
            # send reply to client
            server_socket.send(json.dumps(message).encode())
            response = server_socket.recv().decode()
        
        print(f"Server {servers_hash_port[choosen_server_hash]} is down, trying next servidor.")
            
        # try following server
        next_server_found = False
        for i in range(chosen_server_index, len(servers_hash)):
            next_server_hash = servers_hash[i]
            next_server_socket = servers_hash_socket[next_server_hash]
            if server_alive(next_server_socket):
                print(f"Incoming to server {servers_hash_port[next_server_hash]}")
                next_server_socket.send(json.dumps(message).encode())
                response = next_server_socket.recv().decode()
                # send reply to client
                client_socket.send(response.encode())
                next_server_found = True
                break
        
        # if all servers down, error
        if not next_server_found:
            client_socket.send(b"Error: All servers down")


if __name__ == "__main__":
    if(len(argv) < 3):
        print("Error - missing parameters")
    else:
        broker(int(argv[1]), int(argv[2]))