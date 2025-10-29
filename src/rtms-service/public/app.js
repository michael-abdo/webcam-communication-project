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
    console.log('WebSocket received message:', message.type, message);
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

// Analytics tracking
let analyticsData = {
  talkTime: {},
  totalTalkTime: 0,
  participantCount: 0,
  equalityScore: 0
};
let analyticsInterval = null;

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
      if (message.state === "joining" || message.state === "started") {
        startAnalyticsUpdates();
      } else if (message.state === "stopped") {
        stopAnalyticsUpdates();
      }
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
    case "analytics":
      console.log('Processing analytics message:', message);
      updateAnalyticsData(message);
      break;
    case "rtms_event":
      // Handle RTMS events (meeting started, stopped, etc)
      updateStatus(`RTMS Event: ${message.event}`);
      if (message.event === "meeting.rtms_started") {
        startAnalyticsUpdates();
      } else if (message.event === "meeting.rtms_stopped") {
        stopAnalyticsUpdates();
      }
      break;
    default:
      console.log("Unknown message", message);
  }
}

// Analytics functions
function updateAnalyticsData(message) {
  const { metric, value, participant_id, tags } = message;
  console.log('updateAnalyticsData:', { metric, value, participant_id, tags });
  
  if (metric === 'talk_time_seconds' && participant_id) {
    if (!analyticsData.talkTime[participant_id]) {
      analyticsData.talkTime[participant_id] = {
        id: participant_id,
        name: tags?.user_name || `Participant ${participant_id.substring(0, 8)}`,
        talkTime: 0,
        words: 0
      };
    }
    analyticsData.talkTime[participant_id].talkTime = value;
  } else if (metric === 'words_spoken' && participant_id) {
    if (!analyticsData.talkTime[participant_id]) {
      analyticsData.talkTime[participant_id] = {
        id: participant_id,
        name: tags?.user_name || `Participant ${participant_id.substring(0, 8)}`,
        talkTime: 0,
        words: 0
      };
    }
    analyticsData.talkTime[participant_id].words = value;
  } else if (metric === 'talk_time_equality') {
    analyticsData.equalityScore = value;
  }
  
  renderTalkTimeChart();
  console.log('Analytics data updated:', analyticsData);
}

function renderTalkTimeChart() {
  const container = document.getElementById('talkTimeContainer');
  const loading = document.getElementById('talkTimeLoading');
  const chart = document.getElementById('talkTimeChart');
  const noData = document.getElementById('talkTimeEmpty');
  const barsContainer = document.getElementById('talkTimeBars');
  
  const participants = Object.values(analyticsData.talkTime);
  
  if (participants.length === 0) {
    loading.style.display = 'none';
    chart.style.display = 'none';
    noData.style.display = 'block';
    return;
  }
  
  loading.style.display = 'none';
  noData.style.display = 'none';
  chart.style.display = 'block';
  
  // Calculate total talk time
  analyticsData.totalTalkTime = participants.reduce((sum, p) => sum + p.talkTime, 0);
  analyticsData.participantCount = participants.length;
  
  // Update stats
  document.getElementById('totalTalkTime').textContent = formatDuration(analyticsData.totalTalkTime);
  document.getElementById('activeSpeakers').textContent = analyticsData.participantCount;
  document.getElementById('equalityScore').textContent = Math.round((analyticsData.equalityScore || 0) * 100) + '%';
  
  // Clear and rebuild bars
  barsContainer.innerHTML = '';
  
  // Sort by talk time
  participants.sort((a, b) => b.talkTime - a.talkTime);
  
  participants.forEach(participant => {
    const percentage = analyticsData.totalTalkTime > 0 
      ? (participant.talkTime / analyticsData.totalTalkTime) * 100 
      : 0;
    
    const barDiv = document.createElement('div');
    barDiv.className = 'participant-bar';
    
    const infoDiv = document.createElement('div');
    infoDiv.className = 'participant-info';
    
    const nameDiv = document.createElement('div');
    nameDiv.className = 'participant-name';
    
    const dot = document.createElement('span');
    dot.className = 'speaker-dot';
    dot.style.backgroundColor = getSpeakerColor(participant.id);
    
    const nameText = document.createElement('span');
    nameText.textContent = participant.name;
    
    nameDiv.appendChild(dot);
    nameDiv.appendChild(nameText);
    
    const statsDiv = document.createElement('div');
    statsDiv.className = 'participant-stats';
    statsDiv.textContent = `${formatDuration(participant.talkTime)} (${Math.round(percentage)}%) - ${participant.words} words`;
    
    infoDiv.appendChild(nameDiv);
    infoDiv.appendChild(statsDiv);
    
    const barContainer = document.createElement('div');
    barContainer.className = 'bar-container';
    
    const barFill = document.createElement('div');
    barFill.className = 'bar-fill';
    barFill.style.width = `${Math.max(percentage, 5)}%`;
    barFill.style.backgroundColor = getSpeakerColor(participant.id);
    barFill.textContent = `${Math.round(percentage)}%`;
    
    barContainer.appendChild(barFill);
    
    barDiv.appendChild(infoDiv);
    barDiv.appendChild(barContainer);
    
    barsContainer.appendChild(barDiv);
  });
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
}

function startAnalyticsUpdates() {
  // Fetch analytics data every 5 seconds
  if (analyticsInterval) return;
  
  analyticsInterval = setInterval(() => {
    // In a real implementation, we might fetch from the API endpoint
    // For now, we rely on WebSocket updates
    console.log('Analytics update check');
  }, 5000);
}

function stopAnalyticsUpdates() {
  if (analyticsInterval) {
    clearInterval(analyticsInterval);
    analyticsInterval = null;
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
