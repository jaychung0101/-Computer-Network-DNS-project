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
    if len(sys.argv) != 2 or int(sys.argv[1]) != 23003:
        print("Usage: python rootDNSserver.py 23003") # same as port number in config.txt
        return
    
    # Read all TLDDNSserver from 'config.txt' and save in cache
    with open("config.txt", "r") as f:
        for line in f.readlines():
            if "TLD_dns_server" in line:
                config = line.split()
                cache = [config[3], ":", config[5], ", A ,", config[7]]
                cache_management.cache_access("w", "rootDNSserverCache.txt", cache)

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
        
        cache_management.cache_print("rootDNSserverCache.txt")

        print("The rootDNSserver is ready to receive")

        while True:
            message, clientAddress = rootDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)
            
            """
            cache에
            1. 있으면 
                1-1. rootRecursiveFlag = True 이면 rootrootRecursiveFlag = True 후 TLD로 recursive
                1-2. rootRecursiveFlag = False 이면 TLD RR(A)를 local로 반환 후 iterative
            2. 없으면
                local로 없다고 알려줘야함
            """
            messageFromClient=msg_access.msg_set(messageFromClient, via=" -> root DNS server")
            domain=msg_access.get_value(messageFromClient, type="domain").split('.')
            RR_TLD=cache_management.cache_access("i", "rootDNSserverCache.txt", domain[len(domain)-1]+"TLD")
            if RR_TLD:
                # rootRecursive query
                if rootRecursiveFlag==True:
                    messageFromClient=msg_access.msg_set(messageFromClient, rootRecursiveFlag=True)
                    destPort=cache_management.cache_get(RR_TLD, type="RR_port")
                    rootDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", destPort))
                    """
                    TLD로 전송, caching 등
                    """
                    messageFromTLD=add_via(rootDNSSocket.recvfrom(2048))
                    rootDNSSocket.sendto(pickle.dumps(messageFromTLD), clientAddress)
                
                # iterated query
                else:
                    destPort=cache_management.cache_get(RR_TLD, type="RR_port")
                    messageFromClient=msg_access.msg_set(messageFromClient, 
                                                         rootRecursiveFlag=False,
                                                         nextDest=destPort)
                    rootDNSSocket.sendto(pickle.dumps(messageFromClient), clientAddress)
            
            else: # If there is no TLD server include messageFromClient['domain'] in cache:
                replyMessage=msg_access.msg_reply(messageFromClient,
                                                  IP="Fail to search",
                                                  authoritative=False)
                rootDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

if __name__ == "__main__":
    main()