import React, { useState, useEffect } from 'react';

const DocumentViewer = ({ refreshTrigger, onDeleteSuccess }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedType, setSelectedType] = useState('MDM');
  const [message, setMessage] = useState('');

  const messageTypes = ['MDM', 'OUL', 'ORU'];

  useEffect(() => {
    loadDocuments();
  }, [selectedType, refreshTrigger]);

  const loadDocuments = async () => {
    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(`/api/documents/${selectedType}?limit=20`);
      const result = await response.json();

      if (result.success) {
        setDocuments(result.documents);
        if (result.documents.length === 0) {
          setMessage(`ℹ️ Nessun documento di tipo ${selectedType} trovato nel database.`);
        }
      } else {
        setMessage(`❌ Errore: ${result.error}`);
        setDocuments([]);
      }
    } catch (error) {
      setMessage(`❌ Errore di rete: ${error.message}`);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm('Sei sicuro di voler eliminare questo documento?')) {
      return;
    }

    try {
      const response = await fetch(`/api/documents/${selectedType}/${documentId}`, {
        method: 'DELETE',
      });

      const result = await response.json();

      if (result.success) {
        setMessage(`✅ Documento eliminato con successo`);
        loadDocuments(); // Ricarica la lista
        if (onDeleteSuccess) {
          onDeleteSuccess();
        }
      } else {
        setMessage(`❌ Errore nell'eliminazione: ${result.message}`);
      }
    } catch (error) {
      setMessage(`❌ Errore di rete: ${error.message}`);
    }
  };

  const getDocumentTitle = (doc) => {
    switch (selectedType) {
      case 'MDM':
        const patientName = doc.patient_identification?.name;
        return `${patientName?.family_name || 'N/A'}, ${patientName?.given_name || 'N/A'}`;
      case 'OUL':
        const labPatientName = doc.patient_identification?.name;
        return `${labPatientName?.family_name || 'N/A'}, ${labPatientName?.given_name || 'N/A'}`;
      case 'ORU':
        const patientId = doc.patient_identification?.identifiers?.[0]?.id_number;
        return `Paziente: ${patientId || 'N/A'}`;
      default:
        return 'Documento';
    }
  };

  const getDocumentSummary = (doc) => {
    switch (selectedType) {
      case 'MDM':
        return {
          'Tipo Documento': doc.document_header?.document_type || 'N/A',
          'Data Attività': doc.document_header?.activity_datetime || 'N/A',
          'Classe Paziente': doc.patient_visit?.patient_class || 'N/A',
          'Sesso': doc.patient_identification?.administrative_sex || 'N/A'
        };
      case 'OUL':
        const specimenCount = doc.specimens?.length || 0;
        const firstSpecimen = doc.specimens?.[0];
        return {
          'Numero Campioni': specimenCount,
          'Tipo Primo Campione': firstSpecimen?.specimen_type?.text || 'N/A',
          'Data Collezione': firstSpecimen?.collection_datetime || 'N/A',
          'Sesso': doc.patient_identification?.administrative_sex || 'N/A'
        };
      case 'ORU':
        const observationCount = doc.observation_report?.[0]?.observations?.length || 0;
        return {
          'Numero Osservazioni': observationCount,
          'Classe Paziente': doc.patient_visit?.patient_class || 'N/A',
          'Sesso': doc.patient_identification?.administrative_sex || 'N/A',
          'Data Nascita': doc.patient_identification?.date_of_birth || 'N/A'
        };
      default:
        return {};
    }
  };

  return (
    <div>
      <div className="card">
        <h2>📋 Visualizzazione Documenti</h2>
        <p>Esplora i documenti HL7 convertiti e salvati nel database MongoDB.</p>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '10px', fontWeight: 'bold' }}>
            Tipo di Messaggio:
          </label>
          {messageTypes.map(type => (
            <button
              key={type}
              className={`nav-button ${selectedType === type ? 'active' : ''}`}
              onClick={() => setSelectedType(type)}
              style={{ marginRight: '10px', marginBottom: '10px' }}
            >
              {type}
            </button>
          ))}
        </div>

        <button 
          className="upload-button" 
          onClick={loadDocuments}
          disabled={loading}
        >
          🔄 Ricarica Documenti
        </button>
      </div>

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : message.includes('ℹ️') ? 'info' : 'error'}`}>
          {message}
        </div>
      )}

      {loading && (
        <div className="loading">
          ⏳ Caricamento documenti...
        </div>
      )}

      <div className="documents-grid">
        {documents.map((doc, index) => (
          <div key={doc._id} className="document-card">
            <div className="document-header">
              <div>
                <span className="document-type">{selectedType}</span>
                <h3 style={{ margin: '10px 0 5px 0' }}>
                  {getDocumentTitle(doc)}
                </h3>
                <small style={{ color: '#666' }}>
                  ID: {doc._id} | 
                  Inserito: {new Date(doc._inserted_at).toLocaleDateString('it-IT')}
                </small>
              </div>
              <button
                className="delete-button"
                onClick={() => deleteDocument(doc._id)}
                title="Elimina documento"
              >
                🗑️ Elimina
              </button>
            </div>

            <div style={{ marginBottom: '15px' }}>
              {Object.entries(getDocumentSummary(doc)).map(([key, value]) => (
                <div key={key} style={{ marginBottom: '5px' }}>
                  <strong>{key}:</strong> {value}
                </div>
              ))}
            </div>

            <details>
              <summary style={{ cursor: 'pointer', fontWeight: 'bold', marginBottom: '10px' }}>
                📄 Visualizza JSON Completo
              </summary>
              <div className="document-content">
                {JSON.stringify(doc, null, 2)}
              </div>
            </details>
          </div>
        ))}
      </div>

      {!loading && documents.length === 0 && !message && (
        <div className="card">
          <p style={{ textAlign: 'center', color: '#666' }}>
            Nessun documento di tipo {selectedType} trovato. 
            Carica alcuni file HL7 per iniziare.
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentViewer;
