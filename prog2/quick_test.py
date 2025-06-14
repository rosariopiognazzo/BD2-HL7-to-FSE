#!/usr/bin/env python3
"""
Quick test script per verificare il parsing dei file HL7 di esempio
"""

import os
import sys

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

try:
    from backend.hl7_parser import HL7Parser
    import json
    
    def quick_test():
        print("🧪 Quick Test HL7 Parser")
        print("=" * 40)
        
        parser = HL7Parser()
        
        # Test files in current directory
        test_files = [
            ('datiORB1.txt', 'MDM - Medical Document Management'),
            ('datiORB2.txt', 'OUL - Laboratory Results'),
            ('datiORB3_DOM.txt', 'ORU - Patient Monitoring')
        ]
        
        for filename, description in test_files:
            print(f"\n📄 {filename} ({description})")
            print("-" * 50)
            
            if not os.path.exists(filename):
                print(f"❌ File {filename} non trovato")
                continue
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse HL7
                result = parser.parse_hl7_message(content)
                
                # Extract key info
                msg_type = result.get('message_metadata', {}).get('type', 'Unknown')
                print(f"✅ Tipo messaggio: {msg_type}")
                
                # Show specific info based on type
                if msg_type == 'MDM':
                    patient = result.get('patient_identification', {})
                    name = patient.get('name', {})
                    print(f"👤 Paziente: {name.get('family_name', 'N/A')}, {name.get('given_name', 'N/A')}")
                    doc_type = result.get('document_header', {}).get('document_type', 'N/A')
                    print(f"📄 Tipo documento: {doc_type}")
                
                elif msg_type == 'OUL':
                    patient = result.get('patient_identification', {})
                    specimens = result.get('specimens', [])
                    print(f"🧪 Numero campioni: {len(specimens)}")
                    if specimens:
                        spec_type = specimens[0].get('specimen_type', {}).get('text', 'N/A')
                        print(f"🧪 Primo campione: {spec_type}")
                
                elif msg_type == 'ORU':
                    patient = result.get('patient_identification', {})
                    obs_reports = result.get('observation_report', [])
                    if obs_reports:
                        observations = obs_reports[0].get('observations', [])
                        print(f"📊 Numero osservazioni: {len(observations)}")
                        if observations:
                            first_obs = observations[0].get('observation_identifier', {})
                            print(f"📊 Prima osservazione: {first_obs.get('identifier', 'N/A')}")
                
                print(f"✅ Parsing completato con successo!")
                
            except Exception as e:
                print(f"❌ Errore: {e}")
        
        print(f"\n🎉 Test completato!")
        print(f"\n💡 Per il test completo (incluso MongoDB):")
        print(f"   python test_framework.py")
    
    if __name__ == "__main__":
        quick_test()

except ImportError as e:
    print(f"❌ Errore import: {e}")
    print(f"💡 Installa le dipendenze con:")
    print(f"   cd backend && pip install -r requirements.txt")
