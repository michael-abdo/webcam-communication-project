let tokenInput = null;
let limitInput = null;
let sessionsTableBody = null;
let sessionDetail = null;
let statusMessage = null;
let errorContainer = null;
let activeSessionId = null;

document.addEventListener('DOMContentLoaded', () => {
    tokenInput = document.getElementById('apiTokenInput');
    limitInput = document.getElementById('limitInput');
    sessionsTableBody = document.getElementById('sessionsTableBody');
    sessionDetail = document.getElementById('sessionDetail');
    statusMessage = document.getElementById('statusMessage');
    errorContainer = document.getElementById('errorContainer');

    if (tokenInput) {
        const saved = localStorage.getItem('captureApiToken');
        if (saved) {
            tokenInput.value = saved;
        }
        tokenInput.addEventListener('input', () => {
            localStorage.setItem('captureApiToken', tokenInput.value.trim());
        });
    }

    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            activeSessionId = null;
            clearSessionDetail();
            loadSessions();
        });
    }

    loadSessions();
});

function authHeaders() {
    const token = tokenInput ? tokenInput.value.trim() : '';
    if (!token) {
        return {};
    }
    return {
        Authorization: `Bearer ${token}`,
    };
}

function showStatus(message, type = 'info') {
    if (!statusMessage) return;
    statusMessage.textContent = message;
    statusMessage.style.color = type === 'error' ? '#b91c1c' : '#475569';
}

function clearErrors() {
    if (errorContainer) {
        errorContainer.innerHTML = '';
    }
}

function showError(message) {
    if (!errorContainer) return;
    const div = document.createElement('div');
    div.className = 'error-banner';
    div.textContent = message;
    errorContainer.appendChild(div);
}

function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatStatusValue(status) {
    if (!status) return 'unknown';
    return status.replace(/_/g, ' ');
}

function statusClass(status) {
    switch ((status || '').toLowerCase()) {
        case 'ok':
        case 'completed':
            return 'success';
        case 'attention_required':
        case 'failed':
            return 'warning';
        case 'not_available':
        default:
            return 'muted';
    }
}

function renderStatusPill(status) {
    const cls = statusClass(status);
    const label = escapeHtml(formatStatusValue(status));
    return `<span class="pill ${cls}">${label}</span>`;
}

