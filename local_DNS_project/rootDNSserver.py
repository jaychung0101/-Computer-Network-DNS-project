import socket
import sys
import pickle
import cache_management
import msg_access

def add_via(data):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> root DNS server"
    return message


def main():
    config_path = "textFiles/config.txt"
    cache_path = "textFiles/rootDNSserverCache.txt"

    # Read rootDNSserver port from 'config.txt'
    with open(config_path, "r") as f:
        for line in f.readlines():
            if "root_dns_server" in line:
                config = line.split()
                rootDNSPort = config[7]
                break;
    
    if len(sys.argv) != 2 or sys.argv[1] != rootDNSPort:
        print("Usage: python rootDNSserver.py 23003") # same as port number in config.txt
        return
    
    # Read all TLDDNSserver from 'config.txt' and save in cache
    with open(config_path, "r") as f:
        for line in f.readlines():
            if "TLD_dns_server" in line:
                config = line.split()
                TLD_A = [config[3], ":", config[5], ", A ,", config[7]]
                cache_management.cache_access("w", cache_path, TLD_A)
                TLD_NS = ["com", ":", config[3], ", NS"]
                cache_management.cache_access("w", cache_path, TLD_NS)

    while True:
        user_input = input("recursiveFlag(Enter on/off) >> ")
        if  user_input == "on":
            rootRecursiveFlag = True
            print("recursive processing : ON\n")
            break
        elif user_input == "off":
            rootRecursiveFlag = False
            print("recursive processing : OFF\n")
            break

        print("Please enter 'on' or 'off'")

    rootDNSPort = int(sys.argv[1]) # port = 23003 (same as config.txt)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as rootDNSSocket:
        rootDNSSocket.bind(('', rootDNSPort)) # Bind to all network interface
        
        cache_management.cache_print(cache_path)

        print("The rootDNSserver is ready to receive")

        while True:
            message, clientAddress = rootDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)
            
            messageFromClient=msg_access.msg_set(messageFromClient, via=" -> root DNS server")
            domain=msg_access.get_value(messageFromClient, type="domain").split('.')
            RR_TLD_NS=cache_management.cache_access("s", cache_path, domain[len(domain)-1])
            RR_TLD = cache_management.cache_access("s", cache_path, cache_management.cache_get(RR_TLD_NS, "RR_value"))
            if RR_TLD:
                # rootRecursive query
                if rootRecursiveFlag==True:
                    messageFromClient=msg_access.msg_set(messageFromClient, rootRecursiveFlag=True)
                    destPort=cache_management.cache_get(RR_TLD, type="RR_port")
                    rootDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", destPort))
                    """
                    send to TLD DNS server
                    """
                    messageFromTLD=add_via(rootDNSSocket.recvfrom(2048))
                    rootDNSSocket.sendto(pickle.dumps(messageFromTLD), clientAddress)
                    continue
                
                # iterated query
                else:
                    destPort=cache_management.cache_get(RR_TLD, type="RR_port")
                    messageFromClient=msg_access.msg_set(messageFromClient, 
                                                         rootRecursiveFlag=False,
                                                         cachingRR_1=RR_TLD,
                                                         cachingRR_2=RR_TLD_NS,
                                                         nextDest=destPort)
                    rootDNSSocket.sendto(pickle.dumps(messageFromClient), clientAddress)
            
            # TLD not exists
            else:
                replyMessage=msg_access.msg_reply(messageFromClient,
                                                  IP=False,
                                                  authoritative=False)
                rootDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

if __name__ == "__main__":
    main()