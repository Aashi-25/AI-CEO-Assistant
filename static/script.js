let recorder;
let stream;
let isRecording = false;

const recordBtn = document.getElementById('start-record');
const audioPlayer = document.getElementById('audio-preview');
const playbackSection = document.getElementById('playback-section');

const assistantResponseSection = document.getElementById('assistant-response-section');
const assistantAnswerP = document.getElementById('assistant-answer');
const speakAnswerBtn = document.getElementById('speak-answer-btn');

// Text-to-speech AJAX functionality
const ttsForm = document.getElementById('tts-form');
const ttsAudioSection = document.getElementById('tts-audio-section');
const ttsAudio = document.getElementById('tts-audio');
const ttsTextarea = document.getElementById('tts-textarea');
const clearTTSBtn = document.getElementById('clear-tts');

// --- DOM Elements ---
const questionInput = document.getElementById('question-input');
const micBtn = document.getElementById('mic-btn');
const micIcon = document.getElementById('mic-icon');
const sendBtn = document.querySelector('.send-btn');
const assistantForm = document.getElementById('assistant-form');
const answerSection = document.getElementById('answer-section');
const assistantAnswer = document.getElementById('assistant-answer');
const loadingOverlay = document.getElementById('loading-overlay');
const toast = document.getElementById('toast');
const audioRow = document.getElementById('audio-row');
const questionAudio = document.getElementById('question-audio');

// --- Loading Spinner ---
function showLoading() {
    if (loadingOverlay) loadingOverlay.classList.add('active');
}
function hideLoading() {
    if (loadingOverlay) loadingOverlay.classList.remove('active');
}

// --- Toast Notification ---
function showToast(message, duration = 2500) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
}

// --- Speech Recognition (Mic) ---
let recognition;
let audioBlob = null;
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add('active');
        micIcon.textContent = '⏹️';
        showToast('Listening...');
    };
    recognition.onend = () => {
        isRecording = false;
        micBtn.classList.remove('active');
        micIcon.textContent = '🎤';
    };
    recognition.onerror = (e) => {
        showToast('Mic error: ' + e.error, 3000);
        isRecording = false;
        micBtn.classList.remove('active');
        micIcon.textContent = '🎤';
    };
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        questionInput.value = transcript;
        showToast('Transcribed!');
    };
} else {
    micBtn.disabled = true;
    micBtn.title = 'Speech recognition not supported';
}

micBtn.onclick = function(e) {
    e.preventDefault();
    if (isRecording) {
        recognition && recognition.stop();
        return;
    }
    // Also record audio for playback
    if (navigator.mediaDevices && window.MediaRecorder) {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const mediaRecorder = new MediaRecorder(stream);
                let chunks = [];
                mediaRecorder.ondataavailable = e => chunks.push(e.data);
                mediaRecorder.onstop = () => {
                    audioBlob = new Blob(chunks, { type: 'audio/webm' });
                    questionAudio.src = URL.createObjectURL(audioBlob);
                    audioRow.style.display = 'block';
                    stream.getTracks().forEach(track => track.stop());
                };
                mediaRecorder.start();
                recognition && recognition.start();
                setTimeout(() => {
                    if (mediaRecorder.state !== 'inactive') mediaRecorder.stop();
                    recognition && recognition.stop();
                }, 6000); // Max 6 seconds
            })
            .catch(() => showToast('Microphone access denied.', 3000));
    } else {
        recognition && recognition.start();
    }
};

// --- Ask Assistant (Text or Speech) ---
assistantForm.onsubmit = function(e) {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return showToast('Please enter a question.', 2000);
    showLoading();
    // If audioBlob exists, send as speech-to-text, else as text
    if (audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recorded_audio.webm');
        fetch('/speech-to-text', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.text())
        .then(html => {
            // Extract recognized text from returned HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newConvertedTextArea = tempDiv.querySelector('#convertedText');
            let recognizedText = question;
            if (newConvertedTextArea && newConvertedTextArea.value) {
                recognizedText = newConvertedTextArea.value;
            }
            askAssistant(recognizedText);
        })
        .catch(() => {
            showToast('Speech recognition failed.', 3000);
            hideLoading();
        });
        audioBlob = null;
    } else {
        // For typed question: also convert to speech and show audio
        const ttsFormData = new FormData();
        ttsFormData.append('text', question);
        fetch('/text-to-speech', {
            method: 'POST',
            body: ttsFormData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.audio_url) {
                questionAudio.src = data.audio_url + '?t=' + new Date().getTime();
                audioRow.style.display = 'block';
            } else {
                audioRow.style.display = 'none';
            }
        })
        .catch(() => {
            audioRow.style.display = 'none';
        })
        .finally(() => {
            askAssistant(question);
        });
    }
};

function askAssistant(text) {
    const formData = new FormData();
    formData.append('text', text);
    fetch('/ask', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        assistantAnswer.textContent = data.answer;
        answerSection.classList.add('show');
        // Hide the Executive Summary header
        const responseHeader = document.querySelector('.response-header');
        if (responseHeader) responseHeader.style.display = 'none';
        showToast('Analysis complete!', 'success');
    })
    .catch(() => {
        assistantAnswer.textContent = 'I apologize, but I encountered an issue processing your request. Please try again or contact technical support.';
        answerSection.classList.add('show');
        // Hide the Executive Summary header
        const responseHeader = document.querySelector('.response-header');
        if (responseHeader) responseHeader.style.display = 'none';
        showToast('Connection error. Please check your network and try again.', 'error', 4000);
    })
    .finally(() => {
        hideLoading();
        // Do not clear the question input
        // questionInput.value = '';
        // questionInput.style.height = 'auto';
    });
}

