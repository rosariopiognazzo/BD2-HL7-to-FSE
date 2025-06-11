document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const collectionName = document.getElementById('collectionName').value;
    const jsonFile = document.getElementById('jsonFile').files[0];

    if (!collectionName || !jsonFile) {
        displayFeedback('Please provide both collection name and a JSON file.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('collection', collectionName);
    formData.append('file', jsonFile);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            displayFeedback(`Success: ${result.message}`, 'success');
        } else {
            displayFeedback(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        displayFeedback(`Error: ${error.message}`, 'error');
    }
});

function displayFeedback(message, type) {
    const feedbackElement = document.getElementById('feedback');
    feedbackElement.textContent = message;
    feedbackElement.className = `feedback ${type}`;
}
