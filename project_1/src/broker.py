import json
import threading
import zmq
import hashlib
from sys import argv

servers_hash_socket = {}
servers_hash_port = {}
servers_hash = []

def broker(number_servers, number_neighbours, broker_port):
    # create client side's socket
    context = zmq.Context()
    client_socket = context.socket(zmq.REP)
    client_socket.setsockopt(zmq.LINGER, 0)
    client_socket.bind(f"tcp://*:{broker_port}")
    # create hash ring
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
    # deal with messages
    while True:
        try:
            # Receive message from client socket
            message = json.loads(client_socket.recv().decode())
            # Determine which server is responsible for processing the message
            hash_message_word = hashlib.sha1(message["url"].encode()).hexdigest()
            chosen_server_index = 0
            for i in range(len(servers_hash)):
                if hash_message_word <= servers_hash[i]:
                    chosen_server_index = i
                    break          
            # Send request to server (try other if original is down)
            print("Original server was " + str(servers_hash_port[servers_hash[i]]))
            for i in range(chosen_server_index, len(servers_hash)):
                server_hash = servers_hash[i]
                server_socket = servers_hash_socket[server_hash]
                print("Trying to send to " + str(servers_hash_port[server_hash]))
                try:                    
                    server_socket.send_string(json.dumps(message), zmq.DONTWAIT)
                    poller = zmq.Poller()
                    poller.register(server_socket, zmq.POLLIN)
                    events = dict(poller.poll(timeout=5000))
                    if server_socket in events and events[server_socket] == zmq.POLLIN:
                        response = server_socket.recv()
                        client_socket.send(response)
                        break
                    else:
                        server_socket.close()
                        server_socket = context.socket(zmq.REQ)
                        server_socket.connect(f"tcp://localhost:{servers_hash_port[server_hash]}")
                        servers_hash_socket[server_hash] = server_socket    
                        continue
                except:
                    print(f"Error in comunication with server")
                    server_socket.close()
                    server_socket = context.socket(zmq.REQ)
                    server_socket.connect(f"tcp://localhost:{servers_hash_port[server_hash]}")
                    servers_hash_socket[server_hash] = server_socket
                    continue
        except:
            print(f"Error in comunication with client")
            client_socket.close()
            client_socket = context.socket(zmq.REP)
            client_socket.setsockopt(zmq.LINGER, 0)
            client_socket.bind(f"tcp://*:{broker_port}")
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
