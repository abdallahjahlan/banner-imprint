from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ORDERS_FILE = 'orders.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
if not os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_order(data):
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
    except:
        orders = []
    orders.append(data)
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return """
    <h1>Banner Imprint Server</h1>
    <p>Server is running!</p>
    <ul>
        <li>POST /api/order - Submit new order</li>
        <li>GET /api/orders - View all orders</li>
        <li>GET /uploads/&lt;filename&gt; - View image</li>
    </ul>
    """

@app.route('/api/order', methods=['POST'])
def create_order():
    try:
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = secure_filename(file.filename)
        filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        phone = request.form.get('phone', '')
        transaction_id = request.form.get('transaction_id', '')

        host = request.host_url.rstrip('/')
        image_url = f"{host}/uploads/{filename}"

        order_data = {
            "id": timestamp,
            "phone": phone,
            "transaction_id": transaction_id,
            "filename": filename,
            "original_filename": original_filename,
            "image_url": image_url,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "new"
        }

        save_order(order_data)

        return jsonify({
            "success": True,
            "message": "Order received successfully!",
            "order": order_data
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)
        return jsonify({"success": True, "orders": orders}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
