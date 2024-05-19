import socket
import sys
import pickle
import cache_management
import msg_access

def caching_and_display(message, path):
    cachingRR_1=msg_access.get_value(message, "cachingRR_1")
    cachingRR_2=msg_access.get_value(message, "cachingRR_2")
    print("cachingRR_1 >>", cachingRR_1)
    print("cachingRR_2 >>", cachingRR_2)
    if cachingRR_1:
        cachingRR_1=cachingRR_1.split()
        cachingRR_1=[cachingRR_1[0], ":"] + cachingRR_1[2:]
        cache_management.cache_access("w", path, cachingRR_1)
    if cachingRR_2:
        cachingRR_2=cachingRR_2.split()
        cachingRR_2=[cachingRR_2[0], ":"] + cachingRR_2[2:]
        cache_management.cache_access("w", path, cachingRR_2)
    print()


def add_via(data):
    message = data[0]
    message = pickle.loads(message)
    message['via'] = message.get('via') + " -> local DNS server"
    return message


def sys_validate():
    config_path = "textFiles/config.txt"
    cache_path = "textFiles/localDNSserverCache.txt"

    # Read localDNSserver port from 'config.txt'
    with open(config_path, "r") as f:
        for line in f.readlines():
            if "local_dns_server" in line:
                config = line.split()
                localDNSPort = config[7]
                break;
    
    if len(sys.argv) != 2 or sys.argv[1] != localDNSPort:
        print("Usage: python localDNSserver.py", localDNSPort) # same as port# in config.txt
        return

    # Read rootDNSserver from 'config.txt' and save in cache
    with open(config_path, "r") as f:
        for line in f.readlines():
            if "root_dns_server" in line:
                config = line.split()
                cache = [config[3], ":", config[5], ", A ,", config[7]]
                cache_management.cache_access("w", cache_path, cache)
                break;
    
    localDNSPort = int(sys.argv[1]) # port = 23002 (same as config.txt)
    return cache_path, localDNSPort


def main():
    cache_path, localDNSPort = sys_validate()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as localDNSSocket:
        localDNSSocket.bind(('', localDNSPort)) # Bind to all network interface
        
        cache_management.cache_print(cache_path)

        print("The localDNSserver is ready to receive")

        while True:
            message, clientAddress = localDNSSocket.recvfrom(2048)
            print("receive message from", clientAddress)
            messageFromClient = pickle.loads(message)

            # localDNSserver always request recursive query
            messageFromClient = msg_access.msg_set(messageFromClient, 
                                                   via = "local DNS server", 
                                                   recursiveFlag = True
                                                   )
            domain = msg_access.get_value(messageFromClient, type="domain")
            data = cache_management.cache_access("s", cache_path, domain)

            # END OF DNS-1
            # Domain exists
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
                    RR_A = cache_management.cache_access("s", cache_path, RR_value)
                    RR_A_value = cache_management.cache_get(RR_A, type="RR_value")
                    replyMessage=msg_access.msg_reply(messageFromClient,
                                                      IP=RR_A_value,
                                                      authoritative=True)
                    localDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)

                elif domain=="com":
                    replyMessage=msg_access.msg_reply(messageFromClient,
                                                      IP="Invalid domain",
                                                      authoritative=True)
                    localDNSSocket.sendto(pickle.dumps(replyMessage), clientAddress)
            
            # Domain not exists:
            else:
                domain = domain.split('.')
                authoritativeCaching = cache_management.cache_access("s", cache_path, '.'.join(domain[len(domain)-2:]))
                TLDcaching = cache_management.cache_access("s", cache_path, domain[len(domain)-1])

                # authoritative not caching
                if authoritativeCaching==False:

                    # TLD not caching
                    if TLDcaching==False:
                        root = cache_management.cache_access("s", cache_path, "dns.rootDNSservice.com")
                        rootPort = cache_management.cache_get(root, type="RR_port")
                        localDNSSocket.sendto(pickle.dumps(messageFromClient), ("127.0.0.1", rootPort))
                        """
                        send to root DNS server
                        """
                        messageFromRoot = add_via(localDNSSocket.recvfrom(2048))

                        # END OF DNS-2
                        # root recursive accepted
                        if msg_access.get_value(messageFromRoot, type="reply"):

                            print("From root(root recursive accepted):")
                            caching_and_display(messageFromRoot, cache_path)

                            localDNSSocket.sendto(pickle.dumps(messageFromRoot), clientAddress)
                            continue

                        # root recursive denied
                        else:
                            print("From root(root recursive denied):")
                            caching_and_display(messageFromRoot, cache_path)

                            destPort = msg_access.get_value(messageFromRoot, type="nextDest")

                    # TLD caching
                    else:
                        TLD_key = cache_management.cache_get(TLDcaching, type="RR_value")
                        TLD_A = cache_management.cache_access("s", cache_path, TLD_key)
                        destPort = cache_management.cache_get(TLD_A, "RR_port")
                        messageFromRoot = messageFromClient

                    localDNSSocket.sendto(pickle.dumps(messageFromRoot), ("127.0.0.1", destPort))
                    """
                    send to TLD DNS server
                    """
                    messageFromTLD = add_via(localDNSSocket.recvfrom(2048))

                    # END OF DNS-3
                    # TLD recursive accepted 
                    if msg_access.get_value(messageFromTLD, type="reply"):
                        print("From TLD(TLD recursive accepted):")
                        caching_and_display(messageFromTLD, cache_path)

                        localDNSSocket.sendto(pickle.dumps(messageFromTLD), clientAddress)

                    # TLD recursive denied
                    else:
                        print("From TLD(TLD recursive denied):")
                        caching_and_display(messageFromTLD, cache_path)
                        
                        destPort = msg_access.get_value(messageFromTLD, type="nextDest")

                # authoritative caching
                else:
                    authoritative_key = cache_management.cache_get(authoritativeCaching, type="RR_value")
                    authoritative_A = cache_management.cache_access("s", cache_path, authoritative_key)
                    destPort = cache_management.cache_get(authoritative_A, "RR_port")
                    messageFromTLD=messageFromClient

                localDNSSocket.sendto(pickle.dumps(messageFromTLD), ("127.0.0.1", destPort))
                """
                send to authoritative DNS server
                """
                messageFromAuthoritative = add_via(localDNSSocket.recvfrom(2048))
                print("From authoritative:")
                caching_and_display(messageFromAuthoritative, cache_path)
                
                # END OF DNS-4/5
                if msg_access.get_value(messageFromAuthoritative, type="reply"):
                    localDNSSocket.sendto(pickle.dumps(messageFromAuthoritative), clientAddress)
                        

if __name__ == "__main__":
    main()