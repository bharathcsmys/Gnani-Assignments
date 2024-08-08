import redis

class RedisClient:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_conn = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def redis_set_value(self, key, value):
        return self.redis_conn.set(key, value)

    def redis_get_value(self, key):
        return self.redis_conn.get(key)

    def redis_set_dict_value(self, key, value):
        if not isinstance(value, dict):
            raise ValueError("Value must be a dictionary")
        if self.redis_conn.type(key) != 'hash':
            self.redis_conn.delete(key)
        return self.redis_conn.hset(key, mapping=value)

    def redis_get_dict_value(self, key):
        if self.redis_conn.type(key) != 'hash':
            raise TypeError(f"Key '{key}' is not of type hash")
        return self.redis_conn.hgetall(key)

    def redis_set_value_and_expiry(self, key, value, expiry):
        return self.redis_conn.setex(key, expiry, value)

    def redis_set_dict_value_and_expiry(self, key, value, expiry):
        if not isinstance(value, dict):
            raise ValueError("Value must be a dictionary")
        if self.redis_conn.type(key) != 'hash':
            self.redis_conn.delete(key)
        pipeline = self.redis_conn.pipeline()
        pipeline.hset(key, mapping=value)
        pipeline.expire(key, expiry)
        return pipeline.execute()

    def redis_delete_value(self, key):
        return self.redis_conn.delete(key)


def parse_dict_input(input_str):
    try:
        return dict(item.split('=') for item in input_str.split(','))
    except ValueError:
        raise ValueError("Invalid dictionary format. Ensure you use key=value pairs separated by commas.")

def main():
    client = RedisClient()

    while True:
        print("\nRedis CLI Menu:")
        print("1. Set string value")
        print("2. Get string value")
        print("3. Set dictionary value")
        print("4. Get dictionary value")
        print("5. Set string value with expiry")
        print("6. Set dictionary value with expiry")
        print("7. Delete value")
        print("8. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            key = input("Enter key: ")
            value = input("Enter value: ")
            print("Set result:", client.redis_set_value(key, value))

        elif choice == '2':
            key = input("Enter key: ")
            print("Value:", client.redis_get_value(key))

        elif choice == '3':
            key = input("Enter key: ")
            value = input("Enter dictionary (e.g., key1=value1,key2=value2): ")
            try:
                value_dict = parse_dict_input(value)
                print("Set result:", client.redis_set_dict_value(key, value_dict))
            except ValueError as e:
                print(e)

        elif choice == '4':
            key = input("Enter key: ")
            try:
                print("Dictionary:", client.redis_get_dict_value(key))
            except TypeError as e:
                print(e)

        elif choice == '5':
            key = input("Enter key: ")
            value = input("Enter value: ")
            expiry = int(input("Enter expiry time in seconds: "))
            print("Set result:", client.redis_set_value_and_expiry(key, value, expiry))

        elif choice == '6':
            key = input("Enter key: ")
            value = input("Enter dictionary (e.g., key1=value1,key2=value2): ")
            expiry = int(input("Enter expiry time in seconds: "))
            try:
                value_dict = parse_dict_input(value)
                print("Set result:", client.redis_set_dict_value_and_expiry(key, value_dict, expiry))
            except ValueError as e:
                print(e)

        elif choice == '7':
            key = input("Enter key: ")
            print("Delete result:", client.redis_delete_value(key))

        elif choice == '8':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please select a valid option.")

if __name__ == "__main__":
    main()
