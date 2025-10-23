import crypto from "crypto";
import express from "express";
import rtms from "@zoom/rtms";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

const PORT = Number(process.env.RTMS_SERVICE_PORT || process.env.PORT || 8080);
const WEBHOOK_PATH = process.env.RTMS_WEBHOOK_PATH || "/rtms/webhook";
const AWS_REGION = process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || "us-west-2";
const S3_BUCKET = process.env.S3_BUCKET || process.env.AWS_S3_BUCKET;
const CAPTURE_API_BASE_URL = process.env.CAPTURE_API_BASE_URL
  ? process.env.CAPTURE_API_BASE_URL.replace(/\/$/, "")
  : null;
const CAPTURE_API_TOKEN = process.env.CAPTURE_API_TOKEN;

if (!process.env.ZM_RTMS_CLIENT || !process.env.ZM_RTMS_SECRET) {
  console.error("Missing Zoom RTMS credentials (ZM_RTMS_CLIENT / ZM_RTMS_SECRET)");
  process.exit(1);
}

if (!S3_BUCKET) {
  console.error("Missing S3 bucket (set S3_BUCKET or AWS_S3_BUCKET)");
  process.exit(1);
}

const s3Client = new S3Client({
  region: AWS_REGION,
});

const app = express();
app.use(express.json({ limit: "5mb" }));

const streams = new Map();
let warnedMissingApi = false;

function buildApiUrl(path) {
  if (!CAPTURE_API_BASE_URL) {
    if (!warnedMissingApi) {
      console.warn("CAPTURE_API_BASE_URL not configured; capture metadata will not be recorded.");
      warnedMissingApi = true;
    }
    return null;
  }

  if (!path.startsWith("/")) {
    return `${CAPTURE_API_BASE_URL}/${path}`;
  }
  return `${CAPTURE_API_BASE_URL}${path}`;
}

