from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt, set_access_cookies, unset_jwt_cookies, get_jwt_identity
from datetime import datetime, timedelta
import os
import re

app = Flask(__name__)
app.config['MONGO_URI'] = 'mongodb://localhost:27017/Prime_Video'
app.config['JWT_SECRET_KEY'] = 'a9574f2e-8bf2-4a09-aec8-b3562025002c'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['UPLOAD_FOLDER'] = 'uploads/'

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# 1. Admin Signup
@app.route('/api/admin/signup', methods=['POST'])
def admin_signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    token = data.get('token') 

    if token != admin_access_token:
        return jsonify({"message": "Invalid admin access token"}), 403

    if mongo.db.users.find_one({'email': email}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    mongo.db.users.insert_one({
        'email': email,
        'password_hash': hashed_password,
        'name': name,
        'user_type': 'admin',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    })
    
    return jsonify({"message": "Admin registered successfully"}), 201


# 2. Admin Login
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = mongo.db.users.find_one({'email': email})
    
    if not user or not bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({"message": "Invalid email or password"}), 401

    if user.get('user_type') != 'admin':
        return jsonify({"message": "Access restricted to admins"}), 403

    token = create_access_token(identity=email)
    return jsonify({"token": token, "email": email}), 200


# 3. Upload Video Content (Admin Only)
@app.route('/api/upload/content', methods=['POST'])
@jwt_required()
def add_content():
    current_email = get_jwt_identity()
    
    user = mongo.db.users.find_one({'email': current_email})
    
    if not user or user.get('user_type') != 'admin':
        return jsonify({"message": "Access restricted to admins"}), 403

    data = request.json
    title = data.get('title')
    description = data.get('description')
    genre = data.get('genre')
    content_type = data.get('type')
    duration = data.get('duration')

    video_id = mongo.db.videos.count_documents({}) + 1 
    
    mongo.db.videos.insert_one({
        'video_id': video_id,
        'title': title,
        'description': description,
        'genre': genre,
        'duration': data.get('duration'),
        'content_type': content_type,
        'duration' : duration,
        'ratings': {
            'average_rating': 0,
            'total_ratings': 0
        },
        'uploader_email': current_email, 
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    })

    return jsonify({"message": "Content added successfully"}), 201


# 4. Get Content Details
@app.route('/api/get/content/', methods=['GET'])
def get_content():
    contents = mongo.db.videos.find()
    
    if not contents:
        return jsonify({"message": "Content not found"}), 404

    content_list = []
    
    for content in contents:
        content['_id'] = str(content['_id'])
        content_list.append(content)

    return jsonify(content_list), 200


# 5. Update Content
@app.route('/api/update/content/<int:content_id>', methods=['PUT'])
@jwt_required()
def update_content(content_id):
    current_email = get_jwt_identity()
    
    user = mongo.db.users.find_one({'email': current_email})
    
    if not user or user.get('user_type') != 'admin':
        return jsonify({"message": "Access restricted to admins"}), 403
    
    data = request.get_json()
    content = mongo.db.videos.find_one({'video_id': content_id})
    
    if not content:
        return jsonify({"message": "Content not found"}), 404

    mongo.db.videos.update_one({'video_id': content_id}, {'$set': data})

    return jsonify({"message": "Content updated successfully"}), 200


# 6. Delete Content
@app.route('/api/content/delete/<int:video_id>', methods=['DELETE'])
@jwt_required()
def delete_content(video_id):
    current_email = get_jwt_identity()
    user = mongo.db.users.find_one({'email': current_email})
    
    if not user or user.get('user_type') != 'admin':
        return jsonify({"message": "Access restricted to admins"}), 403
    
    result = mongo.db.videos.delete_one({'video_id': video_id})
    
    if result.deleted_count == 0:
        return jsonify({"message": "Content not found"}), 404

    return jsonify({"message": "Content deleted successfully"}), 200


# 7. User Signup
@app.route('/api/signup', methods=['POST'])
def user_signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    if mongo.db.users.find_one({'email': email}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    mongo.db.users.insert_one({
        'email': email,
        'password_hash': hashed_password,
        'phone' : phone,
        'name': name,
        'user_type': 'user',  
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    })
    
    return jsonify({"message": "User registered successfully"}), 201


# 8. User Login
@app.route('/api/login', methods=['POST'])
def user_login():
    try :
        data = request.get_json()
        identifier = data.get('identifier')
        password = data.get('password')

        user = mongo.db.users.find_one({
            '$or': [
                {'email': identifier},
                {'phone': identifier}
            ]
        })
        
        if not user or not bcrypt.check_password_hash(user['password_hash'], password):
            return jsonify({"message": "Invalid email/phone or password"}), 401

        token = create_access_token(identity=user['email'])
        return jsonify({"token": token, "email": user['email']}), 200
    except Exception as e:
        return jsonify({'Error' : str(e)})


# 9. Get User Profile
@app.route('/api/users/get/', methods=['GET'])
@jwt_required()
def get_user_profile():
    data = request.json
    email = data.get('email')
    user = mongo.db.users.find_one({'email': email})
    
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "username": user['name'],
        "email": user['email'],
        "phone": user.get('phone', '')
    }), 200


# 10. Update User Profile
@app.route('/api/users/update/', methods=['PUT'])
@jwt_required()
def update_user_profile():
    data = request.json
    email = data.get('email')
    user = mongo.db.users.find_one({'email': email})
    
    if not user:
        return jsonify({"message": "User not found"}), 404

    if 'name' in data:
        mongo.db.users.update_one({'email': email}, {'$set': {'name': data['name']}})
    if 'phone' in data:
        mongo.db.users.update_one({'email': email}, {'$set': {'phone': data['phone']}})
    if 'password' in data:
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        mongo.db.users.update_one({'email': email}, {'$set': {'password_hash': hashed_password}})

    return jsonify({"message": "Profile updated successfully"}), 200


