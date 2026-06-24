from flask import Flask, render_template_string

from state import state

app = Flask(__name__)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<title>PerfectDraft MQTT — Admin</title>
<style>
  :root {
    --bg: #0f1115;
    --card: #1a1d24;
    --border: #2b2f3a;
    --text: #e6e8ec;
    --muted: #8a8f9c;
    --ok: #34d399;
    --err: #f87171;
    --accent: #f5a524;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 32px;
  }
  h1 {
    font-size: 22px;
    margin: 0 0 4px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .subtitle { color: var(--muted); margin: 0 0 28px; font-size: 13px; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .card .label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-bottom: 8px;
  }
  .card .value { font-size: 16px; font-weight: 600; word-break: break-word; }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
  }
  .badge.ok { background: rgba(52,211,153,.15); color: var(--ok); }
  .badge.err { background: rgba(248,113,113,.15); color: var(--err); }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: .04em; }
  td.status-2xx { color: var(--ok); font-weight: 600; }
  td.status-4xx, td.status-5xx { color: var(--err); font-weight: 600; }
  .url { color: var(--text); font-family: SFMono-Regular, Consolas, monospace; font-size: 12px; }
  pre {
    background: #0c0e12;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px;
    margin: 6px 0 0;
    max-width: 480px;
    max-height: 140px;
    overflow: auto;
    font-size: 11px;
    color: var(--muted);
    white-space: pre-wrap;
    word-break: break-word;
  }
  .empty { color: var(--muted); padding: 20px; text-align: center; }
  section h2 { font-size: 15px; margin: 0 0 12px; color: var(--text); }
</style>
</head>
<body>
  <h1>🍺 PerfectDraft MQTT</h1>
  <p class="subtitle">Admin status page — auto-refreshes every 10s</p>

  <div class="grid">
    <div class="card">
      <div class="label">Authentication</div>
      <div class="value">
        {% if snap.authenticated %}
          <span class="badge ok"><span class="dot"></span>Authenticated</span>
        {% else %}
          <span class="badge err"><span class="dot"></span>Not authenticated</span>
        {% endif %}
      </div>
    </div>
    <div class="card">
      <div class="label">Last successful auth</div>
      <div class="value">{{ snap.last_auth_time or "—" }}</div>
    </div>
    <div class="card">
      <div class="label">Last auth error</div>
      <div class="value">{{ snap.last_auth_error or "—" }}</div>
    </div>
    <div class="card">
      <div class="label">Machine ID</div>
      <div class="value">{{ snap.machine_id or "not discovered yet" }}</div>
    </div>
    <div class="card">
      <div class="label">Last poll</div>
      <div class="value">{{ snap.last_poll_time or "—" }}</div>
    </div>
    <div class="card">
      <div class="label">Last poll error</div>
      <div class="value">{{ snap.last_poll_error or "—" }}</div>
    </div>
  </div>

  <section>
    <h2>Recent API calls</h2>
    {% if snap.calls %}
    <table>
      <thead>
        <tr><th>Time</th><th>Method</th><th>URL</th><th>Status</th><th>Response</th></tr>
      </thead>
      <tbody>
        {% for call in snap.calls %}
        <tr>
          <td>{{ call.timestamp }}</td>
          <td>{{ call.method }}</td>
          <td class="url">{{ call.url }}</td>
          <td class="{% if call.status_code >= 500 %}status-5xx{% elif call.status_code >= 400 %}status-4xx{% else %}status-2xx{% endif %}">
            {{ call.status_code }}
          </td>
          <td><pre>{{ call.response_body }}</pre></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
      <div class="card empty">No API calls recorded yet.</div>
    {% endif %}
  </section>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE_TEMPLATE, snap=state.snapshot())


@app.route("/healthz")
def healthz():
    return {"ok": True}
