from flask import Flask, request, jsonify, render_template, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import torch
from functools import wraps
import base64  # For encoding and decoding fingerprint data
import os
from flask_cors import CORS
 # Enable CORS for all routes
app = Flask(__name__)
CORS(app)

# Configurations
app.config['MONGO_URI'] = "mongodb://localhost:27017/nandydb"
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# MongoDB Setup
mongo = PyMongo(app)
users_collection = mongo.db.users
resumes_collection = mongo.db.resume

  # Suppresses INFO and WARNING logs

# Helper function to verify token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = users_collection.find_one({'_id': data['user_id']})
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Routes
def select_action():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data received'}), 400

        action = data.get('action')

        if action == 'signup':
            return jsonify({'message': 'Redirecting to signup page...', 'redirect': '/signup'}), 200
        elif action == 'login':
            return jsonify({'message': 'Redirecting to login page...', 'redirect': '/login'}), 200
        else:
            return jsonify({'message': 'Invalid action. Please choose either signup or login.'}), 400
    except Exception as e:
        print(f"Error processing action selection: {e}")
        return jsonify({'message': 'An error occurred during action selection'}), 500
    
@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()  # Get user details and fingerprint data as JSON

        if not data:
            return jsonify({'message': 'No data received'}), 400

        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        if not name or not email or not phone or not password:
            return jsonify({'message': 'All fields, including fingerprint, are required!'}), 400
    

        # Check if the email is already registered
        if users_collection.find_one({'email': email}):
            return jsonify({'message': 'Email already exists!'}), 400

        # Insert the user record into the database
        users_collection.insert_one({
            'name': name,
            'email': email,
            'phone': phone,
            'password': password
        })

        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        print(f"Error processing signup: {e}")
        return jsonify({'message': 'An error occurred during signup'}), 500

@app.route('/register_fingerprint', methods=['POST'])
def register_fingerprint():
    try:
        data = request.get_json()  # Get fingerprint data as JSON
        fingerprint = data.get('fingerprint_data')

        if not fingerprint:
            return jsonify({'message': 'Fingerprint data is required!'}), 400

        # Encode the fingerprint
        encoded_fingerprint = base64.b64encode(fingerprint.encode('utf-8')).decode('utf-8')

        # Check if the encoded fingerprint already exists
        if users_collection.find_one({'fingerprint': encoded_fingerprint}):
            return jsonify({'message': 'Fingerprint already registered!'}), 400

        # Temporarily store the encoded fingerprint (if required for a different use case)
        users_collection.insert_one({'fingerprint': encoded_fingerprint})

        return jsonify({
            'message': 'Fingerprint registered successfully!',
            'fingerprint': encoded_fingerprint
        }), 200
    except Exception as e:
        print(f"Error in registering fingerprint: {e}")
        return jsonify({'message': 'An error occurred while registering fingerprint'}), 500

# 2. Login with Fingerprint Biometrics
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Get fingerprint from request
    fingerprint_data = data.get('fingerprint_data')
    if not fingerprint_data:
        return jsonify({'message': 'Fingerprint data is required!'}), 400

    # Encode the fingerprint to match the stored format
    fingerprint_encoded = base64.b64encode(fingerprint_data.encode('utf-8')).decode('utf-8')

    # Search for the user in MongoDB with the matching fingerprint
    user = users_collection.find_one({'fingerprint': fingerprint_encoded})

    if not user:
        return jsonify({'message': 'Fingerprint does not match any user!'}), 401

    # Fingerprint matches; proceed to dashboard (or return success response)
    return jsonify({'message': 'Login successful! Proceed to dashboard.', 'user_id': str(user['_id'])}), 200


# 5. Home Screen (Dynamic User Info)
@app.route('/home', methods=['GET'])
@token_required
def home(current_user):
    return jsonify({'welcome_message': f"Welcome, {current_user['full_name']}!"})

# 6. Dashboard
@app.route('/dashboard', methods=['GET'])
@token_required
def dashboard(current_user):
    return jsonify({
        'profile': {
            'name': current_user['full_name'],
            'email': current_user['email'],
        }
    })

# 7. Profile Management
@app.route('/profile', methods=['POST'])
@token_required
def update_profile(current_user):
    data = request.json
    users_collection.update_one({'_id': current_user['_id']}, {'$set': data})
    return jsonify({'message': 'Profile updated successfully!'}), 200

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
from openai import OpenAI
import os
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai = OpenAI(api_key=OPENAI_API_KEY)

def generate_id():
    return uuid.uuid4().hex[:8]

def chatgpt_function(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.6,
        max_tokens=250,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1
    )
    return response.choices[0].text.strip()

database = []

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/resume/create', methods=['POST'])
def create_resume():
    if 'headshotImage' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['headshotImage']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    full_name = request.form['fullName']
    current_position = request.form['currentPosition']
    current_length = request.form['currentLength']
    current_technologies = request.form['currentTechnologies']
    work_history = json.loads(request.form['workHistory'])

    new_entry = {
        "id": generate_id(),
        "fullName": full_name,
        "image_url": f"http://localhost:4000/uploads/{filename}",
        "currentPosition": current_position,
        "currentLength": current_length,
        "currentTechnologies": current_technologies,
        "workHistory": work_history
    }

    prompt1 = (
        f"I am writing a resume, my details are \n name: {full_name} \n role: {current_position} ({current_length} years). "
        f"\n I write in the technologies: {current_technologies}. Can you write a 100 words description for the top of the resume(first person writing)?"
    )

    prompt2 = (
        f"I am writing a resume, my details are \n name: {full_name} \n role: {current_position} ({current_length} years). "
        f"\n I write in the technologies: {current_technologies}. Can you write 10 points for a resume on what I am good at?"
    )

    def remainder_text():
        return " ".join([
            f"{item['name']} as a {item['position']}"
            for item in work_history
        ])

    prompt3 = (
        f"I am writing a resume, my details are \n name: {full_name} \n role: {current_position} ({current_length} years). "
        f"\n During my years I worked at {len(work_history)} companies. {remainder_text()} "
        f"\n Can you write me 50 words for each company separated in numbers of my succession in the company (in first person)?"
    )

    objective = chatgpt_function(prompt1)
    keypoints = chatgpt_function(prompt2)
    job_responsibilities = chatgpt_function(prompt3)

    chatgpt_data = {
        "objective": objective,
        "keypoints": keypoints,
        "jobResponsibilities": job_responsibilities
    }

    data = {**new_entry, **chatgpt_data}
    database.append(data)

    return jsonify({
        "message": "Request successful!",
        "data": data
    })

if __name__ == '__main__':
    app.run(port=4000, debug=True)

# 10. Settings
@app.route('/settings/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.json
    new_password = generate_password_hash(data['new_password'], method='sha256')

    users_collection.update_one({'_id': current_user['_id']}, {'$set': {'password': new_password}})
    return jsonify({'message': 'Password updated successfully!'}), 200

@app.route('/settings/delete-account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    users_collection.delete_one({'_id': current_user['_id']})
    return jsonify({'message': 'Account deleted successfully!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
