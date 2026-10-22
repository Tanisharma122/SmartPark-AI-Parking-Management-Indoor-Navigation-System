import os
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

from parking_logic import analyze_parking_image  # you will edit this

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
RESULTS_FOLDER = os.path.join(BASE_DIR, 'static', 'results')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULTS_FOLDER'] = RESULTS_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- UI PAGE ----------
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# ---------- API: ANALYZE IMAGE ----------
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)

        # Call your parking logic (this will also save annotated image)
        result = analyze_parking_image(upload_path, app.config['RESULTS_FOLDER'])

        # Build full URL for frontend <img>
        annotated_rel = result['annotated_filename']   # e.g. 'annotated_img_1.png'
        image_url = url_for('static', filename=f'results/{annotated_rel}')

        response = {
            "image_url": image_url,
            "total_slots": result["total_slots"],
            "free_slots": result["free_slots"],
            "occupied_slots": result["occupied_slots"],
            "slots": result["slots"]
        }
        return jsonify(response)

    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == "__main__":
    app.run(debug=True)
