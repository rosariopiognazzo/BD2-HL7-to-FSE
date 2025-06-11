let patients = [];

function showAlert(msg, type = 'info') {
    const alertBox = document.getElementById('alertBox');
    alertBox.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    setTimeout(() => { alertBox.innerHTML = ''; }, 4000);
}

function showInsertForm() {
    document.getElementById('insertForm').style.display = '';
    document.getElementById('hl7Input').value = '';
}
function hideInsertForm() {
    document.getElementById('insertForm').style.display = 'none';
}

function submitHL7() {
    const hl7 = document.getElementById('hl7Input').value;
    fetch('/api/hl7', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hl7_message: hl7 })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showAlert('Paziente inserito con ID: ' + data.patient_id, 'success');
            hideInsertForm();
            loadPatients();
        } else {
            showAlert('Errore: ' + (data.error || 'Errore generico'), 'danger');
        }
    });
}

function loadPatients(query = '') {
    let url = '/api/patients';
    if (query) url += '?q=' + encodeURIComponent(query);
    fetch(url)
        .then(r => r.json())
        .then(data => {
            patients = data;
            renderPatientsTable();
        });
}

function renderPatientsTable() {
    const div = document.getElementById('patientsTable');
    if (!patients.length) {
        div.innerHTML = '<p>Nessun paziente trovato.</p>';
        return;
    }
    let html = `<table class="table table-bordered table-hover"><thead><tr><th>ID</th><th>Codice Fiscale</th><th>Cognome</th><th>Nome</th><th>Azioni</th></tr></thead><tbody>`;
    for (const p of patients) {
        html += `<tr>
            <td>${p.id}</td>
            <td>${(p.identifier && p.identifier[0]) ? p.identifier[0].value : ''}</td>
            <td>${(p.name && p.name[0]) ? p.name[0].family : ''}</td>
            <td>${(p.name && p.name[0] && p.name[0].given) ? p.name[0].given[0] : ''}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="showPatientDetail('${p.id}')">Dettagli</button>
                <button class="btn btn-sm btn-danger" onclick="deletePatient('${p.id}')">Elimina</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    div.innerHTML = html;
    document.getElementById('patientDetail').innerHTML = '';
}

function showPatientDetail(pid) {
    fetch('/api/patient/' + pid)
        .then(r => r.json())
        .then(p => {
            if (p.error) {
                showAlert(p.error, 'danger');
                return;
            }
            let html = `<h4>Dettaglio Paziente</h4><table class="table table-bordered">`;
            html += `<tr><th>ID</th><td>${p.id}</td></tr>`;
            html += `<tr><th>Codice Fiscale</th><td>${(p.identifier && p.identifier[0]) ? p.identifier[0].value : ''}</td></tr>`;
            html += `<tr><th>Cognome</th><td>${(p.name && p.name[0]) ? p.name[0].family : ''}</td></tr>`;
            html += `<tr><th>Nome</th><td>${(p.name && p.name[0] && p.name[0].given) ? p.name[0].given[0] : ''}</td></tr>`;
            html += `<tr><th>Data di nascita</th><td>${p.birthDate || ''}</td></tr>`;
            html += `<tr><th>Sesso</th><td>${p.gender || ''}</td></tr>`;
            html += `<tr><th>Indirizzo</th><td>${(p.address && p.address[0] && p.address[0].line && p.address[0].line[0]) ? p.address[0].line[0] : ''} ${(p.address && p.address[0]) ? p.address[0].city : ''}</td></tr>`;
            html += `<tr><th>Telefono</th><td>${(p.telecom && p.telecom[0]) ? p.telecom[0].value : ''}</td></tr>`;
            html += '</table>';
            // Carica anche i lab_results
            fetch(`/api/patient/${pid}/lab_results`).then(r => r.json()).then(results => {
                if (results.length) {
                    html += `<h5>Risultati clinici/laboratorio</h5><table class="table table-sm table-bordered"><thead><tr><th>Codice</th><th>Descrizione</th><th>Valore</th><th>Unità</th><th>Range</th><th>Data</th></tr></thead><tbody>`;
                    for (const res of results) {
                        const code = res.code && res.code.coding && res.code.coding[0] ? res.code.coding[0].code : '';
                        const display = res.code && res.code.coding && res.code.coding[0] ? res.code.coding[0].display : '';
                        html += `<tr><td>${code}</td><td>${display}</td><td>${res.value || ''}</td><td>${res.unit || ''}</td><td>${res.referenceRange || ''}</td><td>${res.issued || ''}</td></tr>`;
                    }
                    html += '</tbody></table>';
                }
                document.getElementById('patientDetail').innerHTML = html;
            });
        });
}

function deletePatient(pid) {
    if (!confirm('Sicuro di eliminare questo paziente?')) return;
    fetch('/api/patient/' + pid, { method: 'DELETE' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert('Paziente eliminato.', 'success');
                loadPatients();
            } else {
                showAlert('Errore: ' + (data.error || 'Errore generico'), 'danger');
            }
        });
}

function loadRawLabData() {
    fetch('/api/raw_lab_data')
        .then(r => r.json())
        .then(data => {
            renderRawLabData(data);
        })
        .catch(err => {
            showAlert('Errore nel caricare dati laboratorio: ' + err.message, 'danger');
        });
}

function renderRawLabData(data) {
    const div = document.getElementById('rawLabData');
    if (!data.length) {
        div.innerHTML = '<p>Nessun dato di laboratorio raw trovato.</p>';
        return;
    }
    
    let html = `<h4>Dati Laboratorio Non Processati</h4>`;
    html += `<table class="table table-bordered table-hover"><thead><tr><th>ID Messaggio</th><th>Timestamp</th><th>Tipo</th><th>Azioni</th></tr></thead><tbody>`;
    
    for (const item of data) {
        html += `<tr>
            <td>${item._id || 'N/A'}</td>
            <td>${item.timestamp || 'N/A'}</td>
            <td>${item.messageType || 'N/A'}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="showLabDetail('${item._id}')">Dettagli</button>
                <button class="btn btn-sm btn-success" onclick="showAssignLabToPatient('${item._id}')">Assegna a Paziente</button>
            </td>
        </tr>`;
    }
    html += '</tbody></table>';
    div.innerHTML = html;
}

function showLabDetail(labId) {
    fetch(`/api/raw_lab_data/${labId}`)
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showAlert('Errore: ' + data.error, 'danger');
                return;
            }
            renderLabDetail(data);
        })
        .catch(err => {
            showAlert('Errore nel caricare dettagli: ' + err.message, 'danger');
        });
}

function renderLabDetail(labData) {
    const detailDiv = document.getElementById('labDetail');
    
    let html = `
        <div class="card mt-3">
            <div class="card-header">
                <h5>Dettagli Documento Laboratorio</h5>
                <button class="btn btn-sm btn-secondary float-end" onclick="hideLabDetail()">Chiudi</button>
            </div>
            <div class="card-body">
                <!-- Informazioni Documento -->
                <h6>Informazioni Documento</h6>
                <table class="table table-sm table-bordered">
                    <tr><th>ID Documento</th><td>${labData.document_id}</td></tr>
                    <tr><th>Timestamp</th><td>${labData.timestamp}</td></tr>
                    <tr><th>Tipo Messaggio</th><td>${labData.message_type}</td></tr>
                    <tr><th>Applicazione Mittente</th><td>${labData.sending_application}</td></tr>
                    <tr><th>Applicazione Destinatario</th><td>${labData.receiving_application}</td></tr>
                </table>
                
                <!-- Informazioni Paziente -->
                <h6 class="mt-3">Informazioni Paziente</h6>
                <table class="table table-sm table-bordered">
                    <tr><th>Identificatori</th><td>${labData.patient_info.identifiers || 'N/A'}</td></tr>
                    <tr><th>Nome</th><td>${labData.patient_info.name || 'N/A'}</td></tr>
                    <tr><th>Data Nascita</th><td>${labData.patient_info.birth_date || 'N/A'}</td></tr>
                    <tr><th>Sesso</th><td>${labData.patient_info.gender || 'N/A'}</td></tr>
                    <tr><th>Indirizzo</th><td>${labData.patient_info.address || 'N/A'}</td></tr>
                    <tr><th>Telefono</th><td>${labData.patient_info.phone || 'N/A'}</td></tr>
                </table>
                
                <!-- Risultati Laboratorio -->
                <h6 class="mt-3">Risultati di Laboratorio</h6>`;
    
    if (labData.lab_results && labData.lab_results.length > 0) {
        html += `
                <table class="table table-sm table-bordered table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Codice Test</th>
                            <th>Nome Test</th>
                            <th>Valore</th>
                            <th>Unità</th>
                            <th>Range Riferimento</th>
                            <th>Stato</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        for (const result of labData.lab_results) {
            // Determina il colore della riga in base al valore e range
            let rowClass = '';
            if (result.value && result.reference_range) {
                const isNormal = checkIfValueInRange(result.value, result.reference_range);
                rowClass = isNormal ? 'table-success' : 'table-warning';
            }
            
            html += `
                        <tr class="${rowClass}">
                            <td><code>${result.test_code || 'N/A'}</code></td>
                            <td><strong>${result.test_name || 'N/A'}</strong></td>
                            <td>${result.value || 'N/A'}</td>
                            <td>${result.unit || 'N/A'}</td>
                            <td>${result.reference_range || 'N/A'}</td>
                            <td><span class="badge bg-primary">${result.status || 'N/A'}</span></td>
                        </tr>`;
        }
        
        html += `
                    </tbody>
                </table>`;
    } else {
        html += `<p class="text-muted">Nessun risultato di laboratorio trovato in questo documento.</p>`;
    }
    
    html += `
                <div class="mt-3">
                    <button class="btn btn-success" onclick="showAssignLabToPatient('${labData.document_id}')">
                        Assegna a Paziente
                    </button>
                    <button class="btn btn-info" onclick="downloadLabData('${labData.document_id}')">
                        Scarica JSON
                    </button>
                </div>
            </div>
        </div>`;
    
    detailDiv.innerHTML = html;
    detailDiv.scrollIntoView({ behavior: 'smooth' });
}

