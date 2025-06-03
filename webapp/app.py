import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify, send_from_directory
from hl7_fhir_converter import FSEFramework

# Configurazione Flask
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')

# Configurazione MongoDB Atlas (riusa la stessa del framework)
MONGO_CONN = "mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
framework = FSEFramework(MONGO_CONN)

@app.route('/api/patients', methods=['GET'])
def get_patients():
    query = request.args.get('q', '').strip()
    patients = framework.database.get_all_patients()
    for p in patients:
        p.pop('_id', None)
    if query:
        query_lower = query.lower()
        patients = [p for p in patients if
            any(query_lower in (idn.get('value','').lower()) for idn in p.get('identifier', [])) or
            any(query_lower in (n.get('family','').lower()) for n in p.get('name', [])) or
            any(query_lower in (n.get('given',[""])[0].lower()) for n in p.get('name', []))
        ]
    return jsonify(patients)

@app.route('/api/patient/<pid>', methods=['GET'])
def get_patient(pid):
    patient = framework.database.find_patient_by_id(pid)
    if patient:
        patient.pop('_id', None)
        return jsonify(patient)
    return jsonify({'error': 'Paziente non trovato'}), 404

@app.route('/api/patient/<pid>', methods=['DELETE'])
def delete_patient(pid):
    result = framework.database.patients_collection.delete_one({'id': pid})
    if result.deleted_count:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Paziente non trovato'}), 404

@app.route('/api/hl7', methods=['POST'])
def insert_hl7():
    data = request.get_json()
    hl7_message = data.get('hl7_message', '')
    if not hl7_message.strip():
        return jsonify({'success': False, 'error': 'Messaggio HL7 mancante'}), 400
    result = framework.process_hl7_message(hl7_message)
    return jsonify(result)

@app.route('/api/patient/<pid>/lab_results', methods=['GET'])
def get_lab_results(pid):
    results = list(framework.database.lab_results_collection.find({"subject.reference": f"Patient/{pid}"}))
    for r in results:
        r.pop('_id', None)
    return jsonify(results)

# Serve la SPA su / e su tutte le route non-API
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    if path.startswith('api/'):
        return '', 404
    if path.startswith('static/'):
        return send_from_directory('static', path[len('static/'):])
    # Serve index.html per tutte le altre route (SPA)
    return send_from_directory(os.path.dirname(__file__), 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
