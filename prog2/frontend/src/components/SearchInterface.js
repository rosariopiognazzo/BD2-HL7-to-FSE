import React, { useState } from 'react';

const SearchInterface = () => {
  const [selectedType, setSelectedType] = useState('MDM');
  const [searchCriteria, setSearchCriteria] = useState({});
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const messageTypes = ['MDM', 'OUL', 'ORU'];

  const searchFields = {
    MDM: [
      { key: 'patient_id', label: 'ID Paziente', placeholder: 'Es: 1721260' },
      { key: 'document_type', label: 'Tipo Documento', placeholder: 'Es: ZZZ' }
    ],
    OUL: [
      { key: 'patient_id', label: 'ID Paziente', placeholder: 'Es: 383378' },
      { key: 'test_name', label: 'Nome Test', placeholder: 'Es: POTASSIO' }
    ],
    ORU: [
      { key: 'patient_id', label: 'ID Paziente', placeholder: 'Es: ttttt' },
      { key: 'observation_type', label: 'Tipo Osservazione', placeholder: 'Es: HR, SpO2' }
    ]
  };

  const handleInputChange = (field, value) => {
    setSearchCriteria(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSearch = async () => {
    // Rimuovi campi vuoti
    const cleanedCriteria = Object.fromEntries(
      Object.entries(searchCriteria).filter(([key, value]) => value && value.trim() !== '')
    );

    if (Object.keys(cleanedCriteria).length === 0) {
      setMessage('⚠️ Inserisci almeno un criterio di ricerca');
      return;
    }

    setLoading(true);
    setMessage('');
    setSearchResults([]);

    try {
      const response = await fetch(`/api/search/${selectedType}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanedCriteria),
      });

      const result = await response.json();

      if (result.success) {
        setSearchResults(result.documents);
        if (result.documents.length === 0) {
          setMessage('ℹ️ Nessun documento trovato con i criteri specificati');
        } else {
          setMessage(`✅ Trovati ${result.documents.length} documenti`);
        }
      } else {
        setMessage(`❌ Errore nella ricerca: ${result.error}`);
      }
    } catch (error) {
      setMessage(`❌ Errore di rete: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchCriteria({});
    setSearchResults([]);
    setMessage('');
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

  const getHighlightedContent = (doc) => {
    switch (selectedType) {
      case 'MDM':
        return {
          'ID Paziente': doc.patient_identification?.identifiers?.[0]?.id_number || 'N/A',
          'Tipo Documento': doc.document_header?.document_type || 'N/A',
          'Data Documento': doc.document_header?.activity_datetime || 'N/A',
          'Nome File': doc.document_header?.unique_document_filename || 'N/A'
        };
      case 'OUL':
        const firstSpecimen = doc.specimens?.[0];
        const firstTest = firstSpecimen?.observation_requests?.[0];
        return {
          'ID Paziente': doc.patient_identification?.identifiers?.[0]?.id_number || 'N/A',
          'Tipo Campione': firstSpecimen?.specimen_type?.text || 'N/A',
          'Primo Test': firstTest?.universal_service_identifier?.text || 'N/A',
          'Data Collezione': firstSpecimen?.collection_datetime || 'N/A'
        };
      case 'ORU':
        const firstObs = doc.observation_report?.[0]?.observations?.[0];
        return {
          'ID Paziente': doc.patient_identification?.identifiers?.[0]?.id_number || 'N/A',
          'Prima Osservazione': firstObs?.observation_identifier?.identifier || 'N/A',
          'Valore': firstObs?.observation_value || 'N/A',
          'Unità': firstObs?.units || 'N/A'
        };
      default:
        return {};
    }
  };

  return (
    <div>
      <div className="card">
        <h2>🔍 Ricerca Documenti</h2>
        <p>Cerca documenti specifici nel database utilizzando diversi criteri di ricerca.</p>

        {/* Selezione tipo messaggio */}
        <div style={{ marginBottom: '20px' }}>
          <label style={{ marginRight: '10px', fontWeight: 'bold' }}>
            Tipo di Messaggio:
          </label>
          {messageTypes.map(type => (
            <button
              key={type}
              className={`nav-button ${selectedType === type ? 'active' : ''}`}
              onClick={() => {
                setSelectedType(type);
                clearSearch();
              }}
              style={{ marginRight: '10px', marginBottom: '10px' }}
            >
              {type}
            </button>
          ))}
        </div>

        {/* Form di ricerca */}
        <div className="search-form">
          {searchFields[selectedType].map(field => (
            <div key={field.key} className="form-group">
              <label>{field.label}:</label>
              <input
                type="text"
                className="form-input"
                placeholder={field.placeholder}
                value={searchCriteria[field.key] || ''}
                onChange={(e) => handleInputChange(field.key, e.target.value)}
              />
            </div>
          ))}
          
          <button
            className="search-button"
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? '⏳ Cercando...' : '🔍 Cerca'}
          </button>
          
          <button
            className="nav-button"
            onClick={clearSearch}
            style={{ backgroundColor: '#95a5a6' }}
          >
            🧹 Pulisci
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${
          message.includes('✅') ? 'success' : 
          message.includes('ℹ️') ? 'info' : 
          'error'
        }`}>
          {message}
        </div>
      )}

      {/* Risultati della ricerca */}
      {searchResults.length > 0 && (
        <div className="documents-grid">
          {searchResults.map((doc, index) => (
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
              </div>

              <div style={{ marginBottom: '15px' }}>
                {Object.entries(getHighlightedContent(doc)).map(([key, value]) => (
                  <div key={key} style={{ marginBottom: '5px' }}>
                    <strong>{key}:</strong> 
                    <span style={{ 
                      backgroundColor: Object.values(searchCriteria).some(criteria => 
                        criteria && value.toLowerCase().includes(criteria.toLowerCase())
                      ) ? '#fff3cd' : 'transparent',
                      padding: '0 4px',
                      borderRadius: '2px'
                    }}>
                      {value}
                    </span>
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
      )}
    </div>
  );
};

export default SearchInterface;
