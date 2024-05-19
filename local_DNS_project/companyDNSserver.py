import socket
import sys
import pickle
import os

from utils import cache_utils
from utils import msg_utils

def add_via(data, dnsServer):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> " + dnsServer
    return message


def sys_validate():
    if len(sys.argv) != 3:
        print("Usage: python companyDNSserver.py <port> <companyName.txt>")
        return
    
    config_path = "textFiles/config.txt"
    cache_path = "textFiles/" + sys.argv[2]
    if not os.path.exists(cache_path):
        print(sys.argv[2], "does not exist")
        print("Usage: python companyDNSserver.py <port> <companyName.txt>")
        return

    companyName = sys.argv[2].split('.')[0]
    companyDNSserver = companyName + "_dns_server"
    with open(config_path, "r") as f:
        for line in f.readlines():
            if companyDNSserver in line:
                config = line.split()
                companyDNSPort = config[7]
                break; 
    
    if sys.argv[1] != companyDNSPort:
        print("Usage: python companyDNSserver.py", companyDNSPort, sys.argv[2])
        return

    companyDNSPort = int(sys.argv[1])
    return cache_path, companyName, companyDNSserver, companyDNSPort


def main():
    cache_path, companyName, companyDNSserver, companyDNSPort = sys_validate()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as companyDNSSocket:
        companyDNSSocket.bind(('', companyDNSPort)) # Bind to all network interface
        
        cache_management.cache_print(cache_path)

        print("The", companyName, "DNS server is ready to receive")
        
        while True:
            message, clientAddress = companyDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)
            
            path=" -> " + companyDNSserver
            messageFromClient=msg_utils.msg_set(messageFromClient, via=path)

            RR_key = msg_utils.get_value(messageFromClient, "domain")
            RR_A = cache_management.cache_access("s", cache_path, RR_key)

            # END OF DNS-2/3/4
            # Domain exists
            if RR_A:

                # if RR_A is CNAME, get A type RR
                if cache_management.cache_get(RR_A, type="RR_type") == "CNAME":
                    RR_CNAME = RR_A
                    RR_A_key = cache_management.cache_get(RR_CNAME, type="RR_value")
                    RR_A = cache_management.cache_access("s", cache_path, RR_A_key)
                
                RR_A_value = cache_management.cache_get(RR_A, type="RR_value")
                replyMessage=msg_utils.msg_reply(messageFromClient,
                                                  IP=RR_A_value,
                                                  cachingRR_1=RR_A,
                                                  cachingRR_2=RR_CNAME,
                                                  authoritative=True
                                                  )
                
            # Domain not exists
            else:
                # END OF DNS-5
                replyMessage=msg_utils.msg_reply(messageFromClient,
                                                  IP=False,
                                                  authoritative=False
                                                  )
                
            companyDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

if __name__ == "__main__":
    main()