from flask import Flask, request, jsonify
import pandas as pd
from pymongo import MongoClient
import os
import time

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['passenger_database']
collection = db['passengers']

@app.route('/upload', methods=['POST'])
def upload_file():
    start_time = time.time()  
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        elapsed_time = time.time() - start_time  
        return jsonify({'error': 'No file path provided', 'elapsed_time': elapsed_time}), 400

    if not os.path.exists(file_path):
        elapsed_time = time.time() - start_time  
        return jsonify({'error': 'File does not exist', 'elapsed_time': elapsed_time}), 400

    if not file_path.endswith('.xlsx'):
        elapsed_time = time.time() - start_time  
        return jsonify({'error': 'Invalid file format. Only .xlsx files are allowed.', 'elapsed_time': elapsed_time}), 400

    try:
        df = pd.read_excel(file_path)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        df = df.dropna(axis=1, how='all')
        data = df.to_dict(orient='records')
        collection.insert_many(data)
        elapsed_time = time.time() - start_time  
        return jsonify({'message': 'File successfully uploaded and data inserted into MongoDB', 'elapsed_time': elapsed_time}), 200
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({'error': 'Unexpected error', 'details': str(e), 'elapsed_time': elapsed_time}), 500

@app.route('/read_data', methods=['GET'])
def read_data():
    start_time = time.time()  
    try:
        passenger_id = request.args.get('PassengerId')
        if not passenger_id:
            elapsed_time = time.time() - start_time  
            return jsonify({'error': 'No PassengerID provided', 'elapsed_time': elapsed_time}), 400
        
        try:
            passenger_id = int(passenger_id)  
        except ValueError:
            elapsed_time = time.time() - start_time  
            return jsonify({'error': 'Invalid PassengerID format', 'elapsed_time': elapsed_time}), 400
        
        document = collection.find_one({'PassengerId': passenger_id})
        elapsed_time = time.time() - start_time  

        if document:
            document['_id'] = str(document['_id'])
            return jsonify(document | {'elapsed_time': elapsed_time})
        else:
            return jsonify({'error': 'Passenger not found', 'elapsed_time': elapsed_time}), 404
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({'error': 'Unexpected error', 'details': str(e), 'elapsed_time': elapsed_time}), 500

@app.route('/update_data', methods=['PUT'])
def update_data():
    start_time = time.time()
    try:
        passenger_id = request.args.get('PassengerId')
        if not passenger_id:
            elapsed_time = time.time() - start_time  
            return jsonify({'error': 'No PassengerID provided', 'elapsed_time': elapsed_time}), 400
        
        try:
            passenger_id = int(passenger_id)  
        except ValueError:
            elapsed_time = time.time() - start_time  
            return jsonify({'error': 'Invalid PassengerID format', 'elapsed_time': elapsed_time}), 400
        
        if not request.json:
            elapsed_time = time.time() - start_time  
            return jsonify({'error': 'No data provided', 'elapsed_time': elapsed_time}), 400

        update_data = request.json
        result = collection.update_one({'PassengerId': passenger_id}, {'$set': update_data})
        elapsed_time = time.time() - start_time

        if result.matched_count:
            return jsonify({'message': 'Record updated successfully', 'elapsed_time': elapsed_time}), 200
        else:
            return jsonify({'error': 'Record not found', 'elapsed_time': elapsed_time}), 404
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({'error': 'Unexpected error', 'details': str(e), 'elapsed_time': elapsed_time}), 500

@app.route('/survived', methods=['POST'])
def survived_count():
    start_time = time.time()
    try:
        payload = request.json
        sex = payload.get('Sex')
        
        if not sex:
            elapsed_time = time.time() - start_time
            return jsonify({'error': 'No Sex provided', 'elapsed_time': elapsed_time}), 400

        if sex not in ['male', 'female']:
            elapsed_time = time.time() - start_time
            return jsonify({'error': 'Invalid Sex value. Must be "male" or "female"', 'elapsed_time': elapsed_time}), 400
        
        count = collection.count_documents({
            'Sex': sex,
            'Survived': 1,  
            'Age': {'$lt': 45}
        })
        
        elapsed_time = time.time() - start_time
        return jsonify({'count': count, 'elapsed_time': elapsed_time}), 200
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({'error': 'Unexpected error', 'details': str(e), 'elapsed_time': elapsed_time}), 500

if __name__ == '__main__':
    app.run(debug=True)
