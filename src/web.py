from datetime import datetime, timedelta

from flask import Flask, render_template_string

from history_store import history_store
from state import state

app = Flask(__name__)

BASE_STYLE = """
  @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');
  :root {
    --bg: #07080b;
    --bg2: #0f1117;
    --card: rgba(255,255,255,0.035);
    --card-border: rgba(255,255,255,0.08);
    --text: #f1f3f8;
    --muted: #888fa3;
    --ok: #3ddc97;
    --err: #ff6b6b;
    --warn: #ffc24b;
    --gold: #f6b73c;
    --amber: #ff8a2b;
    --foam: #fff6e3;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: 'Inter', -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
    background:
      radial-gradient(900px 500px at 15% -10%, rgba(246,183,60,0.10), transparent 60%),
      radial-gradient(700px 500px at 100% 0%, rgba(255,138,43,0.08), transparent 55%),
      var(--bg);
    color: var(--text);
    padding: 40px clamp(16px, 4vw, 48px);
    min-height: 100vh;
  }
  a { color: var(--gold); text-decoration: none; }
  a:hover { text-decoration: underline; }
  h1, .display-font { font-family: 'Space Grotesk', 'Inter', sans-serif; }
  .top-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 28px;
    flex-wrap: wrap;
    gap: 12px;
  }
  h1 {
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 4px;
    display: flex;
    align-items: center;
    gap: 10px;
    letter-spacing: -0.01em;
  }
  .subtitle { color: var(--muted); margin: 0; font-size: 13px; }
  .nav-link {
    font-size: 13px;
    font-weight: 500;
    border: 1px solid var(--card-border);
    padding: 9px 16px;
    border-radius: 999px;
    background: var(--card);
    backdrop-filter: blur(6px);
    transition: border-color .15s ease;
  }
  .nav-link:hover { border-color: var(--gold); text-decoration: none; }
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 5px 13px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid transparent;
  }
  .badge.ok { background: rgba(61,220,151,.12); color: var(--ok); border-color: rgba(61,220,151,.25); }
  .badge.err { background: rgba(255,107,107,.12); color: var(--err); border-color: rgba(255,107,107,.25); }
  .badge.warn { background: rgba(255,194,75,.12); color: var(--warn); border-color: rgba(255,194,75,.25); }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }

  @media (max-width: 640px) {
    body { padding: 20px 16px; }
    .top-row { align-items: flex-start; }
    h1 { font-size: 22px; }
    .nav-link { font-size: 12px; padding: 8px 12px; }
  }
"""

