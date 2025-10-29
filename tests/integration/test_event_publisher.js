#!/usr/bin/env node
/**
 * Test Event Publisher for Analytics Services
 * 
 * This script simulates RTMS events to test the analytics pipeline.
 * It publishes various event types to Redis for analytics services to consume.
 */

const Redis = require('ioredis');
const { v4: uuidv4 } = require('uuid');

// Configuration
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const SESSION_ID = process.argv[2] || `test-session-${Date.now()}`;
const DURATION_SECONDS = parseInt(process.argv[3]) || 60; // Default 60 seconds

// Test participants
const PARTICIPANTS = [
  { id: uuidv4(), userId: 'zoom_user_1', userName: 'Alice Johnson' },
  { id: uuidv4(), userId: 'zoom_user_2', userName: 'Bob Smith' },
  { id: uuidv4(), userId: 'zoom_user_3', userName: 'Charlie Brown' },
];

// Sample transcript phrases
const PHRASES = [
  "I think we should focus on the main objectives",
  "That's a great point, let me add to that",
  "Can we circle back to the previous topic?",
  "I agree with the proposed approach",
  "Let me share my screen to show you",
  "Does anyone have any questions?",
  "We need to consider the timeline",
  "That makes sense from my perspective",
  "I have a different viewpoint on this",
  "Let's schedule a follow-up meeting",
];

class TestEventPublisher {
  constructor() {
    this.redis = new Redis(REDIS_URL);
    this.startTime = Date.now();
    this.sequenceNumbers = new Map();
    this.eventCount = 0;
  }

  async connect() {
    try {
      await this.redis.ping();
      console.log('✓ Connected to Redis at', REDIS_URL);
      return true;
    } catch (error) {
      console.error('✗ Failed to connect to Redis:', error.message);
      return false;
    }
  }

  createEvent(eventType, data, participantId = null) {
    const event = {
      eventId: uuidv4(),
      eventType,
      sessionId: SESSION_ID,
      timestamp: Date.now(),
      data: {
        ...data,
        ...(participantId && {
          participantId,
          ...PARTICIPANTS.find(p => p.id === participantId),
        }),
      },
      metadata: {
        rtmsStreamId: `stream-${SESSION_ID}`,
        processingTime: new Date().toISOString(),
        version: '1.0',
      },
    };

    return event;
  }

  async publishEvent(channel, event) {
    try {
      const message = JSON.stringify(event);
      await this.redis.publish(channel, message);
      this.eventCount++;
      console.log(`→ Published ${event.eventType} event to ${channel}`);
    } catch (error) {
      console.error(`✗ Failed to publish event:`, error.message);
    }
  }

  getNextSequenceNo(participantId) {
    const current = this.sequenceNumbers.get(participantId) || 0;
    this.sequenceNumbers.set(participantId, current + 1);
    return current + 1;
  }

  async publishSessionStart() {
    const event = this.createEvent('session', {
      action: 'start',
      participantCount: PARTICIPANTS.length,
      meetingId: `meeting-${SESSION_ID}`,
      hostId: PARTICIPANTS[0].id,
    });

    await this.publishEvent('analytics:session', event);
  }

  async publishSessionEnd() {
    const duration = (Date.now() - this.startTime) / 1000;
    const event = this.createEvent('session', {
      action: 'end',
      duration: Math.round(duration),
      totalEvents: this.eventCount,
      participantCount: PARTICIPANTS.length,
    });

    await this.publishEvent('analytics:session', event);
  }

  async publishParticipantJoin(participant) {
    const event = this.createEvent(
      'participant',
      {
        action: 'join',
        joinTime: new Date().toISOString(),
      },
      participant.id
    );

    await this.publishEvent('analytics:participant', event);
  }

  async publishAudioChunk(participantId, duration = 160) {
    const sequenceNo = this.getNextSequenceNo(participantId);
    const event = this.createEvent(
      'audio',
      {
        duration, // milliseconds
        s3Key: `audio/${SESSION_ID}/participant_${participantId}/chunk_${sequenceNo}.pcm16`,
        size: (16000 * duration) / 1000, // 16kHz sample rate
        sampleRate: 16000,
        channels: 1,
        sequenceNo,
      },
      participantId
    );

    await this.publishEvent('analytics:audio', event);
  }

