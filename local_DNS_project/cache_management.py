def cache_access(access_type, txt=None, data=[]):
    file = "textFiles/" + txt
    if not txt:
        print("Fail to read", txt)
        return
    
    with open(file, "r") as f:
        original_data = f.read()

    exist = False
    if access_type == "r": # read
        count = 0
        for line in original_data.split('\n'):
            if count == 0:
                count += 1
                continue
            print("\t{}. {}".format(count, ' '.join(line.split()[:5])))
            count += 1
        print()
    elif access_type == "i": # include
        for line in original_data.split('\n'):
            if data in line:
                exist = line
                break

        return exist
    elif access_type == "s": # key search
        for line in original_data.split('\n'):
            if data in line:
                elements = line.split()
                if elements[0] == data:
                    exist = line
                    break
        
        return exist
    elif access_type == "w": # write
        for line in original_data.split('\n'):
            if data[0] in line:
                exist = True
                break

        if not exist:
            with open(file, "w") as g:
                g.write(original_data + '\n')
                g.write(' '.join(data))


def cache_print(txt=None):
    if not txt:
        print("Fail to read", txt)
        return

    while True:
        user_input = input("Type \"cache\" to view the cache, press enter to only listen >> ")

        if user_input == "cache":
            print("\n" + "cache list")
            cache_access("r", txt)
            break
        elif user_input == "":
            break
    
    print("If you want to see cache again, please reboot the server!!\n")
    

def cache_get(data=None, type=None):
    # try:
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
            
        raise ValueError("'type' not provided(RR_key/RR_value/RR_type/RR_port)")
    # except (IndexError, ValueError) as e:
    #     print(f"Error in function 'cache_get': {e}")
    #     return