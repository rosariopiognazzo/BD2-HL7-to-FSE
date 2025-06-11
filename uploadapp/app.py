from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import json

# Configurazione Flask
app = Flask(__name__)
app.secret_key = 'uploadapp_secret_key'

# Configurazione MongoDB
MONGO_URI = "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "fse_database"
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

@app.route('/upload', methods=['POST'])
def upload_json():
    """Endpoint per caricare file JSON su MongoDB."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'File JSON mancante'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nessun file selezionato'}), 400

    try:
        data = json.load(file)
        collection_name = request.form.get('collection', 'default_collection')
        db[collection_name].insert_one(data)
        return jsonify({'success': True, 'message': f'File caricato nella collezione {collection_name}'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/upload.html', methods=['GET'])
def serve_upload_page():
    """Endpoint per servire la pagina HTML di upload."""
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