function hideLabDetail() {
    document.getElementById('labDetail').innerHTML = '';
}

function checkIfValueInRange(value, range) {
    try {
        if (!value || !range || typeof range !== 'string') return true;
        
        const numValue = parseFloat(value);
        if (isNaN(numValue)) return true;
        
        // Gestisci range tipo "3.5 - 5.3"
        if (range.includes(' - ')) {
            const [min, max] = range.split(' - ').map(x => parseFloat(x.trim()));
            if (!isNaN(min) && !isNaN(max)) {
                return numValue >= min && numValue <= max;
            }
        }
        
        // Gestisci range tipo "> 3.0" o "< 10.0"
        if (range.startsWith('>')) {
            const minValue = parseFloat(range.substring(1).trim());
            return !isNaN(minValue) && numValue > minValue;
        }
        
        if (range.startsWith('<')) {
            const maxValue = parseFloat(range.substring(1).trim());
            return !isNaN(maxValue) && numValue < maxValue;
        }
        
        return true; // Se non riusciamo a parsare, assumiamo normale
    } catch (e) {
        return true;
    }
}

function downloadLabData(labId) {
    fetch(`/api/raw_lab_data/${labId}`)
        .then(r => r.json())
        .then(data => {
            const dataStr = JSON.stringify(data, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `lab_data_${labId}.json`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        })
        .catch(err => {
            showAlert('Errore nel download: ' + err.message, 'danger');
        });
}

function showAssignLabToPatient(labId) {
    const patientId = prompt('Inserisci ID del paziente a cui assegnare questi risultati:');
    if (patientId) {
        fetch('/api/process_lab_document', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                document_id: labId, 
                patient_id: patientId 
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showAlert(data.message, 'success');
                loadRawLabData(); // Ricarica i dati
            } else {
                showAlert('Errore: ' + data.error, 'danger');
            }
        });
    }
}

document.getElementById('searchInput').addEventListener('input', function() {
    loadPatients(this.value);
});

window.onload = function() {
    loadPatients();
    loadRawLabData();
};
