import socket

HEADER = 64
PORT = 5050
hostname = socket.gethostname()
SERVER = ""
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = 'DISCONNECT'
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)


def main():
    send()


def send():
    msg = input(" -> ")
    while True:
        client.send(msg.encode(FORMAT))
        data = client.recv(2048).decode()
        print(data)
        if msg == 't':
            break
        msg = input(" -> ")


if __name__ == '__main__':
    main()
