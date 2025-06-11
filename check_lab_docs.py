from pymongo import MongoClient

client = MongoClient('mongodb+srv://rosariopiognazzo:MO22HSgdEdNdh2fF@cluster0.vim0kda.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['fse_database']

# Lista tutte le collezioni
collections = db.list_collection_names()
print(f'Collezioni nel database fse_database: {collections}')

for collection_name in collections:
    collection = db[collection_name]
    count = collection.count_documents({})
    print(f'\nCollezione {collection_name}: {count} documenti')
    
    if count > 0:
        # Mostra un documento di esempio
        sample_doc = collection.find_one()
        print(f'  Esempio documento keys: {list(sample_doc.keys())[:10]}')
        
        # Se ha segments, è probabilmente il nostro documento
        if 'segments' in sample_doc:
            print(f'  *** TROVATO DOCUMENTO RAW in {collection_name}! ***')
            print(f'  ID: {sample_doc.get("_id")}, MessageType: {sample_doc.get("messageType")}')