// --- Speak Assistant's Answer ---
let assistantAudio = null;
let audioState = 'idle'; // 'idle', 'playing', 'paused'
speakAnswerBtn.onclick = async function(e) {
    if (e) e.preventDefault();
    const textToSpeak = assistantAnswer.textContent;
    if (!textToSpeak || textToSpeak.includes('Error') || textToSpeak.includes('apologize')) return;

    // If audio is already loaded and playing/paused, toggle pause/resume
    if (assistantAudio) {
        if (!assistantAudio.paused) {
            assistantAudio.pause();
            speakAnswerBtn.innerHTML = '▶️ Resume';
            audioState = 'paused';
        } else if (audioState === 'paused') {
            assistantAudio.play();
            speakAnswerBtn.innerHTML = '⏸️ Pause';
            audioState = 'playing';
        }
        return;
    }

    // Otherwise, fetch and play audio
    speakAnswerBtn.innerHTML = '🔄 Generating Audio...';
    speakAnswerBtn.disabled = true;
    const formData = new FormData();
    formData.append('text', textToSpeak);
    try {
        const response = await fetch('/text-to-speech', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await response.json();
        if (data.audio_url) {
            // Remove any previous audio
            if (assistantAudio) {
                assistantAudio.pause();
                assistantAudio.remove();
            }
            assistantAudio = new Audio(data.audio_url + '?t=' + new Date().getTime());
            assistantAudio.onplay = function() {
                speakAnswerBtn.innerHTML = '⏸️ Pause';
                audioState = 'playing';
            };
            assistantAudio.onpause = function() {
                if (audioState !== 'idle') speakAnswerBtn.innerHTML = '▶️ Resume';
            };
            assistantAudio.onended = function() {
                speakAnswerBtn.innerHTML = '🔊 Listen to Response';
                audioState = 'idle';
                assistantAudio = null;
            };
            assistantAudio.onerror = function() {
                speakAnswerBtn.innerHTML = '🔊 Listen to Response';
                audioState = 'idle';
                assistantAudio = null;
            };
            assistantAudio.play();
            showToast('Playing audio response...', 'success');
        } else {
            showToast('Error generating audio: ' + data.error, 'error', 4000);
            speakAnswerBtn.innerHTML = '🔊 Listen to Response';
            audioState = 'idle';
            assistantAudio = null;
        }
    } catch {
        showToast('Audio generation failed. Please try again.', 'error', 4000);
        speakAnswerBtn.innerHTML = '🔊 Listen to Response';
        audioState = 'idle';
        assistantAudio = null;
    } finally {
        speakAnswerBtn.disabled = false;
    }
};

// --- UX: Enter key submits form ---
questionInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendBtn.click();
    }
});

recordBtn.onclick = () => {
    if (isRecording) {
        // Stop recording
        recorder.stop();
        recordBtn.textContent = "Start Recording";
        isRecording = false;
        return;
    }

    // Reset audio player before new recording
    audioPlayer.src = "";
    playbackSection.style.display = "none";

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(s => {
            stream = s;
            let chunks = [];
            recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            recorder.ondataavailable = e => chunks.push(e.data);

            recorder.onstop = () => {
                // This part handles the Speech-to-Speech playback
                const blob = new Blob(chunks, { type: 'audio/webm' });
                const audioURL = window.URL.createObjectURL(blob);
                audioPlayer.src = audioURL;
                playbackSection.style.display = "block";

                // Now, let's get the text and ask the assistant
                const formData = new FormData();
                formData.append('audio', blob, 'recorded_audio.webm');

                fetch('/speech-to-text', {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                })
                .then(response => {
                    if (!response.ok) throw new Error('Network error');
                    return response.text();
                })
                .then(html => {
                    // ACTION 2: Display the recognized text (restoring original functionality)
                    document.getElementById('result').innerHTML = html;

                    // ACTION 3: Send the text to the assistant
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = html;
                    const newConvertedTextArea = tempDiv.querySelector('#convertedText');

                    if (newConvertedTextArea && newConvertedTextArea.value) {
                        const recognizedText = newConvertedTextArea.value;
                        if (recognizedText.trim()) {
                            askAssistant(recognizedText);
                        }
                    } else {
                        console.error("Could not find recognized text to send to assistant.");
                    }
                })
                .catch(err => {
                    console.error('Error during speech processing:', err);
                    assistantAnswerP.textContent = 'Sorry, there was an error processing your speech.';
                    assistantResponseSection.style.display = 'block';
                });

                // Clean up the media stream
                stream.getTracks().forEach(track => track.stop());
            };

            // Start recording
            chunks = [];
            recorder.start();
            isRecording = true;
            recordBtn.textContent = "Stop Recording";
            console.log("Recording started");
        })
        .catch(err => console.error('Microphone access denied:', err));
};
    