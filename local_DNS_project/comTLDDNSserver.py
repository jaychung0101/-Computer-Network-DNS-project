import socket
import sys
import pickle
import cache_management
import msg_access

def add_via(data):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> .com TLD DNS server"
    return message


def main():
    # Read comTLDDNSserver port from 'config.txt'
    with open("textFiles/config.txt", "r") as f:
        for line in f.readlines():
            if "comTLD_dns_server" in line:
                config = line.split()
                comTLDDNSPort = config[7]
                break;

    if len(sys.argv) != 2 or sys.argv[1] != comTLDDNSPort:
        print("Usage: python comTLDDNSserver.py ", comTLDDNSPort) # same as port# in config.txt
        return

    # Read all .com authoritative from 'config.txt' and save in cache
    with open("textFiles/config.txt", "r") as f:
        """
        .com회사들의 authoritative서버의 NS와 A 저장 필요
        """
        # for line in f.readlines():
        #     if "comTLD_dns_server" in line:
        #         config = line.split()
        #         cache = [config[3], ":", config[5], ", A ,", config[7]]
        #         cache_management.cache_access("w", "comTLDDNSserverCache.txt", cache)
        #         break;
    
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
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as comTLDDNSSocket:
        comTLDDNSSocket.bind(('', comTLDDNSPort)) # Bind to all network interface
        
        cache_management.cache_print("comTLDDNSserverCache.txt")

        print("The comTLDDNSserver is ready to receive")
        
        while True:
            message, clientAddress = comTLDDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)
            
            """
            TLDRecursiveFlag에 따라 각 요청 처리
            1. root에서 온 경우(rootRecursive=True)
                - authoritative로 recursive요청
            2. localDNS에서 온 경우(rootRecursive=False)
                2-1. TLDRecursiveFlag=True인 경우
                    - authoritative로 recursive요청
                2-2. TLDRecursiveFlag=Flase인 경우
                    localDNS로
                    - CNAME있으면 CNAME, A반환
                    - authoritative의 NS, A 반환
            """
            messageFromClient=msg_access.msg_set(messageFromClient, via=" -> .com TLD DNS server")

            RR_key = '.'.join(msg_access.get_value(messageFromClient, "domain").split('.')[-3:])
            RR = cache_management.cache_access("s", "comTLDDNSserverCache.txt", RR_key)
            if RR:
                RR_type = cache_management.cache_get(RR, type="RR_type")
                RR_value = cache_management.cache_get(RR, type="RR_value")
                RR_A = cache_management.cache_access("s", "comTLDDNSserverCache.txt", RR_value)

                # TLD has CNAME
                if RR_type == "CNAME":
                    IP = cache_management.cache_get(RR_A, type="RR_value")
                    replyMessage=msg_access.msg_reply(messageFromClient,
                                                      IP = IP,
                                                      cachingRR_1=RR_A,
                                                      cachingRR_2=RR,
                                                      authoritative=True
                                                      )
                    
                    comTLDDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)
                
                # TLD has NS
                elif RR_type == "NS":
                    destPort = cache_management.cache_get(RR_A, type="RR_port")

                    # recursive query(send by root DNS server or local DNS server)
                    if msg_access.get_value(messageFromClient, "rootRecursiveFlag") == True or TLDRecursiveFlag == True:
                        messageFromClient=msg_access.msg_set(messageFromClient, TLDRecursiveFlag=True)
                        comTLDDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", destPort))
                        """
                        authoritative
                        """
                        messageFromAuthoritative=add_via(comTLDDNSSocket.recvfrom(2048))
                        comTLDDNSSocket.sendto(pickle.dumps(messageFromAuthoritative), clientAddress)
                    
                    # iterated query
                    else:
                        messageFromClient=msg_access.msg_set(messageFromClient,
                                                             cachingRR_1=RR,
                                                             cachingRR_2=RR_A,
                                                             nextDest=destPort
                                                             )
                        comTLDDNSSocket.sendto(pickle.dumps(messageFromClient), clientAddress)

            # if domain not in cache
            else:
                # end of query
                replyMessage=msg_access.msg_reply(messageFromClient,
                                                  IP="Fail to search",
                                                  authoritative=False
                                                  )
                comTLDDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

if __name__ == "__main__":
    main()