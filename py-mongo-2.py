import time
import threading
import pymongo
from pymongo import MongoClient
from faker import Faker

fake = Faker()
client = MongoClient('mongodb://localhost:27017/')
db = client['workerdatabase']
collection = db['workers']

def insert_data(user_id, email, name, position):
    collection.insert_one({
        'user_id': user_id,
        'email': email,
        'name': name,
        'position': position
    })

def generate_fake_data():
    return {
        'user_id': fake.uuid4(),
        'email': fake.email(),
        'name': fake.name(),
        'position': fake.job()
    }

def insert_without_threading(num_records):
    start_time = time.time()
    for _ in range(num_records):
        data = generate_fake_data()
        insert_data(data['user_id'], data['email'], data['name'], data['position'])
    end_time = time.time()
    print(f"Time taken without threading: {end_time - start_time} seconds")


def insert_with_threading(num_records, num_threads):
    start_time = time.time()
    
    def worker():
        while True:
            with lock:
                if not data_queue:
                    break
                data = data_queue.pop()
            insert_data(data['user_id'], data['email'], data['name'], data['position'])
    
    data_queue = [generate_fake_data() for _ in range(num_records)]
    lock = threading.Lock()
    
    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    print(f"Time taken with threading: {end_time - start_time} seconds")

if __name__ == "__main__":
    num_records = int(input("Enter the number of records to insert: "))
    use_threading = input("Use threading? (yes/no): ").strip().lower()
    
    if use_threading == 'yes':
        num_threads = int(8)
        insert_with_threading(num_records, num_threads)
    else:
        insert_without_threading(num_records)
