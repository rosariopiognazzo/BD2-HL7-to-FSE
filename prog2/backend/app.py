from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from bson import ObjectId
from hl7_parser import HL7Parser
from mongodb_manager import MongoDBManager

app = Flask(__name__)
CORS(app)  # Abilita CORS per permettere richieste dal frontend React

# Inizializza i componenti
hl7_parser = HL7Parser()
mongo_manager = MongoDBManager()

# Custom JSON provider per gestire ObjectId (Flask 2.3+)
from flask.json.provider import DefaultJSONProvider

class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json = CustomJSONProvider(app)

# Connetti a MongoDB all'avvio dell'applicazione
if not mongo_manager.connect():
    print("ATTENZIONE: Impossibile connettersi a MongoDB")

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato dell'API"""
    return jsonify({
        "status": "healthy",
        "message": "HL7 Framework API is running"
    })

def serialize_document(doc):
    """Converte ObjectId in string per la serializzazione JSON"""
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, dict):
                doc[key] = serialize_document(value)
            elif isinstance(value, list):
                doc[key] = [serialize_document(item) if isinstance(item, dict) else item for item in value]
    return doc

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nessun file caricato'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nessun file selezionato'}), 400
        
        # Leggi il contenuto del file
        content = file.read().decode('utf-8', errors='ignore')
        
        # Parse del file HL7
        parser = HL7Parser()
        parsed_data = parser.parse_hl7_message(content)
        
        if not parsed_data:
            return jsonify({'error': 'Impossibile processare il file HL7'}), 400
        
        # Determina il tipo di messaggio
        message_metadata = parsed_data.get('message_metadata', {})
        if isinstance(message_metadata, dict):
            message_type_field = message_metadata.get('message_type', '')
        elif isinstance(message_metadata, str):
            message_type_field = message_metadata
        else:
            message_type_field = ''
        
        # Estrai solo il tipo di messaggio (MDM, OUL, ORU)
        if message_type_field.startswith('MDM'):
            message_type = 'MDM'
        elif message_type_field.startswith('OUL'):
            message_type = 'OUL'
        elif message_type_field.startswith('ORU'):
            message_type = 'ORU'
        else:
            return jsonify({'error': f'Tipo di messaggio non supportato: {message_type_field}'}), 400
        
        # Salva nel database - CORREZIONE: parametri nell'ordine giusto
        result = mongo_manager.save_document(parsed_data, message_type)
        
        if result:
            # Serializza il documento per la risposta
            serialized_data = serialize_document(parsed_data.copy())
            return jsonify({
                'message': 'File processato e salvato con successo',
                'document_id': str(result),
                'data': serialized_data
            })
        else:
            return jsonify({'error': 'Errore nel salvare il documento'}), 500
            
    except Exception as e:
        print(f"Errore nell'upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Errore nel processare il file: {str(e)}'}), 500

@app.route('/api/documents/<message_type>', methods=['GET'])
def get_documents(message_type):
    """
    Endpoint per recuperare documenti di un tipo specifico
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        documents = mongo_manager.get_all_documents(message_type.upper(), limit)
        
        return jsonify({
            "success": True,
            "message_type": message_type.upper(),
            "count": len(documents),
            "documents": documents
        })
        
    except Exception as e:
        return jsonify({"error": f"Errore nel recuperare i documenti: {str(e)}"}), 500

@app.route('/api/documents/<message_type>/<document_id>', methods=['DELETE'])
def delete_document(message_type, document_id):
    """
    Endpoint per eliminare un documento specifico
    """
    try:
        success = mongo_manager.delete_document(document_id, message_type.upper())
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Documento {document_id} eliminato con successo"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Documento {document_id} non trovato"
            }), 404
            
    except Exception as e:
        return jsonify({"error": f"Errore nell'eliminazione del documento: {str(e)}"}), 500

@app.route('/api/search/<message_type>', methods=['POST'])
def search_documents(message_type):
    """
    Endpoint per cercare documenti basandosi su criteri specifici
    """
    try:
        search_criteria = request.json
        if not search_criteria:
            return jsonify({"error": "Criteri di ricerca mancanti"}), 400
        
        limit = search_criteria.pop('limit', 50)
        documents = mongo_manager.search_documents(message_type.upper(), search_criteria, limit)
        
        return jsonify({
            "success": True,
            "message_type": message_type.upper(),
            "search_criteria": search_criteria,
            "count": len(documents),
            "documents": documents
        })
        
    except Exception as e:
        return jsonify({"error": f"Errore nella ricerca: {str(e)}"}), 500

@app.route('/api/stats', methods=['GET'])
def get_database_stats():
    """
    Endpoint per ottenere statistiche del database
    """
    try:
        stats = mongo_manager.get_collection_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        return jsonify({"error": f"Errore nel recuperare le statistiche: {str(e)}"}), 500

@app.route('/api/parse-sample', methods=['POST'])
def parse_sample_data():
    """
    Endpoint per testare il parsing con dati di esempio
    """
    try:
        data = request.json
        if not data or 'hl7_content' not in data:
            return jsonify({"error": "Contenuto HL7 mancante"}), 400
        
        hl7_content = data['hl7_content']
        parsed_data = hl7_parser.parse_hl7_message(hl7_content)
        
        return jsonify({
            "success": True,
            "parsed_data": parsed_data
        })
        
    except Exception as e:
        return jsonify({"error": f"Errore nel parsing: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
