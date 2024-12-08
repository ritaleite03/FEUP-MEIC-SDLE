# SDLE Second Assignment

SDLE Second Assignment of group T04G16.

Group members:

1. Rita Leite (up202105309@edu.fe.up.pt)
2. Sofia Moura (up201907201@edu.fe.up.pt)
3. Tiago Azevedo (up202108699@edu.fe.up.pt)

## How to Run:

### Servers

Open 5 different terminals and run:

`python3 server.py <port> <number of servers> <number of neighbors`.

This will start each server with an assigned port, and they can build the hash ring with the information received about the number of servers the system will have.

In our case, since ports `5555` and `5556` will already be occupied, we run the following:

-   `python3 server.py 5557 5 2`
-   `python3 server.py 5558 5 2`
-   `python3 server.py 5559 5 2`
-   `python3 server.py 5560 5 2`
-   `python3 server.py 5561 5 2`

## Broker

Open another terminal and run:

`python3 broker.py <number of servers> <number of neighbors`

This command will cause two brokers to be launched, one on port 5555 and another on port 5556. The command is as follows:

-   `python3 broker.py 5 2`

## Client

Open another terminal and run, where id can be any number:

`python3 client.py <id>`
