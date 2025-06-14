#!/usr/bin/env python3
"""
Script di test per il framework HL7
Testa il parsing dei file di esempio e la connessione a MongoDB
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.hl7_parser import HL7Parser
from backend.mongodb_manager import MongoDBManager
import json

def test_parser():
    """Testa il parsing dei file HL7 di esempio"""
    print("🧪 Test del parser HL7...")
    
    parser = HL7Parser()
    test_files = [
        ('datiORB1.txt', 'MDM'),
        ('datiORB2.txt', 'OUL'), 
        ('datiORB3_DOM.txt', 'ORU')
    ]
    
    for filename, expected_type in test_files:
        print(f"\n📄 Testing {filename} (Expected: {expected_type})")
        
        try:
            # Legge il file
            with open(filename, 'r', encoding='utf-8') as f:
                hl7_content = f.read()
            
            # Parse del contenuto
            parsed_data = parser.parse_hl7_message(hl7_content)
            actual_type = parsed_data.get('message_metadata', {}).get('type', '')
            
            print(f"✅ Parsed successfully!")
            print(f"   Tipo rilevato: {actual_type}")
            print(f"   Match expected: {'✅' if actual_type == expected_type else '❌'}")
            
            # Mostra alcune informazioni chiave
            if actual_type == 'MDM':
                patient_name = parsed_data.get('patient_identification', {}).get('name', {})
                print(f"   Paziente: {patient_name.get('family_name', 'N/A')}")
            elif actual_type == 'OUL':
                specimens = parsed_data.get('specimens', [])
                print(f"   Campioni: {len(specimens)}")
            elif actual_type == 'ORU':
                observations = parsed_data.get('observation_report', [])
                if observations:
                    obs_count = len(observations[0].get('observations', []))
                    print(f"   Osservazioni: {obs_count}")
            
        except Exception as e:
            print(f"❌ Errore nel parsing di {filename}: {e}")

def test_mongodb():
    """Testa la connessione a MongoDB"""
    print("\n🗄️ Test connessione MongoDB...")
    
    mongo = MongoDBManager()
    
    try:
        if mongo.connect():
            print("✅ Connessione MongoDB riuscita!")
            
            # Test statistiche
            stats = mongo.get_collection_stats()
            print(f"📊 Statistiche database:")
            for msg_type, stat in stats.items():
                print(f"   {msg_type}: {stat['document_count']} documenti")
            
            mongo.disconnect()
        else:
            print("❌ Connessione MongoDB fallita!")
            
    except Exception as e:
        print(f"❌ Errore MongoDB: {e}")

def test_integration():
    """Test di integrazione completo"""
    print("\n🔄 Test di integrazione...")
    
    parser = HL7Parser()
    mongo = MongoDBManager()
    
    try:
        if not mongo.connect():
            print("❌ Impossibile connettersi a MongoDB per il test di integrazione")
            return
        
        # Test con datiORB1.txt (MDM)
        print("📄 Test parsing + salvataggio MDM...")
        with open('datiORB1.txt', 'r', encoding='utf-8') as f:
            hl7_content = f.read()
        
        parsed_data = parser.parse_hl7_message(hl7_content)
        message_type = parsed_data.get('message_metadata', {}).get('type', '')
        
        # Aggiungi un flag di test per non confondere con dati reali
        parsed_data['_test_document'] = {'flag': True}
        
        document_id = mongo.save_document(parsed_data, message_type)
        print(f"✅ Documento test salvato con ID: {document_id}")
        
        # Prova a recuperarlo
        documents = mongo.get_all_documents(message_type, limit=1)
        if documents:
            print(f"✅ Documento recuperato dal database")
        
        # Elimina il documento di test
        if mongo.delete_document(document_id, message_type):
            print(f"✅ Documento test eliminato")
        
        mongo.disconnect()
        
    except Exception as e:
        print(f"❌ Errore nel test di integrazione: {e}")

def main():
    """Esegue tutti i test"""
    print("🧪 HL7 Framework - Suite di Test")
    print("=" * 50)
    
    # Verifica che i file di esempio esistano
    required_files = ['datiORB1.txt', 'datiORB2.txt', 'datiORB3_DOM.txt']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ File mancanti: {', '.join(missing_files)}")
        print("   Assicurati di eseguire lo script dalla directory principale del progetto")
        return
    
    # Esegui i test
    test_parser()
    test_mongodb()
    test_integration()
    
    print("\n🎉 Test completati!")
    print("\n💡 Per avviare il framework completo:")
    print("   Windows: start.bat")
    print("   Linux/Mac: ./start.sh")

if __name__ == "__main__":
    main()
