# Phase 2 Transition Plan

## Overview
- **Goal:** Move from Phase 1's file-based ingestion to Phase 2's Zoom-driven capture so facilitators can run live meetings end-to-end inside the Xenodex dashboard.
- **Success Guardrails:** Zoom intake flows without manual cleanup, capture bot + transcription stay inside acceptable freshness, and facilitators can manage meetings entirely from the dashboard.
- **Primary Dependencies:** Zoom Video SDK/native capture worker, facilitator dashboard feature flag, credential vault references for Zoom tokens.

## Core Workstreams

### Input – Zoom Intake & Consent
- Ship the Zoom lobby experience with deep-link entry, name prompt, roster sync, and consent capture.
- Register capture bot credentials and heartbeat the worker so it stays aligned with the meeting.
- Relay participant events (`POST /zoom-participants/{id}/events`) downstream to throughput and output teams.
- Coordinate with UX for join flow screens and with API/data owners on payload definitions.

### Throughput – Live Transcription & Analytics
- Ingest Zoom audio, context, and events from the capture bot into transcription and analytics workers.
- Maintain talk-time and interruption metrics with minimal drift; persist history for later replay.
- Monitor for scaling risks: lag under larger rooms, capture bot disconnects, Zoom rate limits.
- Share schemas defined in `Phase 2 Tables` across services to avoid payload drift.

### Output – Facilitator Dashboard
- Deliver live transcripts, speaker activity, and key event feeds in the facilitator dashboard.
- Support facilitator controls (filters/flags) that feed back into the analytics pipeline.
- Ensure the UI responds instantly to roster updates and remains performant on lower-end devices.
- Align with UX reference screens and accessibility requirements (captions, contrast, keyboard navigation).

## APIs, Data, and Telemetry
- Endpoints: `POST /sessions/{id}/zoom`, `POST /sessions/{id}/zoom/heartbeat`, `POST /zoom-participants/{id}/events`, `GET /sessions/{id}/transcript`, `GET /sessions/{id}/analytics`, `/ws/sessions/{id}`.
- Schema Additions: `zoom_sessions`, `zoom_participants`, `transcripts`, `analytics_metrics`, `session_events` with referential integrity to existing `sessions`.
- Observability: emit `zoom.event.ingested`, `analytics.response.ms`, `phase2.participant.joined/exited`, and alert on WebSocket disconnect or transcript queue backlog.
- Security & Data: require facilitator/admin scopes, respect consent flags, mask participant names in logs, store only vault references for Zoom tokens.

## Release & Risk Management
- Feature flags: `phase2_zoom_ui` (intake), `phase2_zoom_enabled` (APIs/workers); provide rollback playbooks using flags plus queue drain.
- Migrations: run staged migrations for new tables with backfill scripts; include automated tests covering duplicate joins and transcript pagination.
- Coordination checkpoints: UX + Input on lobby flow, Platform + Throughput on worker cadence, Output + Throughput on WebSocket payload cadence.
- Escalation triggers: consent flow failures, transcription freshness slipping, dashboard latency/regressions, or capture bot heartbeat breaks.

## Immediate Next Actions
1. Sequence Zoom SDK capture-bot integration and credentials handoff with platform owners.
2. Finalize API contracts and migrations so Input/Output teams can hook into real data.
3. Stand up end-to-end smoke test (Zoom lobby → capture bot → analytics → dashboard) behind feature flags before widening access.
