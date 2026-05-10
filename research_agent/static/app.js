document.addEventListener('DOMContentLoaded', () => {
    const topicInput = document.getElementById('topic-input');
    const generateBtn = document.getElementById('generate-btn');
    const exportTxtBtn = document.getElementById('export-txt-btn');
    const exportPdfBtn = document.getElementById('export-pdf-btn');
    const backBtn = document.getElementById('back-btn');
    
    const txtStatus = document.getElementById('txt-status');
    const pdfStatus = document.getElementById('pdf-status');
    const searchStatus = document.getElementById('search-status');
    
    const errorMessage = document.getElementById('error-message');
    const loadingSection = document.getElementById('loading-section');
    const landingPage = document.getElementById('landing-page');
    const resultsSection = document.getElementById('results-section');
    const researchContent = document.getElementById('research-content');
    const resultTopic = document.getElementById('result-topic');
    const resultTimestamp = document.getElementById('result-timestamp');
    const resultWordcount = document.getElementById('result-wordcount');
    const mcpSyncNotice = document.getElementById('mcp-sync-notice');

    let currentResearch = null;

    // Check MCP Connection Status on load
    async function checkMcpStatus() {
        try {
            const response = await fetch('/api/mcp/status');
            const data = await response.json();
            
            if (txtStatus) updateStatusIndicator(txtStatus, data.txt);
            if (pdfStatus) updateStatusIndicator(pdfStatus, data.pdf);
            if (searchStatus) updateStatusIndicator(searchStatus, data.search);
        } catch (error) {
            console.error('Failed to check MCP status:', error);
        }
    }

    function updateStatusIndicator(el, connected) {
        if (!el) return;
        if (connected) {
            el.textContent = 'Connected';
            el.classList.remove('disconnected');
            el.classList.add('connected');
        } else {
            el.textContent = 'Disconnected';
            el.classList.remove('connected');
            el.classList.add('disconnected');
        }
    }

    checkMcpStatus();
    setInterval(checkMcpStatus, 5000); // Check status every 5 seconds

    // Generate Research
    generateBtn.addEventListener('click', async () => {
        const topic = topicInput.value.trim();
        
        // Validation
        if (!topic) {
            showError("Please enter a research topic");
            return;
        }
        if (topic.length < 3) {
            showError("Topic must be at least 3 characters");
            return;
        }

        clearError();
        showLoading(true);

        try {
            const response = await fetch('/api/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ topic })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || "AI service temporarily unavailable. Please try again.");
            }

            currentResearch = data;
            displayResults(data);
        } catch (error) {
            showError(error.message);
            showLoading(false);
        }
    });

    // Back Button
    backBtn.addEventListener('click', () => {
        resultsSection.style.display = 'none';
        landingPage.style.display = 'block';
        topicInput.value = '';
        currentResearch = null;
        showLoading(false);
    });

    // Export TXT
    exportTxtBtn.addEventListener('click', async () => {
        if (!currentResearch) return;
        try {
            const response = await fetch('/api/export/txt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    topic: currentResearch.topic,
                    summary: currentResearch.summary 
                })
            });
            const blob = await response.blob();
            downloadFile(blob, `Research_${currentResearch.topic.replace(/ /g, '_')}.txt`);
            showMcpFeedback("Synced to TXT Storage");
        } catch (error) {
            showError("TXT generation failure");
        }
    });

    // Export PDF
    exportPdfBtn.addEventListener('click', async () => {
        if (!currentResearch) return;
        try {
            const response = await fetch('/api/export/pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    topic: currentResearch.topic,
                    summary: currentResearch.summary 
                })
            });
            if (!response.ok) throw new Error("PDF generation failure");
            const blob = await response.blob();
            downloadFile(blob, `Research_${currentResearch.topic.replace(/ /g, '_')}.pdf`);
            showMcpFeedback("Synced to PDF Storage");
        } catch (error) {
            showError("PDF generation failure.");
        }
    });

    function showMcpFeedback(message) {
        mcpSyncNotice.textContent = `✅ ${message}`;
        mcpSyncNotice.classList.remove('hidden');
        setTimeout(() => {
            mcpSyncNotice.classList.add('hidden');
        }, 3000);
    }

    function displayResults(data) {
        landingPage.style.display = 'none';
        resultsSection.style.display = 'block';
        
        resultTopic.textContent = data.topic;
        researchContent.innerHTML = marked.parse(data.summary);
        resultTimestamp.textContent = `Generated: ${data.timestamp}`;
        resultWordcount.textContent = `${data.word_count} words`;
        
        if (data.mcp_status) {
            mcpSyncNotice.textContent = "Research successfully synchronized via MCP nodes.";
            mcpSyncNotice.classList.remove('hidden');
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showLoading(isLoading) {
        if (isLoading) {
            loadingSection.classList.remove('hidden');
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Analyzing...';
        } else {
            loadingSection.classList.add('hidden');
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-sparkles"></i> Generate Research';
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function clearError() {
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
    }

    function downloadFile(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
});
