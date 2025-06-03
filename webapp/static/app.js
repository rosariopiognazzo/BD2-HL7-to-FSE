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

document.getElementById('searchInput').addEventListener('input', function() {
    loadPatients(this.value);
});

window.onload = function() {
    loadPatients();
};
