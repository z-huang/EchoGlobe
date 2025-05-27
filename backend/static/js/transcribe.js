function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

$(function () {
    const RECORD_INTERVAL_MS = 2000;
    let isRecording = false;
    let audioStream;
    let mediaRecorder;
    let ws;

    function startWebSocket(meetingId) {
        ws = new WebSocket(`ws://localhost:8000/ws/transcript/`);
        ws.onopen = () => console.log('WebSocket connected.');
        ws.onmessage = (message) => {
            console.log('Received from server:', message.data);

            const data = JSON.parse(message.data);
            const text = data.text;
            const id = data.block_id;

            const chatMessages = document.getElementById('transcriptArea');
            let existingMsgDiv = document.getElementById(`msg-${id}`);

            if (existingMsgDiv) {
                existingMsgDiv.textContent = text;
            } else {
                const serverMsgDiv = document.createElement('div');
                serverMsgDiv.className = 'server-message';
                serverMsgDiv.id = `msg-${id}`;
                serverMsgDiv.textContent = text;
                chatMessages.appendChild(serverMsgDiv);
            }

            chatMessages.scrollTop = chatMessages.scrollHeight;
        };
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            audioStream = stream;

            const audioTrack = stream.getAudioTracks()[0];
            const audioSettings = audioTrack.getSettings();
            console.log(`Sample Rate: ${audioSettings.sampleRate} Hz`);
            console.log(`Channels: ${audioSettings.channelCount || "Unknown"}`);

            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

            mediaRecorder.ondataavailable = (event) => {
                if (ws.readyState === WebSocket.OPEN) {
                    ws.send(event.data);
                }
            };

            mediaRecorder.start(RECORD_INTERVAL_MS);
            console.log('Streaming started...');
        } catch (error) {
            console.error("Error accessing microphone:", error);
        }
    }

    function stopRecording() {
        if (mediaRecorder) {
            mediaRecorder.stop();
        }
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }
        console.log('Streaming stopped.');
    }

    function updateRecordButtonText(isRecording) {
        if (isRecording) {
            $("#startBtn").html(`<span class="btn-icon">■</span> <span data-i18n="stop">${currentTranslations.stop}</span>`);
        } else {
            $("#startBtn").html(`<span class="btn-icon">●</span> <span data-i18n="record">${currentTranslations.record}</span>`);
        }
    }

    $("#startBtn").click(() => {
        if (!isRecording) {
            startRecording();
        } else {
            stopRecording();
        }
        isRecording = !isRecording;
        updateRecordButtonText(isRecording);
    });

    $(".upload-btn").click(() => {
        const fileInput = $('<input type="file" accept="audio/*" style="display:none">');
        fileInput.on('change', function () {
            const file = this.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('audio', file);

            $.ajax({
                url: '/api/transcribe_file/',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                success: function (response) {
                    console.log(response)
                },
                error: function (xhr, status, error) {
                    alert('Upload failed: ' + error);
                }
            });
        });
        fileInput.trigger('click');
    });

    startWebSocket(0);
})