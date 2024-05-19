import socket
import sys
import pickle

from utils import msg_utils

def is_valid_message(data):
    parts = data.split()
    if len(parts) != 2:
        return False
    if parts[0] != "ipaddr":
        return False
    return parts[1]


def main():
    if len(sys.argv) != 2:
        print("Usage: python client.py <port>")
        return
    
    # Read localDNSserver from 'config.txt'
    with open("textFiles/config.txt", "r") as f:
        for line in f.readlines():
            if "local_dns_server" in line:
                config = line.split()
                break;

    destPort = int(config[7])
    srcPort = int(sys.argv[1])

    while True:
        temp = input("Type a message in format 'ipaddr <name>' >> ")
        
        if is_valid_message(temp):
            message=msg_utils.msg_set(init=True)
            message=msg_utils.msg_set(message, domain=is_valid_message(temp))
            break
        print("Please follow the given format 'ipaddr <name>'\n")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clientSocket:    
        clientSocket.bind(('localhost', srcPort))
        clientSocket.sendto(pickle.dumps(message), ("127.0.0.1", destPort))

        modifiedMessage, _ = clientSocket.recvfrom(2048)
        modifiedMessage = pickle.loads(modifiedMessage)

    # name resolution success
    if msg_utils.get_value(modifiedMessage, type="authoritative"):
        print(msg_utils.get_value(modifiedMessage, type="domain"), ":", msg_utils.get_value(modifiedMessage, type="IP"))

    # name resolution fail
    else:
        print(msg_utils.get_value(modifiedMessage, type="domain"), ": Can't find IP Address")
        
    print("(via:", msg_utils.get_value(modifiedMessage, type="via"), ")")

if __name__ == "__main__":
    main()