async function loadSessions() {
    clearErrors();
    showStatus('Loading sessions...');
    const limit = limitInput ? Math.min(Math.max(Number(limitInput.value) || 20, 1), 100) : 20;

    try {
        const response = await fetch(`/api/sessions?limit=${limit}`, {
            headers: {
                'Content-Type': 'application/json',
                ...authHeaders(),
            },
        });

        if (response.status === 401 || response.status === 403) {
            showStatus('Authorization required. Provide a valid Capture API token.', 'error');
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to load sessions (${response.status})`);
        }

        const payload = await response.json();
        renderSessions(payload.sessions || []);
        showStatus(`Loaded ${payload.count || 0} session(s).`);
    } catch (err) {
        console.error(err);
        showError(err.message || 'Failed to load sessions.');
        showStatus('Unable to load sessions.', 'error');
    }
}

function renderSessions(sessions) {
    if (!sessionsTableBody) return;
    sessionsTableBody.innerHTML = '';

    if (sessions.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 9;
        cell.style.textAlign = 'center';
        cell.style.padding = '32px 0';
        cell.style.color = '#64748b';
        cell.textContent = 'No sessions have been recorded yet.';
        row.appendChild(cell);
        sessionsTableBody.appendChild(row);
        return;
    }

    sessions.forEach((session) => {
        const row = document.createElement('tr');
        row.dataset.sessionId = session.id;
        if (session.id === activeSessionId) {
            row.classList.add('active');
        }

        row.innerHTML = `
            <td>${escapeHtml(session.facilitator_id || '—')}</td>
            <td>${escapeHtml(session.device_kind || '—')}</td>
            <td>${formatDate(session.consent_at)}</td>
            <td><span class="pill muted">${session.participant_count}</span></td>
            <td><span class="pill ${session.chunk_count > 0 ? 'success' : 'muted'}">${session.chunk_count}</span></td>
            <td>${renderStatusPill(session.transcript_status)}</td>
            <td>${renderStatusPill(session.log_status)}</td>
            <td>${renderStatusPill(session.alert_state)}</td>
            <td>${formatDate(session.latest_chunk_at) || '—'}</td>
        `;

        row.addEventListener('click', () => {
            document.querySelectorAll('#sessionsTableBody tr').forEach((tr) => tr.classList.remove('active'));
            row.classList.add('active');
            activeSessionId = session.id;
            loadSessionDetail(session.id);
        });

        sessionsTableBody.appendChild(row);
    });
}

function clearSessionDetail() {
    if (!sessionDetail) return;
    sessionDetail.innerHTML = `
        <div class="empty-state">
            Select a session to view consent, device readiness, and chunk manifest.
        </div>
    `;
}

async function loadSessionDetail(sessionId) {
    if (!sessionDetail) return;
    clearErrors();
    sessionDetail.innerHTML = '<div class="empty-state">Loading session details…</div>';

    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            headers: {
                'Content-Type': 'application/json',
                ...authHeaders(),
            },
        });

        if (response.status === 401 || response.status === 403) {
            showStatus('Authorization required. Provide a valid Capture API token.', 'error');
            clearSessionDetail();
            return;
        }

        if (!response.ok) {
            throw new Error(`Failed to load session ${sessionId} (${response.status})`);
        }

        const session = await response.json();
        renderSessionDetail(session);
    } catch (err) {
        console.error(err);
        showError(err.message || 'Failed to load session details.');
        clearSessionDetail();
    }
}

function renderSessionDetail(session) {
    if (!sessionDetail) return;

    const participants = session.participants || [];
    const chunks = session.chunks || [];

    sessionDetail.innerHTML = `
        <div>
            <h3>Session ${session.id}</h3>
            <dl>
                <dt>Facilitator</dt>
                <dd>${escapeHtml(session.facilitator_id || '—')}</dd>

                <dt>Consent At</dt>
                <dd>${formatDate(session.consent_at)}</dd>

                <dt>Device Kind</dt>
                <dd>${escapeHtml(session.device_kind || '—')}</dd>

                <dt>Locale</dt>
                <dd>${escapeHtml(session.locale || '—')}</dd>

                <dt>Participants</dt>
                <dd>${participants.length}</dd>

                <dt>Chunks</dt>
                <dd>${chunks.length}</dd>

                <dt>Transcript Status</dt>
                <dd>${renderStatusPill(session.transcript_status)}</dd>

                <dt>Log Status</dt>
                <dd>${renderStatusPill(session.log_status)}</dd>

                <dt>Alert State</dt>
                <dd>${renderStatusPill(session.alert_state)}</dd>
            </dl>

            <div class="chunk-list">
                <h4>Chunk Manifest</h4>
                ${chunks.length === 0 ? '<div class="empty-state" style="padding: 12px 0;">No chunks uploaded yet.</div>' : ''}
                ${chunks
                    .map(
                        (chunk) => `
                        <div class="chunk-item">
                            <div><strong>Sequence #${chunk.sequence_no}</strong></div>
                            <div class="chunk-meta">Duration: ${(chunk.duration_ms / 1000).toFixed(1)}s</div>
                            <div class="chunk-meta">Stored At: ${formatDate(chunk.stored_at) || '—'}</div>
                            <div class="chunk-meta">Checksum: ${escapeHtml(chunk.checksum)}</div>
                            <div class="chunk-meta">Storage Key: ${escapeHtml(chunk.storage_key)}</div>
                            <div class="chunk-meta">Transcript: ${renderStatusPill(chunk.transcript_status)}</div>
                            <div class="chunk-meta">Logs: ${renderStatusPill(chunk.log_status)}</div>
                            ${chunk.download_url ? `<button class="chunk-download" data-seq="${chunk.sequence_no}">Download Chunk</button>` : '<span class="chunk-meta">Download URL unavailable</span>'}
                        </div>
                    `
                    )
                    .join('')}
            </div>
        </div>
    `;

    sessionDetail.querySelectorAll('.chunk-download').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const sequence = Number(btn.dataset.seq);
            downloadChunk(sequence);
        });
    });
}

async function downloadChunk(sequenceNo) {
    if (!activeSessionId) {
        showError('No session selected.');
        return;
    }

    try {
        const response = await fetch(`/api/sessions/${activeSessionId}/chunks/${sequenceNo}/download`, {
            headers: {
                ...authHeaders(),
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to generate download link (${response.status})`);
        }

        const payload = await response.json();
        if (payload.url) {
            window.open(payload.url, '_blank', 'noopener');
        } else {
            showError('Download URL unavailable.');
        }
    } catch (err) {
        console.error('Chunk download error', err);
        showError(err.message || 'Failed to generate download link.');
    }
}

function formatDate(value) {
    if (!value) return '';
    try {
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return date.toLocaleString();
    } catch {
        return value;
    }
}
