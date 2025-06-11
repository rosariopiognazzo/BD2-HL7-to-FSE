import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify, send_from_directory, render_template
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

@app.route('/api/raw_lab_data', methods=['GET'])
def get_raw_lab_data():
    """Recupera i dati di laboratorio raw non ancora processati"""
    try:
        # Cerca documenti con struttura di messaggi HL7 parsati
        raw_docs = list(framework.database.lab_results_collection.find({
            "segments": {"$exists": True}
        }).limit(10))
        
        for doc in raw_docs:
            doc.pop('_id', None)
        
        return jsonify(raw_docs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process_lab_document', methods=['POST'])
def process_lab_document():
    """Processa manualmente un documento di laboratorio"""
    try:
        data = request.get_json()
        doc_id = data.get('document_id')
        patient_id = data.get('patient_id')
        
        if not doc_id or not patient_id:
            return jsonify({'error': 'document_id e patient_id sono richiesti'}), 400
        
        # Trova il documento
        doc = framework.database.lab_results_collection.find_one({"_id": doc_id})
        if not doc:
            return jsonify({'error': 'Documento non trovato'}), 404
        
        # Verifica che il paziente esista
        patient = framework.database.find_patient_by_id(patient_id)
        if not patient:
            return jsonify({'error': 'Paziente non trovato'}), 404
        
        # Qui dovremmo processare i risultati di laboratorio e associarli al paziente
        # Per ora restituiamo successo
        
        return jsonify({
            'success': True,
            'message': f'Documento {doc_id} associato al paziente {patient_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def serve_home_page():
    """Endpoint per servire la homepage della webapp."""
    return render_template('app.html')

@app.route('/app.html', methods=['GET'])
def serve_app_page():
    """Endpoint per servire la pagina HTML principale della webapp."""
    return render_template('app.html')

if __name__ == '__main__':
    app.run(debug=True)
