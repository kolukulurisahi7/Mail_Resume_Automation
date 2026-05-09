document.addEventListener('DOMContentLoaded', () => {
    const jdInput = document.getElementById('jdInput');
    const draftEmailBtn = document.getElementById('draftEmailBtn');
    const draftStatus = document.getElementById('draftStatus');

    const jsonInput = document.getElementById('jsonInput');
    const generateResumeBtn = document.getElementById('generateResumeBtn');
    const generateStatus = document.getElementById('generateStatus');

    // Helper to set status
    function setStatus(element, message, type) {
        element.textContent = message;
        element.className = 'status-msg status-' + type;
        if (type === 'success') {
            setTimeout(() => {
                element.textContent = '';
                element.className = 'status-msg';
            }, 5000);
        }
    }

    // 1. Draft Email Handler
    draftEmailBtn.addEventListener('click', async () => {
        const jdText = jdInput.value.trim();
        if (!jdText) {
            setStatus(draftStatus, 'Please paste a JD first.', 'error');
            return;
        }

        setStatus(draftStatus, 'Drafting email...', 'loading');

        try {
            const response = await fetch('/api/draft-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ jd_text: jdText }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to draft email');
            }

            setStatus(draftStatus, `Success! Check Mail.app. (Recipient: ${data.recipient || 'None found'})`, 'success');
        } catch (error) {
            setStatus(draftStatus, `Error: ${error.message}`, 'error');
        }
    });

    // 2. Generate Resume Handler
    generateResumeBtn.addEventListener('click', async () => {
        const jsonText = jsonInput.value.trim();
        if (!jsonText) {
            setStatus(generateStatus, 'Please paste JSON content first.', 'error');
            return;
        }

        let jsonObj;
        try {
            jsonObj = JSON.parse(jsonText);
        } catch (e) {
            setStatus(generateStatus, 'Invalid JSON format.', 'error');
            return;
        }

        setStatus(generateStatus, 'Generating resume...', 'loading');

        try {
            console.log('[DEBUG] Sending resume generation request...');
            
            const response = await fetch('/api/generate-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ json_content: jsonObj }),
            });

            if (!response.ok) {
                // Try to parse error as JSON
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.error || 'Failed to generate resume');
            }

            // Response is a DOCX file blob
            console.log('[DEBUG] Resume generated successfully. Starting download...');
            const blob = await response.blob();
            console.log('[DEBUG] Blob received, size:', blob.size);
            
            // Create download link and trigger download
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Sahi_Kolukuluri.docx';
            document.body.appendChild(a);
            a.click();
            console.log('[DEBUG] Download triggered');
            
            // Cleanup
            a.remove();
            window.URL.revokeObjectURL(url);
            
            setStatus(generateStatus, 'Success! Resume downloaded.', 'success');
        } catch (error) {
            console.error('[DEBUG] Error:', error.message);
            setStatus(generateStatus, `Error: ${error.message}`, 'error');
        }
    });
});
