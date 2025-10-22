import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import http from "http";
import express from "express";
import { WebSocketServer, WebSocket } from "ws";
import rtms from "@zoom/rtms";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const UI_PORT = parseInt(process.env.UI_PORT || "3200", 10);
const LOG_DIR = path.join(__dirname, "logs");

fs.mkdirSync(LOG_DIR, { recursive: true });

const app = express();
app.use(express.static(path.join(__dirname, "public")));

const httpServer = http.createServer(app);
const wss = new WebSocketServer({ server: httpServer, path: "/rtms" });

httpServer.listen(UI_PORT, () => {
  console.log(`[ui] Listening at http://localhost:${UI_PORT}`);
});

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

rtms.onWebhookEvent(({ event, payload }) => {
  const streamId = payload?.rtms_stream_id;

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
});
