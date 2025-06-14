import React, { useState, useEffect } from 'react';
import './index.css';
import FileUpload from './components/FileUpload';
import DocumentViewer from './components/DocumentViewer';
import SearchInterface from './components/SearchInterface';
import Statistics from './components/Statistics';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [stats, setStats] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Funzione per ricaricare le statistiche
  const refreshStats = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  useEffect(() => {
    // Carica le statistiche all'avvio e quando refreshTrigger cambia
    fetch('/api/stats')
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          setStats(data.stats);
        }
      })
      .catch(error => console.error('Errore nel caricamento delle statistiche:', error));
  }, [refreshTrigger]);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'upload':
        return <FileUpload onUploadSuccess={refreshStats} />;
      case 'view':
        return <DocumentViewer refreshTrigger={refreshTrigger} onDeleteSuccess={refreshStats} />;
      case 'search':
        return <SearchInterface />;
      case 'stats':
        return <Statistics stats={stats} onRefresh={refreshStats} />;
      default:
        return <FileUpload onUploadSuccess={refreshStats} />;
    }
  };

  return (
    <div className="App">
      <header className="header">
        <div className="container">
          <h1>HL7 Framework</h1>
          <p style={{ textAlign: 'center', margin: '10px 0 0 0', opacity: 0.9 }}>
            Sistema per la conversione di dati sanitari HL7 in JSON e gestione MongoDB
          </p>
        </div>
      </header>

      <nav className="nav">
        <div className="container">
          <div className="nav-buttons">
            <button
              className={`nav-button ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              📤 Carica File HL7
            </button>
            <button
              className={`nav-button ${activeTab === 'view' ? 'active' : ''}`}
              onClick={() => setActiveTab('view')}
            >
              📋 Visualizza Documenti
            </button>
            <button
              className={`nav-button ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              🔍 Ricerca
            </button>
            <button
              className={`nav-button ${activeTab === 'stats' ? 'active' : ''}`}
              onClick={() => setActiveTab('stats')}
            >
              📊 Statistiche
            </button>
          </div>
        </div>
      </nav>

      <main className="container">
        {renderActiveTab()}
      </main>

      <footer style={{ 
        textAlign: 'center', 
        padding: '40px 20px', 
        color: '#7f8c8d',
        borderTop: '1px solid #ecf0f1',
        marginTop: '40px'
      }}>
        <p>HL7 Framework - Progetto Basi di Dati 2</p>
        <p style={{ fontSize: '14px', marginTop: '10px' }}>
          Supporta messaggi MDM, OUL e ORU secondo le specifiche HL7 v2.x
        </p>
      </footer>
    </div>
  );
}

export default App;