# 11. Search Videos
@app.route('/api/search/', methods=['POST'])
def search_videos():
    data = request.get_json()
    query = data.get('query')

    if not query:
        return jsonify({"message": "Query parameter is required"}), 400

    regex_query = re.compile(query, re.IGNORECASE)

    videos = mongo.db.videos.find({
        'title': regex_query
    })

    result = []
    for video in videos:
        video['_id'] = str(video['_id'])
        result.append({
            "video_id": video.get('video_id', ''),
            "title": video.get('title', ''),
            "description": video.get('description', ''),
            "genre": video.get('genre', '')
        })
    
    return jsonify(result), 200


# 12. Add to Watchlist
@app.route('/api/add/watchlist', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    data = request.get_json()
    email = data.get('email')
    video_id = data.get('video_id')

    mongo.db.watchlist.update_one(
        {'email': email},
        {'$addToSet': {'video_id': video_id}},
        upsert=True
    )

    return jsonify({"message": "Content added to watchlist successfully"}), 200


# 13. Get Watchlist
@app.route('/api/get/watchlist/', methods=['GET'])
@jwt_required()
def get_watchlist():
    data = request.get_json()
    email = data.get('email')
    watchlist = mongo.db.watchlist.find_one({'email': email})
    
    if not watchlist:
        return jsonify({"message": "Watchlist not found"}), 404

    content_ids = watchlist.get('content_ids', [])
    content_details = [mongo.db.videos.find_one({'video_id': content_id}) for content_id in content_ids]

    return jsonify({
        "watchlist": [
            {
                "title": content['title'],
                "description": content['description'],
                "genre": content['genre']
            } for content in content_details if content
        ]
    }), 200


# 14. Remove from Watchlist
@app.route('/api/delete/watchlist', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist():
    data = request.get_json()
    email = data.get('email')
    video_id = data.get('video_id')

    mongo.db.watchlist.update_one(
        {'email': email},
        {'$pull': {'video_id': video_id}}
    )

    return jsonify({"message": "Content removed from watchlist successfully"}), 200

# 15. Rate a Movie
@app.route('/api/ratemovies/<int:video_id>', methods=['POST'])
@jwt_required()
def rate_movie(video_id):
    current_email = get_jwt_identity()
    data = request.get_json()

    video = mongo.db.videos.find_one({'video_id': video_id})
    if not video:
        return jsonify({"message": "Video not found"}), 404

    try:
        rating_value = float(data.get('rating'))
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid rating value. Rating must be a float."}), 400

    if not (1 <= rating_value <= 10):
        return jsonify({"message": "Rating must be between 1 and 10."}), 400

    rating_doc = mongo.db.ratings.find_one({'video_id': video_id})
    if rating_doc:
        existing_rating = next((r for r in rating_doc['ratings'] if r['email'] == current_email), None)
        if existing_rating:
            mongo.db.ratings.update_one(
                {'video_id': video_id, 'ratings.email': current_email},
                {'$set': {'ratings.$.rating': rating_value}}
            )
        else:
            mongo.db.ratings.update_one(
                {'video_id': video_id},
                {'$push': {'ratings': {'email': current_email, 'rating': rating_value}}},
                upsert=True
            )
    else:
        mongo.db.ratings.insert_one({
            'video_id': video_id,
            'title': video.get('title', ''),
            'ratings': [{'email': current_email, 'rating': rating_value}],
            'total_ratings': 1,
            'average_rating': rating_value
        })

    rating_doc = mongo.db.ratings.find_one({'video_id': video_id})
    if rating_doc:
        total_ratings = len(rating_doc['ratings'])
        average_rating = sum(r['rating'] for r in rating_doc['ratings']) / total_ratings

        mongo.db.ratings.update_one(
            {'video_id': video_id},
            {'$set': {
                'total_ratings': total_ratings,
                'average_rating': average_rating
            }}
        )

        mongo.db.videos.update_one(
            {'video_id': video_id},
            {'$set': {
                'ratings.total_ratings': total_ratings,
                'ratings.average_rating': average_rating,
                'updated_at': datetime.utcnow()
            }}
        )

    return jsonify({
        "message": "Rating updated successfully",
        "video_id": video_id,
        "user_rating": rating_value,
        "average_rating": average_rating,
        "total_ratings": total_ratings,
        "title" : rating_doc.get('title')
    }), 200


# 16. View ratings of a movie
@jwt_required()
@app.route('/api/get/ratings', methods=['GET'])
def get_ratings():
    data = request.json
    video_id = data.get('video_id')
    rating_doc = mongo.db.ratings.find_one({'video_id': video_id})
    if not rating_doc:
        return jsonify({"message": "No ratings found for this video"}), 404

    response = {
        "video_id": video_id,
        "title": rating_doc.get('title', ''),
        "total_ratings": rating_doc.get('total_ratings', 0),
        "average_rating": rating_doc.get('average_rating', 0),
    }

    return jsonify(response), 200


@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_data):
    jti = jwt_data['jti']
    print(f"Checking blocklist for JTI: {jti}")  # Debugging line
    return mongo.db.blacklist.find_one({'jti': jti}) is not None


# 17. Logout endpoint
@app.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()['jti']  # Get the JWT ID
    mongo.db.blacklist.insert_one({'jti': jti})
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response


if __name__ == '__main__':
    app.run(debug=True)
