import React from 'react';

const Statistics = ({ stats, onRefresh }) => {
  if (!stats) {
    return (
      <div className="card">
        <h2>📊 Statistiche Database</h2>
        <div className="loading">⏳ Caricamento statistiche...</div>
      </div>
    );
  }

  const totalDocuments = Object.values(stats).reduce((total, stat) => {
    return total + (stat.document_count || 0);
  }, 0);

  const getStatDescription = (messageType) => {
    switch (messageType) {
      case 'MDM':
        return 'Documenti medici e referti';
      case 'OUL':
        return 'Risultati di laboratorio';
      case 'ORU':
        return 'Dati di monitoraggio paziente';
      default:
        return 'Documenti';
    }
  };

  const getStatIcon = (messageType) => {
    switch (messageType) {
      case 'MDM':
        return '📄';
      case 'OUL':
        return '🧪';
      case 'ORU':
        return '📊';
      default:
        return '📋';
    }
  };

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2>📊 Statistiche Database</h2>
          <button className="upload-button" onClick={onRefresh}>
            🔄 Aggiorna
          </button>
        </div>
        <p>Panoramica dei dati memorizzati nel database MongoDB.</p>
      </div>

      {/* Statistiche generali */}
      <div className="card">
        <h3>📈 Riepilogo Generale</h3>
        <div className="stats-grid">
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <div className="stat-number">{totalDocuments}</div>
            <div className="stat-label">Documenti Totali</div>
          </div>
          
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <div className="stat-number">{Object.keys(stats).length}</div>
            <div className="stat-label">Tipi di Messaggio</div>
          </div>
          
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <div className="stat-number">3</div>
            <div className="stat-label">Collections Attive</div>
          </div>
          
          <div className="stat-card" style={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' }}>
            <div className="stat-number">DATABASE1</div>
            <div className="stat-label">Database Nome</div>
          </div>
        </div>
      </div>

      {/* Statistiche per tipo di messaggio */}
      <div className="card">
        <h3>📋 Dettagli per Tipo di Messaggio</h3>
        <div className="documents-grid">
          {Object.entries(stats).map(([messageType, stat]) => (
            <div key={messageType} className="document-card">
              <div className="document-header">
                <div>
                  <span className="document-type">
                    {getStatIcon(messageType)} {messageType}
                  </span>
                  <h4 style={{ margin: '10px 0 5px 0' }}>
                    {getStatDescription(messageType)}
                  </h4>
                </div>
              </div>

              <div style={{ marginBottom: '15px' }}>
                <div style={{ marginBottom: '10px' }}>
                  <strong>Collection:</strong> {stat.collection_name}
                </div>
                
                <div style={{ 
                  fontSize: '2rem', 
                  fontWeight: 'bold', 
                  textAlign: 'center',
                  color: '#2c3e50',
                  marginBottom: '10px'
                }}>
                  {stat.document_count}
                </div>
                
                <div style={{ textAlign: 'center', color: '#7f8c8d' }}>
                  documenti archiviati
                </div>

                {stat.error && (
                  <div style={{ 
                    marginTop: '10px',
                    padding: '10px',
                    backgroundColor: '#fee',
                    border: '1px solid #fcc',
                    borderRadius: '4px',
                    color: '#c00'
                  }}>
                    ⚠️ Errore: {stat.error}
                  </div>
                )}
              </div>

              <div style={{ 
                width: '100%',
                height: '8px',
                backgroundColor: '#ecf0f1',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: totalDocuments > 0 ? `${(stat.document_count / totalDocuments) * 100}%` : '0%',
                  height: '100%',
                  backgroundColor: messageType === 'MDM' ? '#3498db' : 
                                   messageType === 'OUL' ? '#e74c3c' : '#2ecc71',
                  transition: 'width 0.3s ease'
                }}></div>
              </div>
              
              <div style={{ 
                textAlign: 'center', 
                fontSize: '12px', 
                color: '#7f8c8d',
                marginTop: '5px'
              }}>
                {totalDocuments > 0 ? 
                  `${((stat.document_count / totalDocuments) * 100).toFixed(1)}%` : 
                  '0%'
                } del totale
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Informazioni tecniche */}
      <div className="card">
        <h3>⚙️ Informazioni Tecniche</h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
          gap: '20px' 
        }}>
          <div>
            <h4>🗄️ Struttura Database</h4>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li>📦 <strong>Database:</strong> DATABASE1</li>
              <li>📋 <strong>Collection MDM:</strong> mdm_documents</li>
              <li>🧪 <strong>Collection OUL:</strong> oul_lab_results</li>
              <li>📊 <strong>Collection ORU:</strong> oru_patient_monitoring</li>
            </ul>
          </div>
          
          <div>
            <h4>📋 Tipi di Messaggio Supportati</h4>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              <li>📄 <strong>MDM^T01:</strong> Medical Document Management</li>
              <li>🧪 <strong>OUL^R22:</strong> Unsolicited Laboratory Observation</li>
              <li>📊 <strong>ORU^R01:</strong> Unsolicited Observation Result</li>
            </ul>
          </div>
        </div>
        
        <div style={{ 
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#f8f9fa',
          borderRadius: '6px',
          fontSize: '14px',
          color: '#666'
        }}>
          <strong>Ultimo Aggiornamento:</strong> {new Date().toLocaleString('it-IT')}
        </div>
      </div>
    </div>
  );
};

export default Statistics;
