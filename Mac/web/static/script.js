// Timspeak Web Interface JavaScript

let isRecording = false;
let currentSttAdapter = null;
let currentLlmAdapter = null;
let pollInterval = null;

// DOM elements
const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const sttSelect = document.getElementById('sttSelect');
const llmSelect = document.getElementById('llmSelect');
const originalText = document.getElementById('originalText');
const cleanedText = document.getElementById('cleanedText');
const copyBtn = document.getElementById('copyBtn');
const clearBtn = document.getElementById('clearBtn');
const statusText = document.getElementById('statusText');
const spinner = document.getElementById('spinner');
const sttCount = document.getElementById('sttCount');
const llmCount = document.getElementById('llmCount');

// Initialize on page load
window.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    copyBtn.addEventListener('click', copyToClipboard);
    clearBtn.addEventListener('click', clearResults);

    sttSelect.addEventListener('change', (e) => {
        currentSttAdapter = e.target.value;
    });

    llmSelect.addEventListener('change', (e) => {
        currentLlmAdapter = e.target.value;
    });
}

// Load status and available adapters
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        // Populate STT adapters
        sttSelect.innerHTML = '';
        Object.entries(data.stt_adapters).forEach(([key, name]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = name;
            if (key === data.default_stt) {
                option.selected = true;
                currentSttAdapter = key;
            }
            sttSelect.appendChild(option);
        });

        // Populate LLM adapters
        llmSelect.innerHTML = '';
        Object.entries(data.llm_adapters).forEach(([key, name]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = name;
            if (key === data.default_llm) {
                option.selected = true;
                currentLlmAdapter = key;
            }
            llmSelect.appendChild(option);
        });

        // Update counts
        sttCount.textContent = Object.keys(data.stt_adapters).length;
        llmCount.textContent = Object.keys(data.llm_adapters).length;

        // Enable record button if adapters are loaded
        if (Object.keys(data.stt_adapters).length > 0 && Object.keys(data.llm_adapters).length > 0) {
            recordBtn.disabled = false;
            setStatus('Ready');
        } else {
            setStatus('No adapters available - check configuration');
        }

    } catch (error) {
        console.error('Failed to load status:', error);
        setStatus('Failed to connect to server');
    }
}

// Start recording
async function startRecording() {
    try {
        const response = await fetch('/api/record/start', {
            method: 'POST'
        });

        if (response.ok) {
            isRecording = true;
            recordBtn.disabled = true;
            stopBtn.disabled = false;
            sttSelect.disabled = true;
            llmSelect.disabled = true;
            setStatus('Recording... Speak now!');
        } else {
            const data = await response.json();
            alert('Failed to start recording: ' + data.error);
        }

    } catch (error) {
        console.error('Failed to start recording:', error);
        alert('Failed to start recording');
    }
}

// Stop recording
async function stopRecording() {
    try {
        const response = await fetch('/api/record/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stt_adapter: currentSttAdapter,
                llm_adapter: currentLlmAdapter
            })
        });

        if (response.ok) {
            isRecording = false;
            recordBtn.disabled = true;
            stopBtn.disabled = true;
            setStatus('Processing...', true);

            // Start polling for results
            startPolling();

        } else {
            const data = await response.json();
            alert('Failed to stop recording: ' + data.error);
            resetButtons();
        }

    } catch (error) {
        console.error('Failed to stop recording:', error);
        alert('Failed to stop recording');
        resetButtons();
    }
}

// Poll for results
function startPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
    }

    pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/result');
            const data = await response.json();

            if (data.status === 'complete') {
                // Display results
                originalText.value = data.original;
                cleanedText.value = data.cleaned;
                copyBtn.disabled = false;
                clearBtn.disabled = false;
                setStatus(`Complete! Used ${data.stt_used} → ${data.llm_used}`, false);

                // Stop polling
                clearInterval(pollInterval);
                pollInterval = null;

                // Re-enable controls
                resetButtons();

            } else if (data.status === 'error') {
                // Show error
                setStatus('Error: ' + data.error, false);
                alert('Processing failed: ' + data.error);

                // Stop polling
                clearInterval(pollInterval);
                pollInterval = null;

                // Re-enable controls
                resetButtons();
            }
            // Otherwise keep polling (status === 'waiting')

        } catch (error) {
            console.error('Failed to get result:', error);
            clearInterval(pollInterval);
            pollInterval = null;
            resetButtons();
        }

    }, 500); // Poll every 500ms
}

// Copy cleaned text to clipboard
function copyToClipboard() {
    const text = cleanedText.value;
    if (!text) {
        alert('No text to copy');
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        setStatus('Copied to clipboard!', false);
        setTimeout(() => {
            setStatus('Ready', false);
        }, 2000);
    }).catch((error) => {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard');
    });
}

// Clear results
async function clearResults() {
    try {
        await fetch('/api/clear', { method: 'POST' });
        originalText.value = '';
        cleanedText.value = '';
        copyBtn.disabled = true;
        clearBtn.disabled = true;
        setStatus('Ready', false);
    } catch (error) {
        console.error('Failed to clear:', error);
    }
}

// Set status message
function setStatus(message, showSpinner = false) {
    statusText.textContent = message;
    if (showSpinner) {
        spinner.classList.remove('hidden');
    } else {
        spinner.classList.add('hidden');
    }
}

// Reset buttons to ready state
function resetButtons() {
    recordBtn.disabled = false;
    stopBtn.disabled = true;
    sttSelect.disabled = false;
    llmSelect.disabled = false;
}