LANDING_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="10">
<title>PerfectDraft: Live Status</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<style>
""" + BASE_STYLE + """
  .hero {
    position: relative;
    background:
      radial-gradient(500px 260px at 85% -20%, rgba(246,183,60,0.12), transparent 60%),
      linear-gradient(160deg, #14171f 0%, #0c0e14 100%);
    border: 1px solid var(--card-border);
    border-radius: 24px;
    padding: 36px;
    display: flex;
    align-items: center;
    gap: 44px;
    margin-bottom: 28px;
    flex-wrap: wrap;
    overflow: hidden;
  }

  /* Keg: self-drawn steel-cylinder silhouette with hoop bands and a coupler;
     the amber liquid rect is clipped to the same silhouette path, so the
     keg itself becomes the level gauge (no external SVG asset needed). */
  .glass-wrap { flex-shrink: 0; text-align: center; }
  .keg-svg { width: 110px; height: 170px; display: block; }
  .keg-liquid { transition: y .6s ease, height .6s ease; }
  .glass-label { margin-top: 10px; }
  .glass-label .big { font-size: 22px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
  .glass-label .small { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }

  .hero-meta { flex: 1; min-width: 260px; }
  .hero-meta .eyebrow { color: var(--gold); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .08em; margin-bottom: 6px; }
  .hero-meta h2 { margin: 0 0 4px; font-size: 26px; font-weight: 700; }
  .hero-meta .device-type { color: var(--muted); font-size: 13px; margin-bottom: 18px; }

  .temp-readout { display: flex; align-items: baseline; gap: 10px; margin-bottom: 18px; }
  .temp-readout .temp-big {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 56px;
    font-weight: 700;
    line-height: 1;
    background: linear-gradient(180deg, var(--foam), var(--gold));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
  }
  .temp-readout .temp-target { color: var(--muted); font-size: 14px; }

  .badge-row { display: flex; gap: 10px; flex-wrap: wrap; }

  .section-title {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: var(--muted);
    margin: 30px 0 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-title::after {
    content: "";
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--card-border), transparent);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
  }
  .trend-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 14px;
  }
  .card {
    position: relative;
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 16px;
    padding: 30px 20px 18px;
    text-align: center;
    backdrop-filter: blur(6px);
    transition: border-color .15s ease, transform .15s ease;
  }
  .card:hover { border-color: rgba(246,183,60,0.35); transform: translateY(-1px); }
  .card-link {
    display: block;
    text-decoration: none;
    color: inherit;
  }
  .card-link:hover { text-decoration: none; }
  .card .icon {
    position: absolute;
    top: 12px;
    left: 12px;
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: rgba(246,183,60,0.1);
    color: var(--gold);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    margin-bottom: 0;
  }

  /* Fill-mug icon: two stacked copies of the same glyph: a faint outline
     underneath, and a gold copy on top clipped from the bottom up by
     --fill, so the mug's own silhouette becomes the level gauge. */
  .icon.mug-icon { font-size: 13px; }
  .icon.mug-icon .mug-bg { color: rgba(255,255,255,0.18); }
  .icon.mug-icon .mug-fg {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--gold);
    filter: drop-shadow(0 0 4px rgba(246,183,60,0.55));
    clip-path: inset(calc(100% - var(--fill, 50%)) 0 0 0);
    transition: clip-path .6s ease;
  }
  .card .label {
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .05em;
    margin-bottom: 6px;
  }
  .card .value { font-size: 30px; font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
  .card .sub { color: var(--muted); font-size: 12px; margin-top: 4px; }

  .trend-card {
    text-align: left;
    padding: 20px 20px 16px;
    overflow: hidden;
  }
  .trend-card::after {
    content: "";
    position: absolute;
    inset: auto -10% -40% 35%;
    height: 120px;
    background: radial-gradient(circle, rgba(246,183,60,0.16), transparent 65%);
    pointer-events: none;
  }
  .trend-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 12px;
    margin-bottom: 10px;
  }
  .trend-title {
    color: var(--muted);
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: 6px;
  }
  .trend-now {
    font-size: 28px;
    font-weight: 700;
    font-family: 'Space Grotesk', sans-serif;
  }
  .trend-meta {
    color: var(--muted);
    font-size: 12px;
    text-align: right;
  }
  .sparkline {
    width: 100%;
    height: 92px;
    display: block;
    margin-top: 8px;
  }
  .sparkline-bg { opacity: .28; }
  .sparkline-line {
    fill: none;
    stroke: var(--gold);
    stroke-width: 3;
    stroke-linecap: round;
    stroke-linejoin: round;
    filter: drop-shadow(0 0 8px rgba(246,183,60,.28));
  }
  .sparkline-line.cool {
    stroke: #7ae3ff;
    filter: drop-shadow(0 0 8px rgba(122,227,255,.2));
  }
  .sparkline-grid {
    stroke: rgba(255,255,255,0.07);
    stroke-width: 1;
  }
  .trend-foot {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: var(--muted);
    font-size: 12px;
    margin-top: 10px;
  }

  .bar-track {
    width: 100%;
    height: 8px;
    background: rgba(255,255,255,0.07);
    border-radius: 999px;
    overflow: hidden;
    margin-top: 10px;
  }
  .bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--gold), var(--amber));
    border-radius: 999px;
    transition: width .6s ease;
  }
  .empty {
    color: var(--muted);
    padding: 70px 20px;
    text-align: center;
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 20px;
  }
  .footer-note { color: var(--muted); font-size: 12px; margin-top: 30px; }

  @media (max-width: 640px) {
    .hero { padding: 24px 20px; gap: 24px; flex-direction: column; align-items: stretch; text-align: center; }
    .glass-wrap { align-self: center; }
    .keg-svg { width: 80px; height: 124px; }
    .hero-meta h2 { font-size: 20px; word-break: break-all; }
    .temp-readout { flex-direction: column; align-items: center; gap: 2px; margin-bottom: 14px; }
    .temp-readout .temp-big { font-size: 44px; }
    .badge-row { justify-content: center; }
    .grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .card { padding: 26px 14px 14px; }
    .card .value { font-size: 22px; }
  }
  @media (max-width: 400px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
  <div class="top-row">
    <div>
      <h1>🍺 PerfectDraft Live Status</h1>
      <p class="subtitle">Auto-refreshes every 10s · machine {{ snap.machine_id or "—" }}</p>
    </div>
    <a class="nav-link" href="/logs">View connection &amp; API log →</a>
  </div>

  {% if not info %}
    <div class="empty">No machine data yet: waiting for the first successful poll.</div>
  {% else %}
  <div class="hero">
    {% set pct = info.keg_volume_pct %}
    <div class="glass-wrap">
      <svg class="keg-svg" viewBox="0 0 110 170" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="kegSteel" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stop-color="#4b5160"/>
            <stop offset="0.5" stop-color="#8a91a3"/>
            <stop offset="1" stop-color="#333844"/>
          </linearGradient>
          <linearGradient id="kegLiquid" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0" stop-color="#ff8a2b"/>
            <stop offset="1" stop-color="#ffcf6e"/>
          </linearGradient>
          <clipPath id="kegClip">
            <path d="M18,8 L92,8 Q100,8 100,16 L100,154 Q100,162 92,162 L18,162 Q10,162 10,154 L10,16 Q10,8 18,8 Z"/>
          </clipPath>
        </defs>
        <path d="M18,8 L92,8 Q100,8 100,16 L100,154 Q100,162 92,162 L18,162 Q10,162 10,154 L10,16 Q10,8 18,8 Z"
              fill="url(#kegSteel)" stroke="rgba(255,255,255,0.25)" stroke-width="2"/>
        <rect class="keg-liquid" x="10" y="{{ 162 - (154 * pct / 100) }}" width="90" height="{{ 154 * pct / 100 }}"
              fill="url(#kegLiquid)" clip-path="url(#kegClip)" opacity="0.9"/>
        <rect x="8" y="38" width="94" height="7" rx="2" fill="rgba(0,0,0,0.35)"/>
        <rect x="8" y="124" width="94" height="7" rx="2" fill="rgba(0,0,0,0.35)"/>
        <rect x="46" y="0" width="18" height="10" rx="3" fill="#5a6072" stroke="rgba(255,255,255,0.25)" stroke-width="1.5"/>
      </svg>
      <div class="glass-label">
        <div class="big">{{ info.keg_volume }} L</div>
        <div class="small">{{ info.keg_type }} keg · {{ pct }}% full</div>
      </div>
    </div>
    <div class="hero-meta">
      <div class="eyebrow">PerfectDraft {{ info.machine_type }}</div>
      <h2>{{ info.serial_number }}</h2>
      <div class="device-type">Firmware {{ info.firmware_version }}</div>
      <div class="temp-readout">
        <span class="temp-big">{{ info.temperature }}°{{ info.temp_unit }}</span>
        <span class="temp-target">target {{ info.target_temperature }}°{{ info.temp_unit }} &middot; range {{ info.temp_min }}–{{ info.temp_max }}°{{ info.temp_unit }}</span>
      </div>
      <div class="badge-row">
        {% if info.connected %}
          <span class="badge ok"><span class="dot"></span>Online</span>
        {% else %}
          <span class="badge err"><span class="dot"></span>Offline</span>
        {% endif %}
        {% if info.door_closed %}
          <span class="badge ok"><span class="dot"></span>Door Closed</span>
        {% else %}
          <span class="badge warn"><span class="dot"></span>Door Open</span>
        {% endif %}
        {% if info.error_codes %}
          <span class="badge err"><span class="dot"></span>Error {{ info.error_codes }}</span>
        {% else %}
          <span class="badge ok"><span class="dot"></span>No Errors</span>
        {% endif %}
      </div>
    </div>
  </div>

  <div class="section-title">Keg</div>
  <div class="grid">
    <div class="card">
      <div class="icon mug-icon" style="--fill: {{ info.keg_volume_pct }}%;">
        <i class="fa-solid fa-beer-mug-empty mug-bg"></i>
        <i class="fa-solid fa-beer-mug-empty mug-fg"></i>
      </div>
      <div class="label">Keg Volume Remaining</div>
      <div class="value">{{ info.keg_volume }} L</div>
      <div class="bar-track"><div class="bar-fill" style="width: {{ info.keg_volume_pct }}%"></div></div>
      <div class="sub">{{ info.keg_type }}</div>
    </div>
    <div class="card">
      <div class="icon">📟</div>
      <div class="label">Keg Pressure</div>
      <div class="value">{{ info.keg_pressure }}</div>
      <div class="sub">raw sensor reading</div>
    </div>
    <div class="card">
      <div class="icon">🍺</div>
      <div class="label">Last Pour</div>
      <div class="value">{{ info.volume_of_last_pour }} L</div>
      <div class="sub">{{ info.duration_of_last_pour }}s duration</div>
    </div>
    <div class="card">
      <div class="icon">🔢</div>
      <div class="label">Pours Since Startup</div>
      <div class="value">{{ info.pours_since_startup }}</div>
    </div>
  </div>

  <div class="section-title">30-Day Trends</div>
  <div class="trend-grid">
    <div class="card trend-card">
      <div class="trend-head">
        <div>
          <div class="trend-title">Temperature History</div>
          <div class="trend-now">{{ info.temperature }}°{{ info.temp_unit }}</div>
        </div>
        <div class="trend-meta">30 days<br>{{ history.temperature_points }} samples</div>
      </div>
      {% if history.temperature_path %}
      <svg class="sparkline" viewBox="0 0 320 92" preserveAspectRatio="none" aria-label="Temperature trend">
        <defs>
          <linearGradient id="tempSparkFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#7ae3ff" stop-opacity="0.45"></stop>
            <stop offset="1" stop-color="#7ae3ff" stop-opacity="0"></stop>
          </linearGradient>
        </defs>
        <line class="sparkline-grid" x1="0" y1="76" x2="320" y2="76"></line>
        <path class="sparkline-bg" d="{{ history.temperature_fill_path }}" fill="url(#tempSparkFill)"></path>
        <path class="sparkline-line cool" d="{{ history.temperature_path }}"></path>
      </svg>
      {% else %}
      <div class="sub">Not enough temperature history yet.</div>
      {% endif %}
      <div class="trend-foot">
        <span>Low {{ history.temperature_min_label }}</span>
        <span>High {{ history.temperature_max_label }}</span>
      </div>
    </div>
    <div class="card trend-card">
      <div class="trend-head">
        <div>
          <div class="trend-title">Keg Fullness History</div>
          <div class="trend-now">{{ info.keg_volume_pct }}%</div>
        </div>
        <div class="trend-meta">30 days<br>{{ history.usage_points }} samples</div>
      </div>
      {% if history.usage_path %}
      <svg class="sparkline" viewBox="0 0 320 92" preserveAspectRatio="none" aria-label="Keg fullness trend">
        <defs>
          <linearGradient id="usageSparkFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#f6b73c" stop-opacity="0.5"></stop>
            <stop offset="1" stop-color="#f6b73c" stop-opacity="0"></stop>
          </linearGradient>
        </defs>
        <line class="sparkline-grid" x1="0" y1="76" x2="320" y2="76"></line>
        <path class="sparkline-bg" d="{{ history.usage_fill_path }}" fill="url(#usageSparkFill)"></path>
        <path class="sparkline-line" d="{{ history.usage_path }}"></path>
      </svg>
      {% else %}
      <div class="sub">Not enough usage history yet.</div>
      {% endif %}
      <div class="trend-foot">
        <span>Low {{ history.usage_min_label }}</span>
        <span>High {{ history.usage_max_label }}</span>
      </div>
    </div>
  </div>

  <div class="section-title">Temperature &amp; Mode</div>
  <div class="grid">
    <div class="card">
      <div class="icon">🌡️</div>
      <div class="label">Target Temperature</div>
      <div class="value">{{ info.target_temperature }}°{{ info.temp_unit }}</div>
      <div class="sub">Range {{ info.temp_min }}–{{ info.temp_max }}°{{ info.temp_unit }}</div>
    </div>
    <div class="card">
      <div class="icon">⏱️</div>
      <div class="label">API Time To Target</div>
      <div class="value">{{ info.time_to_target }} min</div>
    </div>
    <div class="card">
      <div class="icon">🧊</div>
      <div class="label">Cooling Rate</div>
      <div class="value">{{ info.cooling_rate_label }}</div>
      <div class="sub">based on recent history</div>
    </div>
    <div class="card">
      <div class="icon">⌛</div>
      <div class="label">Calculated Time To Target</div>
      <div class="value">{{ info.calculated_time_to_target_label }}</div>
      <div class="sub">derived from cooling rate</div>
    </div>
    <div class="card">
      <div class="icon">🍃</div>
      <div class="label">Eco Mode</div>
      <div class="value">{{ "On" if info.eco_mode else "Off" }}</div>
      <div class="sub">Scheduler {{ "On" if info.eco_scheduler else "Off" }}</div>
    </div>
    <div class="card">
      <div class="icon">⚙️</div>
      <div class="label">Mode</div>
      <div class="value">{{ info.mode }}</div>
      <div class="sub">Boost {{ "On" if info.boost else "Off" }}</div>
    </div>
  </div>

  <div class="section-title">Support my drinking habit</div>
  <div class="grid">
    <a class="card-link" href="https://www.perfectdraft.com/en-gb/perfectdraft-gift-vouchers" target="_blank" rel="noopener noreferrer">
      <div class="card">
        <div class="icon">🎁</div>
        <div class="label">Buy Me A Keg Voucher</div>
        <div class="value">Gift Vouchers</div>
        <div class="sub">*Opens PerfectDraft in a new tab</div>
      </div>
    </a>
  </div>
  {% endif %}

  <p class="footer-note">Raw MQTT topic: {{ snap.machine_id and ("…/" + snap.machine_id|string + "/state") or "—" }}</p>
</body>
</html>
"""

LOGS_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="10">
<title>PerfectDraft MQTT: Connection Log</title>
<style>
""" + BASE_STYLE + """
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
    margin-bottom: 28px;
  }
  .card {
    background: var(--card);
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 16px 18px;
    backdrop-filter: blur(6px);
  }
  .card .label {
    color: var(--muted);
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-bottom: 8px;
  }
  .card .value { font-size: 16px; font-weight: 600; word-break: break-word; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--card-border); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: .04em; }
  td.status-2xx { color: var(--ok); font-weight: 600; }
  td.status-4xx, td.status-5xx { color: var(--err); font-weight: 600; }
  .url { color: var(--text); font-family: SFMono-Regular, Consolas, monospace; font-size: 12px; }
  pre {
    background: #0c0e12;
    border: 1px solid var(--card-border);
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
  .table-scroll { overflow-x: auto; }

  @media (max-width: 640px) {
    .grid { grid-template-columns: 1fr 1fr; gap: 10px; }
    .card { padding: 14px 16px; }
    table { min-width: 640px; }
  }
  @media (max-width: 400px) {
    .grid { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>
  <div class="top-row">
    <div>
      <h1>🔌 Connection &amp; API Log</h1>
      <p class="subtitle">Auto-refreshes every 10s</p>
    </div>
    <a class="nav-link" href="/">← Back to live status</a>
  </div>

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
    <div class="table-scroll">
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
    </div>
    {% else %}
      <div class="card empty">No API calls recorded yet.</div>
    {% endif %}
  </section>
</body>
</html>
"""


def _extract_display_info(machine_info):
    if not machine_info:
        return None
    details = machine_info.get("details") or {}
    setting = machine_info.get("setting") or {}
    settings_nested = details.get("settings") or {}

    temp_unit = setting.get("temperatureUnit") or settings_nested.get("temperatureUnit") or "C"
    temp_min = setting.get("temperatureMin", settings_nested.get("temperatureMin", "—"))
    temp_max = setting.get("temperatureMax", settings_nested.get("temperatureMax", "—"))
    target_temp = setting.get("temperature", settings_nested.get("temperature", "—"))
    current_temp = details.get("temperature")

    temp_pct = 50
    try:
        if current_temp is not None and isinstance(temp_min, (int, float)) and isinstance(temp_max, (int, float)) and temp_max > temp_min:
            temp_pct = max(0, min(100, round((current_temp - temp_min) / (temp_max - temp_min) * 100)))
    except (TypeError, ZeroDivisionError):
        pass

    keg_volume = details.get("kegVolume", 0) or 0
    keg_volume_pct = max(0, min(100, round((keg_volume / 6) * 100))) if isinstance(keg_volume, (int, float)) else 0

    keg_pressure = details.get("kegPressure")
    volume_of_last_pour = details.get("volumeOfLastPour", 0)

    def _round(value, digits=1):
        if not isinstance(value, (int, float)):
            return value
        rounded = round(value, digits)
        return int(rounded) if digits == 0 else rounded

    return {
        "machine_type": (machine_info.get("type") or "Machine").replace("_", " ").title(),
        "serial_number": details.get("serialNumber", "—"),
        "firmware_version": details.get("firmwareVersion", "—"),
        "connected": bool(details.get("connectedState")),
        "door_closed": bool(details.get("doorClosed")),
        "error_codes": details.get("errorCodes", 0),
        "temperature": _round(current_temp) if current_temp is not None else "—",
        "temp_unit": temp_unit,
        "temp_pct": temp_pct,
        "keg_volume": _round(keg_volume, 2),
        "keg_volume_pct": keg_volume_pct,
        "keg_type": details.get("kegType", "—"),
        "keg_pressure": _round(keg_pressure, 0) if keg_pressure is not None else "—",
        "duration_of_last_pour": details.get("durationOfLastPour", 0),
        "volume_of_last_pour": _round(volume_of_last_pour, 2),
        "pours_since_startup": details.get("numberOfPoursSinceStartup", 0),
        "target_temperature": _round(target_temp),
        "temp_min": _round(temp_min),
        "temp_max": _round(temp_max),
        "time_to_target": details.get("timeToReachTargetTemperature", 0),
        "eco_mode": settings_nested.get("ecoModeEnabled", False),
        "eco_scheduler": settings_nested.get("ecoModeSchedulerEnabled", False),
        "mode": setting.get("mode", "—"),
        "boost": setting.get("boost", False),
        "cooling_rate_label": "—",
        "calculated_time_to_target_label": "—",
    }


def _downsample(values, max_points=120):
    if len(values) <= max_points:
        return values

    step = (len(values) - 1) / (max_points - 1)
    sampled = []
    for index in range(max_points):
        sampled.append(values[round(index * step)])
    return sampled


def _build_sparkline(values, width=320, height=92, top_padding=8, bottom_padding=16):
    valid_values = [value for value in values if isinstance(value, (int, float))]
    if len(valid_values) < 2:
        return {
            "path": "",
            "fill_path": "",
            "min_label": "—",
            "max_label": "—",
            "points": len(valid_values),
        }

    sampled = _downsample(valid_values)
    minimum = min(sampled)
    maximum = max(sampled)
    drawable_height = height - top_padding - bottom_padding
    span = maximum - minimum
    if span == 0:
        span = 1

    points = []
    for index, value in enumerate(sampled):
        x = 0 if len(sampled) == 1 else (width * index / (len(sampled) - 1))
        y = top_padding + ((maximum - value) / span) * drawable_height
        points.append((round(x, 2), round(y, 2)))

    path = "M " + " L ".join(f"{x} {y}" for x, y in points)
    fill_path = (
        f"M {points[0][0]} {height - bottom_padding} L "
        + " L ".join(f"{x} {y}" for x, y in points)
        + f" L {points[-1][0]} {height - bottom_padding} Z"
    )

    return {
        "path": path,
        "fill_path": fill_path,
        "min_label": minimum,
        "max_label": maximum,
        "points": len(valid_values),
    }


def _format_value(value, suffix="", digits=1):
    if not isinstance(value, (int, float)):
        return "—"
    rounded = round(value, digits)
    if digits == 0:
        rounded = int(rounded)
    return f"{rounded}{suffix}"


def _format_duration(minutes):
    if not isinstance(minutes, (int, float)):
        return "—"
    if minutes <= 0:
        return "At target"

    rounded_minutes = round(minutes)
    if rounded_minutes < 60:
        return f"{rounded_minutes} min"

    hours, remainder = divmod(rounded_minutes, 60)
    if remainder == 0:
        return f"{hours}h"
    return f"{hours}h {remainder}m"


def _calculate_cooling_metrics(rows, current_temperature, target_temperature):
    valid_rows = []
    for row in rows:
        temperature = row.get("temperature")
        timestamp = row.get("timestamp")
        if not isinstance(temperature, (int, float)) or not timestamp:
            continue
        try:
            valid_rows.append((datetime.fromisoformat(timestamp), float(temperature)))
        except ValueError:
            continue

    if len(valid_rows) < 2:
        return None, None

    window_start = valid_rows[-1][0] - timedelta(hours=6)
    recent_rows = [row for row in valid_rows if row[0] >= window_start]
    if len(recent_rows) < 2:
      recent_rows = valid_rows[-2:]

    start_time, start_temp = recent_rows[0]
    end_time, end_temp = recent_rows[-1]
    elapsed_hours = (end_time - start_time).total_seconds() / 3600
    if elapsed_hours <= 0:
        return None, None

    cooling_rate = (start_temp - end_temp) / elapsed_hours
    if cooling_rate <= 0:
        return None, None

    if not isinstance(current_temperature, (int, float)) or not isinstance(target_temperature, (int, float)):
        return cooling_rate, None

    remaining_delta = current_temperature - target_temperature
    if remaining_delta <= 0:
        return cooling_rate, 0

    return cooling_rate, (remaining_delta / cooling_rate) * 60


def _build_history_view(machine_id, info):
    rows = history_store.get_recent_history(machine_id=machine_id, days=30)
    temperature_sparkline = _build_sparkline([row.get("temperature") for row in rows])
    usage_sparkline = _build_sparkline([row.get("keg_volume_pct") for row in rows])

    cooling_rate, calculated_time_to_target = _calculate_cooling_metrics(
        rows,
        info.get("temperature") if info else None,
        info.get("target_temperature") if info else None,
    )

    temp_unit = info.get("temp_unit", "C") if info else "C"
    history = {
        "temperature_path": temperature_sparkline["path"],
        "temperature_fill_path": temperature_sparkline["fill_path"],
      "temperature_min_label": _format_value(temperature_sparkline["min_label"], f"°{temp_unit}"),
      "temperature_max_label": _format_value(temperature_sparkline["max_label"], f"°{temp_unit}"),
        "temperature_points": temperature_sparkline["points"],
        "usage_path": usage_sparkline["path"],
        "usage_fill_path": usage_sparkline["fill_path"],
        "usage_min_label": _format_value(usage_sparkline["min_label"], "%", 0),
        "usage_max_label": _format_value(usage_sparkline["max_label"], "%", 0),
        "usage_points": usage_sparkline["points"],
    }

    if info:
        info["cooling_rate_label"] = _format_value(cooling_rate, "°C/h", 2)
        info["calculated_time_to_target_label"] = _format_duration(calculated_time_to_target)

    return history


@app.route("/")
def index():
    snap = state.snapshot()
    info = _extract_display_info(snap.get("machine_info"))
    history = _build_history_view(snap.get("machine_id"), info)
    temp_pct = info["temp_pct"] if info else 50
    return render_template_string(
        LANDING_TEMPLATE,
        snap=snap,
        info=info,
        history=history,
        temp_pct=temp_pct,
    )


@app.route("/logs")
def logs():
    return render_template_string(LOGS_TEMPLATE, snap=state.snapshot())


@app.route("/healthz")
def healthz():
    return {"ok": True}
