# Phase 1 Capture TODOs

- [ ] **Add structured metrics + alerts** — Extend `blueprints/capture_api.py::record_chunk` to emit `phase1.chunk.uploaded` telemetry via StatsD/cloud metrics and wire alerting for sustained 5xx responses (Phase 1 APIs · Bare Minimum Support: Telemetry).
- [ ] **Reconcile chunk upload contract** — Update `/api/sessions/<id>/chunks` (and capture client) to accept the multipart upload workflow described in Phase 1 APIs.md, or revise the spec to officially bless the current presigned-upload + metadata POST pattern.
