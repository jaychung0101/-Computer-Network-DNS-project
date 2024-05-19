import cache_management

def main():
    cache_path = "textFiles/localDNSserverCache.txt"

    print("Are you sure to reset localDNSserevr cache?")
    print("localDNSserverCache.txt:")
    cache_management.cache_access("r", cache_path)
    user_input = input("Enter y/n >> ")

    if user_input=="y":
        with open(cache_path, "w") as f:
            init = "[0] key [2] value [4] type [6] port"
            f.write(init)

        print("cache reset success. Please restart local DNS server")

    return

if __name__ == "__main__":
    main()