import Redis from "ioredis";
import { v4 as uuidv4 } from "uuid";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";

/**
 * EventPublisher handles publishing RTMS events to Redis pub/sub channels
 * and optionally stores them in S3 for replay capability
 */
class EventPublisher {
  constructor(redisConfig = {}, s3Config = {}) {
    // Initialize Redis client
    this.redis = new Redis({
      host: redisConfig.host || process.env.REDIS_HOST || "localhost",
      port: redisConfig.port || process.env.REDIS_PORT || 6379,
      password: redisConfig.password || process.env.REDIS_PASSWORD,
      retryStrategy: (times) => Math.min(times * 50, 2000),
      enableOfflineQueue: true,
      maxRetriesPerRequest: 3,
    });

    // S3 client for event store (optional)
    if (s3Config.bucket || process.env.EVENT_STORE_BUCKET) {
      this.s3Client = new S3Client({
        region: s3Config.region || process.env.AWS_REGION || "us-west-2",
      });
      this.eventStoreBucket = s3Config.bucket || process.env.EVENT_STORE_BUCKET;
    }

    // Event schema version
    this.schemaVersion = "1.0";

    // Metrics
    this.metrics = {
      published: 0,
      failed: 0,
      stored: 0,
    };

    // Setup error handling
    this.redis.on("error", (err) => {
      console.error("[EventPublisher] Redis error:", err);
    });

    this.redis.on("connect", () => {
      console.log("[EventPublisher] Connected to Redis");
    });
  }

  /**
   * Create base event structure
   */
  createBaseEvent(eventType, sessionId, streamId) {
    return {
      eventId: uuidv4(),
      eventType,
      sessionId,
      timestamp: Date.now(),
      metadata: {
        rtmsStreamId: streamId,
        processingTime: new Date().toISOString(),
        version: this.schemaVersion,
      },
    };
  }

  /**
   * Publish audio event
   */
  async publishAudioEvent(state, audioData) {
    const event = {
      ...this.createBaseEvent("audio", state.sessionId, state.streamId),
      data: {
        participantId: audioData.participantId,
        userId: audioData.userId,
        userName: audioData.userName,
        chunkId: uuidv4(),
        duration: audioData.duration,
        s3Key: audioData.s3Key,
        size: audioData.size,
        sampleRate: audioData.sampleRate || 16000,
        channels: audioData.channels || 1,
        sequenceNo: audioData.sequenceNo,
      },
    };

    const result = await this.publish("rtms:events:audio", event);
    if (result.success && state.eventCount !== undefined) {
      state.eventCount++;
    }
    return result;
  }

  /**
   * Publish video event
   */
  async publishVideoEvent(state, videoData) {
    const event = {
      ...this.createBaseEvent("video", state.sessionId, state.streamId),
      data: {
        participantId: videoData.participantId,
        userId: videoData.userId,
        userName: videoData.userName,
        frameId: uuidv4(),
        s3Key: videoData.s3Key,
        size: videoData.size,
        mimeType: videoData.mimeType || "image/jpeg",
        sequenceNo: videoData.sequenceNo,
        resolution: videoData.resolution,
      },
    };

    const result = await this.publish("rtms:events:video", event);
    if (result.success && state.eventCount !== undefined) {
      state.eventCount++;
    }
    return result;
  }

  /**
   * Publish transcript event
   */
  async publishTranscriptEvent(state, transcriptData) {
    const event = {
      ...this.createBaseEvent("transcript", state.sessionId, state.streamId),
      data: {
        participantId: transcriptData.participantId,
        userId: transcriptData.userId,
        userName: transcriptData.userName,
        text: transcriptData.text,
        startTime: transcriptData.startTime,
        endTime: transcriptData.endTime,
        confidence: transcriptData.confidence || 0.95,
        language: transcriptData.language || "en",
        words: transcriptData.words,
      },
    };

    const result = await this.publish("rtms:events:transcript", event);
    if (result.success && state.eventCount !== undefined) {
      state.eventCount++;
    }
    return result;
  }

  /**
   * Publish session event
   */
  async publishSessionEvent(state, action, additionalData = {}) {
    const event = {
      ...this.createBaseEvent("session", state.sessionId, state.streamId),
      data: {
        action,
        meetingUuid: state.meetingUuid,
        ...additionalData,
      },
    };

    const result = await this.publish("rtms:events:session", event);
    if (result.success && state.eventCount !== undefined) {
      state.eventCount++;
    }
    return result;
  }

  /**
   * Publish participant event
   */
  async publishParticipantEvent(state, participantData, action) {
    const event = {
      ...this.createBaseEvent("participant", state.sessionId, state.streamId),
      data: {
        participantId: participantData.participantId,
        userId: participantData.userId,
        userName: participantData.userName,
        action,
        role: participantData.role,
      },
    };

    const result = await this.publish("rtms:events:participant", event);
    if (result.success && state.eventCount !== undefined) {
      state.eventCount++;
    }
    return result;
  }

  /**
   * Core publish method
   */
  async publish(channel, event) {
    try {
      // Serialize event
      const eventJson = JSON.stringify(event);

      // Publish to Redis
      await this.redis.publish(channel, eventJson);
      this.metrics.published++;

      // Store in S3 if configured (async, don't wait)
      if (this.eventStoreBucket) {
        this.storeEvent(event).catch((err) => {
          console.error("[EventPublisher] Failed to store event:", err);
        });
      }

      return { success: true, eventId: event.eventId };
    } catch (error) {
      this.metrics.failed++;
      console.error(`[EventPublisher] Failed to publish to ${channel}:`, error);
      
      // Attempt to store failed event for replay
      if (this.eventStoreBucket) {
        await this.storeFailedEvent(channel, event, error);
      }

      return { success: false, error: error.message };
    }
  }

  /**
   * Store event in S3 for replay capability
   */
  async storeEvent(event) {
    const key = `events/${event.sessionId}/${event.eventType}/${event.timestamp}_${event.eventId}.json`;
    
    try {
      await this.s3Client.send(
        new PutObjectCommand({
          Bucket: this.eventStoreBucket,
          Key: key,
          Body: JSON.stringify(event),
          ContentType: "application/json",
          Metadata: {
            eventType: event.eventType,
            sessionId: event.sessionId,
            timestamp: String(event.timestamp),
          },
        })
      );
      this.metrics.stored++;
    } catch (error) {
      console.error("[EventPublisher] Failed to store event in S3:", error);
      throw error;
    }
  }

  /**
   * Store failed events for later replay
   */
  async storeFailedEvent(channel, event, error) {
    const failedEvent = {
      ...event,
      _failed: {
        channel,
        error: error.message,
        timestamp: Date.now(),
      },
    };

    const key = `failed-events/${event.sessionId}/${event.timestamp}_${event.eventId}.json`;
    
    try {
      await this.s3Client.send(
        new PutObjectCommand({
          Bucket: this.eventStoreBucket,
          Key: key,
          Body: JSON.stringify(failedEvent),
          ContentType: "application/json",
        })
      );
    } catch (s3Error) {
      console.error("[EventPublisher] Failed to store failed event:", s3Error);
    }
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return { ...this.metrics };
  }

  /**
   * Cleanup
   */
  async close() {
    await this.redis.quit();
  }
}

// Export singleton instance
export const eventPublisher = new EventPublisher();

// Also export class for testing
export { EventPublisher };