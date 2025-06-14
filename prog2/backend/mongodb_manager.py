from pymongo import MongoClient
from datetime import datetime
import json

class MongoDBManager:
    """
    Gestisce la connessione e le operazioni con MongoDB
    """
    
    def __init__(self, connection_string="mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"):
        self.connection_string = connection_string
        self.client = None
        self.db = None
        self.database_name = "DATABASE1"
        
        # Nomi delle collections
        self.collections = {
            "MDM": "mdm_documents",
            "OUL": "oul_lab_results", 
            "ORU": "oru_patient_monitoring"
        }
    
    def connect(self):
        """Stabilisce la connessione a MongoDB"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Test della connessione
            self.client.admin.command('ping')
            print(f"Connesso a MongoDB - Database: {self.database_name}")
            return True
        except Exception as e:
            print(f"Errore di connessione a MongoDB: {e}")
            return False
    
    def disconnect(self):
        """Chiude la connessione a MongoDB"""
        if self.client:
            self.client.close()
            print("Connessione MongoDB chiusa")
    
    def save_document(self, document_data, message_type):
        """
        Salva un documento nella collection appropriata
        """
        if self.db is None:
            raise Exception("Connessione MongoDB non stabilita")
        
        collection_name = self.collections.get(message_type)
        if not collection_name:
            raise Exception(f"Tipo di messaggio non supportato: {message_type}")
        
        collection = self.db[collection_name]
        
        # Aggiungi timestamp di inserimento
        document_data["_inserted_at"] = datetime.utcnow()
        
        try:
            result = collection.insert_one(document_data)
            print(f"Documento salvato in {collection_name} con ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Errore nel salvataggio del documento: {e}")
            raise
    
    def get_all_documents(self, message_type, limit=50):
        """
        Recupera tutti i documenti di un tipo specifico
        """
        if self.db is None:
            raise Exception("Connessione MongoDB non stabilita")
        
        collection_name = self.collections.get(message_type)
        if not collection_name:
            raise Exception(f"Tipo di messaggio non supportato: {message_type}")
        
        collection = self.db[collection_name]
        
        try:
            documents = list(collection.find().limit(limit))
            # Converte ObjectId in stringa per la serializzazione JSON
            for doc in documents:
                doc["_id"] = str(doc["_id"])
            return documents
        except Exception as e:
            print(f"Errore nel recupero dei documenti: {e}")
            raise
    
    def delete_document(self, document_id, message_type):
        """
        Elimina un documento specifico
        """
        if self.db is None:
            raise Exception("Connessione MongoDB non stabilita")
        
        collection_name = self.collections.get(message_type)
        if not collection_name:
            raise Exception(f"Tipo di messaggio non supportato: {message_type}")
        
        collection = self.db[collection_name]
        
        try:
            from bson import ObjectId
            result = collection.delete_one({"_id": ObjectId(document_id)})
            if result.deleted_count > 0:
                print(f"Documento {document_id} eliminato da {collection_name}")
                return True
            else:
                print(f"Documento {document_id} non trovato")
                return False
        except Exception as e:
            print(f"Errore nell'eliminazione del documento: {e}")
            raise
    
    def search_documents(self, message_type, search_criteria, limit=50):
        """
        Cerca documenti basandosi su criteri specifici
        """
        if self.db is None:
            raise Exception("Connessione MongoDB non stabilita")
        
        collection_name = self.collections.get(message_type)
        if not collection_name:
            raise Exception(f"Tipo di messaggio non supportato: {message_type}")
        
        collection = self.db[collection_name]
        
        try:
            # Costruisce la query MongoDB
            query = {}
            
            # Esempi di ricerca per diversi tipi di messaggio
            if message_type == "MDM":
                if "patient_id" in search_criteria:
                    query["patient_identification.identifiers.id_number"] = {
                        "$regex": search_criteria["patient_id"], "$options": "i"
                    }
                if "document_type" in search_criteria:
                    query["document_header.document_type"] = {
                        "$regex": search_criteria["document_type"], "$options": "i"
                    }
            
            elif message_type == "OUL":
                if "patient_id" in search_criteria:
                    query["patient_identification.identifiers.id_number"] = {
                        "$regex": search_criteria["patient_id"], "$options": "i"
                    }
                if "test_name" in search_criteria:
                    query["specimens.observation_requests.universal_service_identifier.text"] = {
                        "$regex": search_criteria["test_name"], "$options": "i"
                    }
            
            elif message_type == "ORU":
                if "patient_id" in search_criteria:
                    query["patient_identification.identifiers.id_number"] = {
                        "$regex": search_criteria["patient_id"], "$options": "i"
                    }
                if "observation_type" in search_criteria:
                    query["observation_report.observations.observation_identifier.identifier"] = {
                        "$regex": search_criteria["observation_type"], "$options": "i"
                    }
            
            documents = list(collection.find(query).limit(limit))
            
            # Converte ObjectId in stringa
            for doc in documents:
                doc["_id"] = str(doc["_id"])
            
            return documents
            
        except Exception as e:
            print(f"Errore nella ricerca dei documenti: {e}")
            raise
    
    def get_collection_stats(self):
        """
        Restituisce statistiche sulle collections
        """
        if self.db is None:
            raise Exception("Connessione MongoDB non stabilita")
        
        stats = {}
        for message_type, collection_name in self.collections.items():
            try:
                collection = self.db[collection_name]
                count = collection.count_documents({})
                stats[message_type] = {
                    "collection_name": collection_name,
                    "document_count": count
                }
            except Exception as e:
                stats[message_type] = {
                    "collection_name": collection_name,
                    "document_count": 0,
                    "error": str(e)
                }
        
        return stats
