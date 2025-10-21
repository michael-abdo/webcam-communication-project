# Phase 1 Capture TODOs

- [ ] **Add structured metrics + alerts** — Extend `blueprints/capture_api.py::record_chunk` to emit `phase1.chunk.uploaded` telemetry via StatsD/cloud metrics and wire alerting for sustained 5xx responses (Phase 1 APIs · Bare Minimum Support: Telemetry).
- [ ] **Reconcile chunk upload contract** — Update `/api/sessions/<id>/chunks` (and capture client) to accept the multipart upload workflow described in Phase 1 APIs.md, or revise the spec to officially bless the current presigned-upload + metadata POST pattern.
- [x] **Build validation dashboard** — Replace the in-memory `/tests/results` flow with a DB-backed reviewer experience that lists Phase 1 sessions and surfaces raw media/transcript/log status (`app_lightweight.py`, `templates/tests/test_results.html`) to satisfy Phase 1 Output requirements.
- [x] **Service: list recent sessions** — Add a helper in `services/capture_service.py` that returns recent sessions with participant and chunk counts for reviewer dashboards.
- [x] **API: GET /api/sessions list** — Implement a JSON listing route in `blueprints/capture_api.py` (and associated tests) that surfaces recent sessions for the new dashboard.
- [x] **UI Route: /phase1/sessions page** — Add a Flask route in `app_lightweight.py` plus template plumbing to render the Phase 1 session list.
- [x] **Template & JS: phase1 session dashboard** — Create `templates/phase1_sessions.html` and accompanying JS under `static/js/` that fetches the new APIs, displays session tables, and shows chunk details.
- [x] **Tests: Cover new GET endpoints** — Extend `tests/test_capture_api.py` with assertions for the list endpoint (and chunk fetch if added).
- [x] **Docs: Document reviewer tooling** — Update `README.md` (Phase 1 section) describing the new validation dashboard and how to run it.
