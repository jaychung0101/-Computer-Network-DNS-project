import socket
import sys
import pickle
import msg_access


# data유효성 검사
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
    
    # config.txt에서 localDNSserver 정보 읽기
    with open("config.txt", "r") as f:
        for line in f.readlines():
            if "local_dns_server" in line:
                config = line.split()
                break;

    destPort = int(config[7])
    srcPort = int(sys.argv[1])

    while True:
        temp = input("Type a message in format 'ipaddr <name>' >> ")
        
        if is_valid_message(temp):
            message=msg_access.msg_set(init=True)
            msg_access.msg_set(message, domain=is_valid_message(temp))
            break
        print("Please follow the given format 'ipaddr <name>'\n")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as clientSocket:    
        clientSocket.bind(('localhost', srcPort))
        clientSocket.sendto(pickle.dumps(message), ("127.0.0.1", destPort))

        modifiedMessage, _ = clientSocket.recvfrom(2048)
        modifiedMessage = pickle.loads(modifiedMessage)

    if msg_access.get_value(modifiedMessage, type="authoritative"):
        print(msg_access.get_value(modifiedMessage, type="domain"), ":", msg_access.get_value(modifiedMessage, type="IP"))
    else:
        print(msg_access.get_value(modifiedMessage, type="domain"), ": Can't find IP Address")
        
    print("(via:", msg_access.get_value(modifiedMessage, type="via"), ")")


if __name__ == "__main__":
    main()