import socket
import sys
import pickle
import cache_management
import msg_access


def add_via(data):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> local DNS server"
    return message


def main():
    # Read localDNSserver port from 'config.txt'
    with open("textFiles/config.txt", "r") as f:
        for line in f.readlines():
            if "local_dns_server" in line:
                config = line.split()
                localDNSPort = config[7]
                break;
    
    if len(sys.argv) != 2 or sys.argv[1] != localDNSPort:
        print("Usage: python localDNSserver.py", localDNSPort) # same as port# in config.txt
        return

    # Read rootDNSserver from 'config.txt' and save in cache
    with open("textFiles/config.txt", "r") as f:
        for line in f.readlines():
            if "root_dns_server" in line:
                config = line.split()
                cache = [config[3], ":", config[5], ", A ,", config[7]]
                cache_management.cache_access("w", "localDNSserverCache.txt", cache)
                break;
    
    
    localDNSPort = int(sys.argv[1]) # port = 23002 (same as config.txt)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as localDNSSocket:
        localDNSSocket.bind(('', localDNSPort)) # Bind to all network interface
        
        cache_management.cache_print("localDNSserverCache.txt")

        print("The localDNSserver is ready to receive")

        while True:
            message, clientAddress = localDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)
            
            """
            recursiveFlag에 따라 각 요청 처리
            1. cache에 domain이 key로 존재
                1-1. RR(A (,CNAME))반환O
                1-2. authoritative RR(NS, A) -> authoritative 이동 후 RR(A) 반환
                1-3. TLD RR(NS, A) -> TLD 이동 후 authoritative RR(NS, A) 반환
            2. cache에 없으면
                2-1. TLD서버에 대한 cache존재 시 TLD서버로 이동
                2-2. root 이동
            """
            # localDNSserver always request recursive query
            messageFromClient=msg_access.msg_set(messageFromClient, 
                               via = "local DNS server", 
                               recursiveFlag = True
                            )

            domain = msg_access.get_value(messageFromClient, type="domain")
            data=cache_management.cache_access("s", "localDNSserverCache.txt", domain)
            """
            response에 via 항상 추가, caching 구현해야함!!!!!
            """
            # Domain in cache
            if data:
                RR_type = cache_management.cache_get(data, type="RR_type")
                RR_value = cache_management.cache_get(data, type="RR_value")

                # Return IP
                if RR_type == 'A':
                    replyMessage=msg_access.msg_reply(messageFromClient,
                                                        IP=RR_value,
                                                        authoritative=True)
                    localDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

                # CNAME -> A return IP
                elif RR_type == 'CNAME': 
                    RR_A = cache_management.cache_access("s", "localDNSserverCache.txt", RR_value)
                    RR_A_value = cache_management.cache_get(RR_A, type="RR_value")
                    replyMessage=msg_access.msg_reply(messageFromClient,
                                                      IP=RR_A_value,
                                                      authoritative=True)
                    localDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

                # NS -> A access to authoritative DNS server
                elif RR_type == 'NS': 
                    RR_A = cache_management.cache_access("s", "localDNSserverCache.txt", RR_value)
                    RR_A_type=cache_management.cache_get(RR_A, type="RR_type")
                    if RR_A_type == "A":
                        destPort = cache_management.cache_get(RR_A, type="RR_port")
                    localDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", destPort))
                    """
                    authoritative서버에서 처리 구현해야함
                    """
                    messageFromServer = add_via(localDNSSocket.recvfrom(2048))
                    localDNSSocket.sendto(pickle.dumps(messageFromServer), clientAddress)
            
            # Domain not in cache:
            else:
                """
                TLD서버가 caching되어있으면 TLD서버에 전달
                수신하는 메세지마다 reply검사 필요
                """
                TLDcaching = cache_management.cache_access("s", "localDNSserverCache.txt", "dns.comTLDDNSsolution.com")
                
                if TLDcaching==False:
                    root = cache_management.cache_access("s", "localDNSserverCache.txt", "dns.rootDNSservice.com")
                    rootPort = cache_management.cache_get(root, type="RR_port")
                    localDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", rootPort))
                    """
                    send to root DNS server
                    """
                    messageFromRoot = add_via(localDNSSocket.recvfrom(2048))

                    # root recursive accepted
                    if msg_access.get_value(messageFromRoot, type="reply"):
                        localDNSSocket.sendto(pickle.dumps(messageFromRoot), clientAddress)
                    # root recursive denied
                    destPort = msg_access.get_value(messageFromRoot, type="nextDest")
                else:
                    destPort = cache_management.cache_get(TLDcaching, type="RR_port")
                localDNSSocket.sendto(pickle.dumps(messageFromRoot), ("127.0.0.1", destPort))
                """
                send to TLD DNS server
                """
                messageFromTLD = add_via(localDNSSocket.recvfrom(2048))

                # TLD recursive accepted
                if msg_access.get_value(messageFromTLD, type="reply"):
                    localDNSSocket.sendto(pickle.dumps(messageFromTLD), clientAddress)

                # TLD recursive denied
                else:
                    destPort = msg_access.get_value(messageFromTLD, type="nextDest")
                    localDNSSocket.sendto(pickle.dumps(messageFromTLD), ("127.0.0.1", destPort))
                    """
                    send to authoritative DNS server
                    """
                    messageFromAuthoritative = add_via(localDNSSocket.recvfrom(2048))

                    localDNSSocket.sendto(pickle.dumps(messageFromAuthoritative), clientAddress)
                        

if __name__ == "__main__":
    main()