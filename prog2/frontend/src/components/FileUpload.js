import React, { useState, useRef } from 'react';

const FileUpload = ({ onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [uploadedData, setUploadedData] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;

    // Verifica che sia un file di testo
    if (!file.name.toLowerCase().endsWith('.txt') && !file.type.includes('text')) {
      setMessage('Errore: Selezionare un file di testo (.txt)');
      return;
    }

    setIsUploading(true);
    setMessage('');
    setUploadedData(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setMessage(`✅ Successo: ${result.message}`);
        setUploadedData(result);
        if (onUploadSuccess) {
          onUploadSuccess();
        }
      } else {
        setMessage(`❌ Errore: ${result.error}`);
      }
    } catch (error) {
      setMessage(`❌ Errore di rete: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    handleFileUpload(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files[0];
    handleFileUpload(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setDragOver(false);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="card">
      <h2>📤 Caricamento File HL7</h2>
      <p>
        Carica file contenenti messaggi HL7 (MDM, OUL, ORU) per convertirli in formato JSON 
        e salvarli nel database MongoDB.
      </p>

      <div
        className={`upload-area ${dragOver ? 'dragover' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={openFileDialog}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt"
          onChange={handleFileSelect}
          className="file-input"
        />
        
        {isUploading ? (
          <div className="loading">
            <p>⏳ Processando file...</p>
          </div>
        ) : (
          <div>
            <p>📁 Clicca qui o trascina un file HL7 (.txt)</p>
            <button className="upload-button" type="button">
              Seleziona File
            </button>
          </div>
        )}
      </div>

      {message && (
        <div className={`message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {uploadedData && (
        <div className="card" style={{ marginTop: '20px' }}>
          <h3>📋 Dati Processati</h3>
          <div style={{ marginBottom: '15px' }}>
            <strong>Tipo Messaggio:</strong> {uploadedData.message_type}<br />
            <strong>ID Documento:</strong> {uploadedData.document_id}
          </div>
          
          <h4>📄 JSON Generato:</h4>
          <div className="json-viewer">
            {JSON.stringify(uploadedData.parsed_data, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