async function postJson(path, body) {
  const url = buildApiUrl(path);
  if (!url) {
    return null;
  }

  const headers = {
    "Content-Type": "application/json",
  };

  if (CAPTURE_API_TOKEN) {
    headers.Authorization = `Bearer ${CAPTURE_API_TOKEN}`;
  }

  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Capture API ${url} responded ${response.status}: ${text}`);
  }

  const responseText = await response.text();
  return responseText ? JSON.parse(responseText) : null;
}

function buildObjectKey(sessionId, category, sequence, extension) {
  const safeCategory = category.replace(/^\/+|\/+$/g, "") || "recordings";
  const timestamp = new Date().toISOString().replace(/[-:]/g, "").split(".")[0];
  const unique = crypto.randomBytes(4).toString("hex");
  const seq = sequence != null ? String(sequence).padStart(4, "0") : "0000";
  const safeExt = extension.replace(/^\./, "");
  return `${safeCategory}/${sessionId}/${timestamp}_chunk_${seq}_${unique}.${safeExt}`;
}

async function uploadBuffer(sessionId, category, sequence, extension, contentType, buffer) {
  const key = buildObjectKey(sessionId, category, sequence, extension);
  const command = new PutObjectCommand({
    Bucket: S3_BUCKET,
    Key: key,
    Body: buffer,
    ContentType: contentType,
  });
  await s3Client.send(command);
  return key;
}

async function registerSessionWithCapture(streamId, payload) {
  if (!payload?.meeting_uuid) {
    return null;
  }

  try {
    const response = await postJson("/sessions", {
      meeting_uuid: payload.meeting_uuid,
      stream_id: streamId,
      host_id: payload.host_id,
      topic: payload.topic,
      locale: payload.locale,
    });
    return response;
  } catch (error) {
    console.error("Failed to register RTMS session", error.message);
    return null;
  }
}

async function ensureParticipant(state, metadata) {
  const zoomUserId = metadata?.userId ?? metadata?.user_id ?? metadata?.userName;
  if (!zoomUserId) {
    return null;
  }

  const deviceKey = String(zoomUserId);
  if (state.participants.has(deviceKey)) {
    return state.participants.get(deviceKey);
  }

  try {
    const response = await postJson(`/sessions/${state.sessionId}/participants`, {
      zoom_user_id: deviceKey,
      display_name: metadata?.userName,
      status: "active",
    });
    const participantId = response?.participant?.id ?? null;
    state.participants.set(deviceKey, participantId);
    return participantId;
  } catch (error) {
    console.error("Failed to register participant", deviceKey, error.message);
    state.participants.set(deviceKey, null);
    return null;
  }
}

async function registerChunk(state, details) {
  const url = `/sessions/${state.sessionId}/chunks`;
  try {
    await postJson(url, {
      storage_key: details.storageKey,
      checksum: details.checksum,
      duration_ms: details.durationMs,
      sequence_no: details.sequenceNo,
      participant_device_id: details.participantDeviceId ?? null,
    });
  } catch (error) {
    console.error("Failed to record chunk metadata", error.message);
  }
}

async function handleAudioFrame(state, buffer, metadata) {
  const participantId = await ensureParticipant(state, metadata);
  const participantDeviceId = metadata?.userId ?? metadata?.user_id ?? metadata?.userName ?? null;
  const checksum = crypto.createHash("sha256").update(buffer).digest("hex");
  const durationMs = Math.round((buffer.length / 2 / 16000) * 1000);
  const sequenceNo = state.nextSequence++;

  try {
    const storageKey = await uploadBuffer(
      state.sessionId,
      "audio",
      sequenceNo,
      "pcm16",
      "audio/raw",
      buffer,
    );

    await registerChunk(state, {
      storageKey,
      checksum,
      durationMs,
      sequenceNo,
      participantDeviceId: participantDeviceId ? String(participantDeviceId) : null,
    });
  } catch (error) {
    console.error("Audio processing failed", error.message);
  }
}

async function handleVideoFrame(state, buffer) {
  const checksum = crypto.createHash("sha256").update(buffer).digest("hex");
  const sequenceNo = state.nextSequence++;
  const durationMs = Math.round(1000 / 15);

  try {
    const storageKey = await uploadBuffer(
      state.sessionId,
      "video",
      sequenceNo,
      "jpg",
      "image/jpeg",
      buffer,
    );

    await registerChunk(state, {
      storageKey,
      checksum,
      durationMs,
      sequenceNo,
      participantDeviceId: null,
    });
  } catch (error) {
    console.error("Video processing failed", error.message);
  }
}

async function handleTranscript(state, buffer) {
  const checksum = crypto.createHash("sha256").update(buffer).digest("hex");
  const sequenceNo = state.nextSequence++;

  try {
    const storageKey = await uploadBuffer(
      state.sessionId,
      "transcripts",
      sequenceNo,
      "txt",
      "text/plain",
      buffer,
    );

    await registerChunk(state, {
      storageKey,
      checksum,
      durationMs: 0,
      sequenceNo,
      participantDeviceId: null,
    });
  } catch (error) {
    console.error("Transcript processing failed", error.message);
  }
}

function configureClient(client, streamState) {
  const videoParams = {
    contentType: rtms.VideoContentType.RAW_VIDEO,
    codec: rtms.VideoCodec.JPG,
    resolution: rtms.VideoResolution.SD,
    dataOpt: rtms.VideoDataOption.VIDEO_MIXED_GALLERY_VIEW,
    fps: 15,
  };

  const audioParams = {
    contentType: rtms.AudioContentType.RAW_AUDIO,
    codec: rtms.AudioCodec.L16,
    sampleRate: rtms.AudioSampleRate.SR_16K,
    channel: rtms.AudioChannel.MONO,
    dataOpt: rtms.AudioDataOption.AUDIO_MULTI_STREAMS,
    duration: 20,
    frameSize: 320,
  };

  client.setVideoParams(videoParams);
  client.setAudioParams(audioParams);

  client.onAudioData(async (data, size, timestamp, metadata) => {
    try {
      await handleAudioFrame(streamState, Buffer.from(data), metadata);
    } catch (error) {
      console.error("Audio callback error", error.message);
    }
  });

  client.onVideoData(async (data, size, timestamp, metadata) => {
    try {
      await handleVideoFrame(streamState, Buffer.from(data));
    } catch (error) {
      console.error("Video callback error", error.message);
    }
  });

  client.onTranscriptData(async (data, size, timestamp, metadata) => {
    try {
      await handleTranscript(streamState, Buffer.from(data));
    } catch (error) {
      console.error("Transcript callback error", error.message);
    }
  });
}

async function ensureStream(streamId, payload) {
  if (streams.has(streamId)) {
    return streams.get(streamId);
  }

  let sessionId = (payload?.meeting_uuid || streamId || "rtms").replace(/[^a-zA-Z0-9_-]/g, "");

  const apiResponse = await registerSessionWithCapture(streamId, payload);
  if (apiResponse?.session_id) {
    sessionId = apiResponse.session_id;
  }

  const client = new rtms.Client();
  const streamState = {
    client,
    sessionId,
    meetingUuid: payload?.meeting_uuid || null,
    nextSequence: 0,
    participants: new Map(),
  };
  configureClient(client, streamState);
  streams.set(streamId, streamState);
  return streamState;
}

function stopStream(streamId) {
  const state = streams.get(streamId);
  if (!state) return;
  try {
    state.client.leave();
  } catch (err) {
    console.error("Error leaving RTMS stream", streamId, err);
  }
  streams.delete(streamId);
}

app.post(WEBHOOK_PATH, async (req, res) => {
  const { event, payload } = req.body || {};
  const streamId = payload?.rtms_stream_id;

  if (!streamId) {
    console.warn("Webhook without stream id", event);
    return res.status(200).json({ status: "ignored" });
  }

  if (event === "meeting.rtms_started") {
    try {
      const state = await ensureStream(streamId, payload);
      console.log("Joining RTMS stream", streamId, "session", state.sessionId);
      state.client.join(payload);
    } catch (error) {
      console.error("Failed to start RTMS stream", streamId, error.message);
    }
  } else if (event === "meeting.rtms_stopped") {
    console.log("Stopping RTMS stream", streamId);
    stopStream(streamId);
  } else {
    console.log("Unhandled RTMS event", event);
  }

  res.json({ status: "ok" });
});

app.get("/healthz", (_req, res) => {
  res.json({ status: "ok", activeStreams: streams.size });
});

app.listen(PORT, () => {
  console.log(`RTMS service listening on port ${PORT} (webhook path ${WEBHOOK_PATH})`);
});

process.on("SIGTERM", () => {
  console.log("Shutting down RTMS service");
  for (const streamId of streams.keys()) {
    stopStream(streamId);
  }
  process.exit(0);
});
