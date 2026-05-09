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

        setStatus(generateStatus, 'Generating resume and opening Finder...', 'loading');

        try {
            const response = await fetch('/api/generate-resume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ json_content: jsonObj }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Failed to generate resume');
            }

            setStatus(generateStatus, 'Success! Resume generated.', 'success');
        } catch (error) {
            setStatus(generateStatus, `Error: ${error.message}`, 'error');
        }
    });
});
