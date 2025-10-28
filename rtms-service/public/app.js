const startButton = document.getElementById("startButton");
const statusEl = document.getElementById("status");
const videoEl = document.getElementById("videoFrame");
const videoPlaceholder = document.getElementById("videoPlaceholder");
const transcriptList = document.getElementById("transcriptList");

let socket;
let audioContext;
let nextAudioTime = 0;
let audioReady = false;
const pendingAudio = [];

function updateStatus(message) {
  statusEl.textContent = message;
}

function ensureSocket() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    return;
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/rtms/ws`);

  socket.addEventListener("open", () => {
    updateStatus("Connected. Waiting for RTMS events…");
  });

  socket.addEventListener("close", () => {
    updateStatus("Connection closed. Click start to reconnect.");
    startButton.disabled = false;
  });

  socket.addEventListener("error", (err) => {
    console.error("WebSocket error", err);
    updateStatus("WebSocket connection failed. Check logs and retry.");
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    handleMessage(message);
  });
}

function base64ToArrayBuffer(base64) {
  const binary = atob(base64);
  const length = binary.length;
  const bytes = new Uint8Array(length);

  for (let i = 0; i < length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }

  return bytes.buffer;
}

function enqueueAudioFrame(frame) {
  if (!audioReady) {
    pendingAudio.push(frame);
    return;
  }

  playAudioFrame(frame);
}

function playAudioFrame(frame) {
  if (!audioContext) {
    return;
  }

  const arrayBuffer = base64ToArrayBuffer(frame.data);
  const samples = new Int16Array(arrayBuffer);
  const frameLength = samples.length;

  if (frame.channels !== 1) {
    console.warn("Only mono audio is supported in this demo. Ignoring frame.");
    return;
  }

  const audioBuffer = audioContext.createBuffer(1, frameLength, frame.sampleRate);
  const channelData = audioBuffer.getChannelData(0);

  for (let i = 0; i < frameLength; i += 1) {
    channelData[i] = samples[i] / 32768;
  }

  const source = audioContext.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioContext.destination);

  const startTime = Math.max(nextAudioTime, audioContext.currentTime);
  source.start(startTime);
  nextAudioTime = startTime + audioBuffer.duration;
}

function activateAudio() {
  if (audioContext) {
    if (audioContext.state === "running") {
      return Promise.resolve(true);
    }

    return audioContext.resume().then(() => {
      audioReady = true;
      while (pendingAudio.length > 0) {
        const frame = pendingAudio.shift();
        playAudioFrame(frame);
      }
      return true;
    });
  }

  audioContext = new AudioContext({ sampleRate: 16000 });
  nextAudioTime = audioContext.currentTime;

  return audioContext.resume().then(() => {
    audioReady = true;
    while (pendingAudio.length > 0) {
      const frame = pendingAudio.shift();
      playAudioFrame(frame);
    }
    return true;
  });
}

function formatTime(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleTimeString();
}

// Map to store speaker colors
const speakerColors = new Map();
const colorPalette = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
];

function getSpeakerColor(speakerId) {
  if (!speakerId) return '#6b7280'; // Gray for unknown
  
  if (!speakerColors.has(speakerId)) {
    const colorIndex = speakerColors.size % colorPalette.length;
    speakerColors.set(speakerId, colorPalette[colorIndex]);
  }
  
  return speakerColors.get(speakerId);
}

function appendTranscript({ userName, userId, participantId, text, timestamp }) {
  if (!text) {
    return;
  }

  const speakerId = participantId || userId || userName || 'unknown';
  const speakerName = userName || 'Unknown speaker';
  const color = getSpeakerColor(speakerId);

  const item = document.createElement("li");
  const speaker = document.createElement("span");
  speaker.className = "speaker";
  speaker.textContent = speakerName;
  speaker.style.color = color;

  const time = document.createElement("span");
  time.className = "time";
  time.textContent = formatTime(timestamp);

  const content = document.createElement("p");
  content.textContent = text;

  item.appendChild(speaker);
  item.appendChild(time);
  item.appendChild(content);
  item.style.borderLeftColor = color;

  transcriptList.appendChild(item);
  transcriptList.scrollTop = transcriptList.scrollHeight;
}

function handleMessage(message) {
  switch (message.type) {
    case "status":
      updateStatus(`Stream ${message.streamId ?? ""} ${message.state ?? ""}`.trim());
      break;
    case "video":
      if (message.data) {
        videoEl.src = `data:${message.mimeType};base64,${message.data}`;
        videoPlaceholder.classList.add("hidden");
      }
      break;
    case "audio":
      enqueueAudioFrame(message);
      break;
    case "transcript":
      appendTranscript(message);
      break;
    default:
      console.log("Unknown message", message);
  }
}

startButton.addEventListener("click", () => {
  startButton.disabled = true;
  updateStatus("Connecting…");

  activateAudio()
    .then(() => {
      ensureSocket();
    })
    .catch((error) => {
      console.error("Unable to start audio context", error);
      updateStatus("Failed to start audio context. Check console for details.");
      startButton.disabled = false;
    });
});
