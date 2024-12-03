import json
import threading
import zmq
import hashlib
from sys import argv

servers_hash_socket = {}
servers_hash_port = {}
servers_hash = []

def broker(number_servers, number_neighbours, broker_port):

    print(f"Broker port = {broker_port}")

    context = zmq.Context()
    client_socket = context.socket(zmq.REP)
    client_socket.setsockopt(zmq.LINGER, 0)
    client_socket.bind(f"tcp://*:{broker_port}")
    
    for i in range(number_servers):    
        port = 5557 + i
        server_socket = context.socket(zmq.REQ)
        server_socket.connect(f"tcp://localhost:{port}")
        for j in range(5):
            server_partion = "server_" + str(port) + "_" + str(j)
            hash = hashlib.sha256(server_partion.encode()).hexdigest()
            servers_hash.append(hash)
            servers_hash_port[hash] = port
            servers_hash_socket[hash] = server_socket

    servers_hash.sort()
    
    while True:
        
        # receive message from client socket
        try: 
            message = json.loads(client_socket.recv().decode())
        
        # deal with possible errors
        except zmq.ZMQError as e:
            print(f"Error in client socket: {e}")
            client_socket.close()
            client_socket = context.socket(zmq.REP)
            client_socket.setsockopt(zmq.LINGER, 0)
            client_socket.bind(f"tcp://*:{broker_port}")
            continue
            
        # see who is responsible to process message
        hash_message_word = hashlib.sha1(message["url"].encode()).hexdigest()
        choosen_server_hash = servers_hash[0]
        for i in range(len(servers_hash)):
            if hash_message_word <= servers_hash[i]:
                choosen_server_hash = servers_hash[i]
                break  
        
        # send message to server socket and response to client socket
        try:
            print(f"Broker port {broker_port} encaminhando para o servidor {servers_hash_port[choosen_server_hash]}")
            server_socket = servers_hash_socket[choosen_server_hash]   
            server_socket.send(json.dumps(message).encode())
            response = server_socket.recv().decode()
            client_socket.send(response.encode())
        
        # deal with possible errors
        except zmq.ZMQError as e:
            print(f"Error in server socket: {e}")
            server_socket.close()
            server_socket = context.socket(zmq.REQ)
            server_socket.connect(f"tcp://localhost:{servers_hash_port[choosen_server_hash]}")
            continue




if __name__ == "__main__":
    
    if(len(argv) < 3):
        print("Erro - parâmetros ausentes")
    
    else:  
        param1 = int(argv[1])
        param2 = int(argv[2])        
        thread1 = threading.Thread(target=broker, args=(param1, param2, 5555))
        thread2 = threading.Thread(target=broker, args=(param1, param2, 5556))
        thread1.start()
        thread2.start()
