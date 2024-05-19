import socket
import sys
import pickle

from utils import cache_utils
from utils import msg_utils

def add_via(data):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> .com TLD DNS server"
    return message


def sys_validate():
    config_path = "textFiles/config.txt"
    cache_path = "textFiles/comTLDDNSserverCache.txt"
    
    # Read comTLDDNSserver port from 'config.txt'
    with open(config_path, "r") as f:
        for line in f.readlines():
            if "comTLD_dns_server" in line:
                config = line.split()
                comTLDDNSPort = config[7]
                break;

    if len(sys.argv) != 2 or sys.argv[1] != comTLDDNSPort:
        print("Usage: python comTLDDNSserver.py", comTLDDNSPort) # same as port# in config.txt
        return
    
    # Read all .com authoritative from 'config.txt' and save in cache
    with open(config_path, "r") as f:
        for _ in range(4):
            f.readline()
        
        for line in f:
            config = line.split()
            NS = ['.'.join(config[3].split('.')[-2:]), ":", config[3], ", NS"]
            cache_utils.cache_access("w", cache_path, NS)
            A = [config[3], ":", config[5], ", A ,", config[7]]
            cache_utils.cache_access("w", cache_path, A)
    
    while True:
        user_input = input("recursiveFlag(Enter on/off) >> ")
        if  user_input == "on":
            TLDRecursiveFlag = True
            print("recursive processing : ON\n")
            break
        elif user_input == "off":
            TLDRecursiveFlag = False
            print("recursive processing : OFF\n")
            break

        print("Please enter 'on' or 'off'")
    
    comTLDDNSPort = int(sys.argv[1]) # port = 23004 (same as config.txt)
    return cache_path, TLDRecursiveFlag, comTLDDNSPort


def main():
    cache_path, TLDRecursiveFlag, comTLDDNSPort = sys_validate()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as comTLDDNSSocket:
        comTLDDNSSocket.bind(('', comTLDDNSPort)) # Bind to all network interface
        
        cache_utils.cache_print(cache_path)

        print("The comTLDDNSserver is ready to receive")
        
        while True:
            message, clientAddress = comTLDDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient=pickle.loads(message)
            messageFromClient=msg_utils.msg_set(messageFromClient, via=" -> .com TLD DNS server")

            domain=msg_utils.get_value(messageFromClient, "domain").split('.')
            RR_key='.'.join(domain[len(domain)-2:])
            RR_NS = cache_utils.cache_access("s", cache_path, RR_key)
            
            # NS exists
            if RR_NS:
                RR_NS_value = cache_utils.cache_get(RR_NS, type="RR_value")
                RR_A = cache_utils.cache_access("s", cache_path, RR_NS_value)
                
                # TLD has NS
                destPort = cache_utils.cache_get(RR_A, type="RR_port")
                messageFromClient=msg_utils.msg_set(messageFromClient,
                                                     cachingRR_1=RR_NS,
                                                     cachingRR_2=RR_A,
                                                     nextDest=destPort
                                                     )
                
                # END OF DNS-2/3
                # recursive query(send by root DNS server or local DNS server)
                if TLDRecursiveFlag == True or msg_utils.get_value(messageFromClient, "rootRecursiveFlag") == True:
                    comTLDDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", destPort))
                    """
                    send to authoritative DNS server
                    """
                    messageFromClient=add_via(comTLDDNSSocket.recvfrom(2048))

            # NS not exists
            else:
                # END OF DNS-5
                messageFromClient=msg_utils.msg_reply(messageFromClient,
                                                       IP=False,
                                                       authoritative=False
                                                       )
                
            comTLDDNSSocket.sendto(pickle.dumps(messageFromClient), clientAddress)

if __name__ == "__main__":
    main()