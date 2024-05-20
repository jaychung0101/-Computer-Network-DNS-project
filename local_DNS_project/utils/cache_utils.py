def cache_access(access_type, cache_path=None, data=[]):
    if not cache_path:
        print("Fail to read", cache_path)
        return
    
    with open(cache_path, "r") as f:
        exist = False

        if access_type == "r": # read
            f.readline()
            count = 1
            for line in f:
                print("\t{}. {}".format(count, ' '.join(line.split()[:5])))
                count += 1
            print()

        elif access_type == "s": # key search
            for line in f:
                if data in line:
                    elements = line.split()
                    if elements[0] == data:
                        exist = line
                        break
                    
        elif access_type == "w": # write
            for line in f:
                if data[0] in line:
                    elements = line.split()
                    if elements[0] == data[0]:
                        exist = line
                        break

            if not exist:
                with open(cache_path, "a") as g:
                    g.write('\n')
                    g.write(' '.join(data))

        return exist


def cache_print(cache_path=None):
    if not cache_path:
        print("Fail to read", cache_path)
        return

    while True:
        user_input = input("Type \"cache\" to view the cache, press enter to only listen >> ")

        if user_input == "cache":
            print("\n" + "cache list")
            cache_access("r", cache_path)
            break
        elif user_input == "":
            break
    
    print("If you want to see cache again, please restart the server!!\n")
    

def cache_get(data=None, type=None):
    if not data:
        raise ValueError("'data' not provided")

    data = data.split()
    if type=="RR_key":
        return data[0]
    
    if type=="RR_value":
        return data[2]
    
    if type=="RR_type":
        return data[4]
    
    if type=="RR_port":
        if len(data) == 7:
            return int(data[6])
        else:
            raise IndexError("'port' does not exist")