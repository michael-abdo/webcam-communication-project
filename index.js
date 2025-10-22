import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import http from "http";
import express from "express";
import { WebSocketServer, WebSocket } from "ws";
import rtms from "@zoom/rtms";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = parseInt(process.env.PORT || "5000", 10);
const WEBHOOK_PATH = process.env.ZM_RTMS_PATH || "/zoom-webhook";
const LOG_DIR = path.join(__dirname, "logs");

fs.mkdirSync(LOG_DIR, { recursive: true });

const app = express();
app.use(express.static(path.join(__dirname, "public")));
app.use(express.json({ limit: "1mb" }));

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/rtms" });

function broadcast(message) {
  const payload = JSON.stringify(message);

  wss.clients.forEach((socket) => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(payload);
    }
  });
}

wss.on("connection", (socket) => {
  console.log("[ws] Client connected");

  socket.on("close", () => {
    console.log("[ws] Client disconnected");
  });
});

const streamClients = new Map();

function handleMeetingEvent(body) {
  const event = body?.event;
  const payload = body?.payload;
  const streamId = payload?.rtms_stream_id;
  const meetingUuid = payload?.meeting_uuid;

  console.log(
    `[webhook] event=${event ?? "unknown"} streamId=${streamId ?? "none"} meeting=${meetingUuid ?? "none"}`
  );

  if (!streamId) {
    console.log(`[rtms] Ignoring event without stream ID: ${event ?? "unknown"}`);
    return;
  }

  if (event === "meeting.rtms_stopped") {
    const client = streamClients.get(streamId);

    if (client) {
      client.leave();
      streamClients.delete(streamId);
      console.log(`[rtms] Stream stopped for ${streamId}`);
      broadcast({ type: "status", streamId, state: "stopped" });
    } else {
      console.log(`[rtms] Received stop event for unknown stream ${streamId}`);
    }

    return;
  }

  if (event !== "meeting.rtms_started") {
    console.log(`[rtms] Ignoring unsupported event ${event}`);
    return;
  }

  const client = new rtms.Client();
  streamClients.set(streamId, client);

  const audioParams = {
    contentType: rtms.AudioContentType.RAW_AUDIO,
    codec: rtms.AudioCodec.L16,
    sampleRate: rtms.AudioSampleRate.SR_16K,
    channel: rtms.AudioChannel.MONO,
    dataOpt: rtms.AudioDataOption.AUDIO_MIXED_STREAM,
    duration: 20,
    frameSize: 320,
  };

  const videoParams = {
    contentType: rtms.VideoContentType.RAW_VIDEO,
    codec: rtms.VideoCodec.JPG,
    resolution: rtms.VideoResolution.SD,
    dataOpt: rtms.VideoDataOption.VIDEO_SINGLE_ACTIVE_STREAM,
    fps: 15,
  };

  client.setAudioParams(audioParams);
  client.setVideoParams(videoParams);
  client.setDeskshareParams(videoParams);

  client.onTranscriptData((data, size, timestamp, metadata) => {
    broadcast({
      type: "transcript",
      streamId,
      size,
      timestamp,
      userName: metadata.userName,
      text: data.toString(),
    });
  });

  client.onAudioData((data, size, timestamp, metadata) => {
    broadcast({
      type: "audio",
      streamId,
      size,
      timestamp,
      userName: metadata.userName,
      sampleRate: 16000,
      channels: 1,
      encoding: "PCM16",
      data: Buffer.from(data).toString("base64"),
    });
  });

  client.onVideoData((data, size, timestamp, metadata) => {
    broadcast({
      type: "video",
      streamId,
      size,
      timestamp,
      userName: metadata.userName,
      mimeType: "image/jpeg",
      data: Buffer.from(data).toString("base64"),
    });
  });

  client.onDeskshareData((data, size, timestamp, metadata) => {
    broadcast({
      type: "deskshare",
      streamId,
      size,
      timestamp,
      userName: metadata.userName,
      mimeType: "image/jpeg",
      data: Buffer.from(data).toString("base64"),
    });
  });

  broadcast({ type: "status", streamId, state: "starting" });
  console.log(`[rtms] Joining meeting for stream ${streamId}`);
  client.join(payload);
}

app.post(WEBHOOK_PATH, (req, res) => {
  handleMeetingEvent(req.body);
  res.json({ status: "ok" });
});

app.all(WEBHOOK_PATH, (_req, res) => {
  res.status(405).json({ error: "Method Not Allowed" });
});

app.get("/healthz", (_req, res) => {
  res.json({ status: "ok" });
});

server.listen(PORT, () => {
  console.log(`[server] Listening at http://localhost:${PORT}`);
  console.log(`[server] Webhook path: ${WEBHOOK_PATH}`);
});