  async publishTranscript(participantId, text) {
    const words = text.split(' ');
    const duration = words.length * 0.3; // ~0.3 seconds per word
    const startTime = (Date.now() - this.startTime) / 1000;

    const event = this.createEvent(
      'transcript',
      {
        text,
        startTime,
        endTime: startTime + duration,
        confidence: 0.85 + Math.random() * 0.1,
        language: 'en',
        wordCount: words.length,
      },
      participantId
    );

    await this.publishEvent('analytics:transcript', event);

    // Also publish corresponding audio chunks
    const chunks = Math.ceil((duration * 1000) / 160); // 160ms chunks
    for (let i = 0; i < chunks; i++) {
      await this.publishAudioChunk(participantId);
      await this.sleep(50); // Small delay between chunks
    }
  }

  async publishVideoFrame(participantId) {
    const event = this.createEvent(
      'video',
      {
        frameNumber: this.getNextSequenceNo(`${participantId}-video`),
        timestamp: Date.now(),
        width: 1280,
        height: 720,
        format: 'I420',
        s3Key: `video/${SESSION_ID}/participant_${participantId}/frame.jpg`,
      },
      participantId
    );

    await this.publishEvent('analytics:video', event);
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async runSimulation() {
    console.log('\n🎬 Starting event simulation...');
    console.log(`📍 Session ID: ${SESSION_ID}`);
    console.log(`⏱  Duration: ${DURATION_SECONDS} seconds`);
    console.log(`👥 Participants: ${PARTICIPANTS.length}\n`);

    // Start session
    await this.publishSessionStart();

    // Participants join
    for (const participant of PARTICIPANTS) {
      await this.publishParticipantJoin(participant);
      await this.sleep(500);
    }

    // Main simulation loop
    const endTime = this.startTime + DURATION_SECONDS * 1000;
    let lastVideoTime = Date.now();
    let currentSpeaker = 0;

    while (Date.now() < endTime) {
      // Simulate conversation - one person speaks at a time
      const participant = PARTICIPANTS[currentSpeaker];
      const phrase = PHRASES[Math.floor(Math.random() * PHRASES.length)];

      // Publish transcript and audio
      await this.publishTranscript(participant.id, phrase);

      // Publish video frames periodically (every 1 second)
      if (Date.now() - lastVideoTime > 1000) {
        for (const p of PARTICIPANTS) {
          await this.publishVideoFrame(p.id);
        }
        lastVideoTime = Date.now();
      }

      // Switch speaker
      currentSpeaker = (currentSpeaker + 1) % PARTICIPANTS.length;

      // Random pause between speakers (0.5-2 seconds)
      await this.sleep(500 + Math.random() * 1500);

      // Show progress
      const elapsed = Math.round((Date.now() - this.startTime) / 1000);
      const progress = Math.round((elapsed / DURATION_SECONDS) * 100);
      process.stdout.write(`\r⏳ Progress: ${progress}% (${elapsed}/${DURATION_SECONDS}s)`);
    }

    // End session
    console.log('\n');
    await this.publishSessionEnd();

    console.log(`\n✅ Simulation complete!`);
    console.log(`📊 Total events published: ${this.eventCount}`);
  }

  async disconnect() {
    await this.redis.quit();
    console.log('\n👋 Disconnected from Redis');
  }
}

// Main execution
async function main() {
  console.log('=================================');
  console.log('  Analytics Event Test Publisher ');
  console.log('=================================\n');

  const publisher = new TestEventPublisher();

  // Connect to Redis
  const connected = await publisher.connect();
  if (!connected) {
    process.exit(1);
  }

  // Check for analytics services
  const subscribers = await publisher.redis.pubsub('numsub', 
    'analytics:audio',
    'analytics:transcript',
    'analytics:video',
    'analytics:session',
    'analytics:participant'
  );

  console.log('\n📡 Current analytics service subscribers:');
  for (let i = 0; i < subscribers.length; i += 2) {
    console.log(`   ${subscribers[i]}: ${subscribers[i + 1]} subscribers`);
  }
  console.log('');

  // Run simulation
  try {
    await publisher.runSimulation();
  } catch (error) {
    console.error('\n✗ Simulation error:', error.message);
  } finally {
    await publisher.disconnect();
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\n🛑 Received interrupt signal, shutting down...');
  process.exit(0);
});

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = TestEventPublisher;
