import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
from database import Database
from engine import AuraEngine, AuraConfig, AuraExplainer

# ============================================================================
# DATA LOADING & CACHING
# ============================================================================

@st.cache_resource
def get_db() -> Database:
    return Database("aura.db")

@st.cache_resource
def get_engine() -> AuraEngine:
    cfg = AuraConfig(learning_days=7)
    return AuraEngine(cfg)

@st.cache_resource
def get_explainer() -> AuraExplainer:
    return AuraExplainer()

@st.cache_data(ttl=60)
def load_events(limit: int = 250) -> List[Dict[str, Any]]:
    db = get_db()
    db._bootstrap_demo_data_if_empty()
    return db.recent_events(limit=limit)

@st.cache_data(ttl=60)
def load_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    db = get_db()
    return db.recent_alerts(limit=limit)

def get_device_status() -> Dict[str, Dict[str, Any]]:
    db = get_db()
    devices = db.get_all_devices()
    result = {}
    for d in devices:
        result[d["node_label"]] = {"name": d["name"], "status": d["status"]}
    return result

# ============================================================================
# ALGORITHM VISUALIZATION FUNCTIONS
# ============================================================================

def build_algorithm_flow_diagram() -> go.Figure:
    """Phase 1 (Initial profile) + Phase 2 (Active monitoring) with pattern extraction, temporal analysis, and decision engine"""
    fig = go.Figure()
    
    # Phase 1: Learning components
    phase1_components = [
        (0.25, 0.85, 'Firewall\nObservation', '#0F87FF'),
        (0.10, 0.70, 'Pattern Extraction', '#00FFC2'),
        (0.25, 0.70, 'Temporal Analysis', '#00FFC2'),
        (0.40, 0.70, 'Decision Engine', '#00FFC2'),
        (0.25, 0.50, 'Saved Profile', '#FFD700'),
    ]
    
    for x, y, label, color in phase1_components:
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=16, color=color, symbol='square'),
            text=[label],
            textposition='middle center',
            textfont=dict(size=8, color='#E6F1FF'),
            hoverinfo='skip', showlegend=False
        ))
    
    # Phase 1 arrows
    arrows_phase1 = [
        ((0.25, 0.82), (0.25, 0.75)),
        ((0.25, 0.68), (0.15, 0.55)),
        ((0.25, 0.68), (0.25, 0.55)),
        ((0.25, 0.68), (0.35, 0.55)),
    ]
    
    for (x0, y0), (x1, y1) in arrows_phase1:
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0,
            xref='x', yref='y', axref='x', ayref='y',
            arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#0F87FF',
            showarrow=True
        )
    
    # Phase 2: Defense components
    phase2_components = [
        (0.60, 0.85, 'Live Requests\n(S1 → S2)', '#FF6B9D'),
        (0.75, 0.85, 'Load Profile', '#FFD700'),
        (0.60, 0.65, 'Traffic Inspection', '#FF6B9D'),
        (0.45, 0.45, 'Timing Check', '#00FFC2'),
        (0.60, 0.45, 'Outlier Detection', '#00FFC2'),
        (0.75, 0.45, 'Decision Engine', '#00FFC2'),
        (0.60, 0.25, 'Allow / Block / Flag', '#FFD700'),
    ]
    
    for x, y, label, color in phase2_components:
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=14, color=color, symbol='diamond'),
            text=[label],
            textposition='middle center',
            textfont=dict(size=7, color='#E6F1FF'),
            hoverinfo='skip', showlegend=False
        ))
    
    # Phase 2 arrows
    arrows_phase2 = [
        ((0.60, 0.82), (0.60, 0.70)),
        ((0.75, 0.82), (0.70, 0.70)),
        ((0.60, 0.62), (0.50, 0.50)),
        ((0.60, 0.62), (0.60, 0.50)),
        ((0.60, 0.62), (0.70, 0.50)),
        ((0.50, 0.42), (0.60, 0.30)),
        ((0.60, 0.42), (0.60, 0.30)),
        ((0.70, 0.42), (0.60, 0.30)),
    ]
    
    for (x0, y0), (x1, y1) in arrows_phase2:
        fig.add_annotation(
            x=x1, y=y1, ax=x0, ay=y0,
            xref='x', yref='y', axref='x', ayref='y',
            arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='#FF6B9D',
            showarrow=True
        )
    
    # Separator line
    fig.add_shape(
        type='line', x0=0.5, y0=0, x1=0.5, y1=1,
        xref='paper', yref='paper',
        line=dict(color='rgba(132,165,255,0.2)', width=2, dash='dash')
    )
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=20, r=20, t=60, b=20),
        height=700,
        hovermode=False,
    )
    
    return fig


def build_lstm_sequence_visual(events: List[Dict[str, Any]]) -> go.Figure:
    """Temporal pattern learning: 24-hour rhythm"""
    if not events:
        hours = list(range(24))
        values = [np.sin(h * 3.14159 / 12) * 50 + 50 + random.gauss(0, 5) for h in hours]
    else:
        hour_buckets = {h: [] for h in range(24)}
        for e in events:
            try:
                ts = datetime.fromisoformat(e['timestamp'])
                h = ts.hour
                total = (e.get('bytes_sent') or 0) + (e.get('bytes_recv') or 0)
                hour_buckets[h].append(total)
            except:
                pass
        
        hours = []
        values = []
        for h in range(24):
            if hour_buckets[h]:
                hours.append(h)
                values.append(np.mean(hour_buckets[h]))
        
        if not hours:
            hours = list(range(24))
            values = [0] * 24
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=values,
        mode='lines+markers',
        line=dict(color='#0F87FF', width=3),
        marker=dict(size=8, color='#00FFC2'),
        fill='tozeroy',
        fillcolor='rgba(15,135,255,0.2)',
        name='Learned Rhythm',
        hovertemplate='Hour %{x}: %{y:.0f} bytes<extra></extra>'
    ))
    
    fig.update_layout(
        title='<b>Temporal Pattern Learning</b><br><sub>Behavioral rhythm across 24 hours</sub>',
        xaxis_title='Hour of Day (UTC)',
        yaxis_title='Average Traffic (bytes)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E6F1FF'),
        margin=dict(l=50, r=20, t=60, b=40),
        height=320,
        hovermode='x unified',
    )
    
    return fig


def build_isolation_forest_scatter(events: List[Dict[str, Any]]) -> go.Figure:
    """Outlier detection: 2D scatter of timing vs volume"""
    normal_x, normal_y, anomaly_x, anomaly_y = [], [], [], []
    
    for e in events:
        try:
            ts = datetime.fromisoformat(e['timestamp'])
            hour = ts.hour
            total_bytes = (e.get('bytes_sent') or 0) + (e.get('bytes_recv') or 0)
            
            if e.get('is_anomaly'):
                anomaly_x.append(hour)
                anomaly_y.append(total_bytes)
            else:
                normal_x.append(hour)
                normal_y.append(total_bytes)
        except:
            pass
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=normal_x,
        y=normal_y,
        mode='markers',
        marker=dict(size=6, color='#00FFC2', opacity=0.6),
        name='Normal Baseline',
        hovertemplate='Hour: %{x}, Volume: %{y} bytes<extra></extra>'
    ))
    
    if anomaly_x:
        fig.add_trace(go.Scatter(
            x=anomaly_x,
            y=anomaly_y,
            mode='markers',
            marker=dict(size=10, color='#FF4949', symbol='x', line=dict(width=2)),
            name='Unusual Activity',
            hovertemplate='Hour: %{x}, Volume: %{y} bytes<extra></extra>'
        ))
    
    fig.update_layout(
        title='<b>Outlier Detection</b><br><sub>Timing vs Volume Analysis</sub>',
        xaxis_title='Hour of Day',
        yaxis_title='Traffic Volume (bytes)',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E6F1FF'),
        margin=dict(l=50, r=20, t=60, b=40),
        height=320,
        hovermode='closest',
    )
    
    return fig


def build_cnn_feature_heatmap(events: List[Dict[str, Any]]) -> go.Figure:
    """Feature extraction: protocol distribution"""
    protocols = {}
    for e in events:
        proto = e.get('protocol', 'TCP')
        protocols[proto] = protocols.get(proto, 0) + 1
    
    if not protocols:
        protocols = {'TCP': 50, 'UDP': 30, 'ICMP': 10}
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(protocols.keys()),
            y=list(protocols.values()),
            marker=dict(
                color=['#00FFC2', '#0F87FF', '#FFD700'][:len(protocols)],
                line=dict(color='#E6F1FF', width=2)
            ),
            text=list(protocols.values()),
            textposition='outside',
            hovertemplate='%{x}: %{y} packets<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='<b>Protocol Distribution</b><br><sub>Protocol pattern recognition</sub>',
        xaxis_title='Network Protocol',
        yaxis_title='Packet Count',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E6F1FF'),
        margin=dict(l=50, r=20, t=60, b=40),
        height=320,
        showlegend=False,
    )
    
    return fig


# ============================================================================
# VISUALIZATION HELPERS
# ============================================================================

def build_traffic_wave_figure(events: List[Dict[str, Any]]) -> go.Figure:
    if not events:
        x = [datetime.utcnow() - timedelta(minutes=i) for i in reversed(range(60))]
        y = [0 for _ in x]
    else:
        parsed = []
        for e in events:
            try:
                ts = datetime.fromisoformat(e["timestamp"])
            except Exception:
                continue
            total_bytes = (e.get("bytes_sent") or 0) + (e.get("bytes_recv") or 0)
            parsed.append((ts, total_bytes))
        parsed.sort(key=lambda t: t[0])
        x = [p[0] for p in parsed]
        y = [p[1] for p in parsed]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(
                color="#00FFC2",
                width=3,
                shape="spline",
                smoothing=1.3,
            ),
            fill="tozeroy",
            fillcolor="rgba(0, 255, 194, 0.18)",
            hovertemplate="<b>%{x}</b><br>Traffic: %{y} bytes<extra></extra>",
            name="Incoming Traffic",
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(
            showgrid=False,
            color="#8BA1C4",
            title="Time",
        ),
        yaxis=dict(
            showgrid=False,
            color="#8BA1C4",
            title="Bytes",
        ),
        font=dict(color="#E6F1FF"),
        hovermode="x unified",
    )

    return fig


def phase_from_profile() -> str:
    engine = get_engine()
    profile_path = engine._profile_file_for_user()
    return "Active Monitoring" if profile_path.exists() else "Profile Building"


def compute_phase_badge(phase: str) -> str:
    if phase == "Active Monitoring":
        return '<span class="phase-badge defense">DEFENSE ACTIVE</span>'
    return '<span class="phase-badge learning">PROFILE BUILDING</span>'


def calculate_security_score(events: List[Dict[str, Any]]) -> Tuple[int, str, str]:
    """Calculate security posture (0-100)"""
    if not events:
        return 85, "Profile Building", "#0F87FF"
    
    total = len(events)
    anomalies = len([e for e in events if e.get('is_anomaly')])
    anomaly_rate = anomalies / total if total > 0 else 0
    
    base_score = 95
    score = max(10, base_score - int(anomaly_rate * 100))
    
    if score >= 90:
        return score, "Excellent", "#00FFC2"
    elif score >= 75:
        return score, "Good", "#0F87FF"
    elif score >= 60:
        return score, "Fair", "#FFD700"
    elif score >= 45:
        return score, "At Risk", "#FF9B00"
    else:
        return score, "Critical", "#FF4949"


def build_threat_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create structured threat timeline"""
    timeline = []
    
    for e in events:
        if e.get('is_anomaly'):
            try:
                ts = datetime.fromisoformat(e['timestamp'])
                severity = 'HIGH' if e.get('anomaly_score', 0.5) > 0.7 else 'MEDIUM'
                timeline.append({
                    'timestamp': ts,
                    'time_str': ts.strftime('%d %b %H:%M UTC'),
                    'severity': severity,
                    'source_ip': e.get('source_ip', 'unknown'),
                    'node': 'S1' if '192.168' in (e.get('source_ip') or '') else 'S2',
                    'score': e.get('anomaly_score', 0.5),
                })
            except:
                pass
    
    timeline.sort(key=lambda x: x['timestamp'], reverse=True)
    return timeline[:20]


def format_anomaly_panels(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {
            "lstm_desc": "Awaiting profile building. Temporal analysis will characterise typical access rhythms over the next days.",
            "if_desc": "Outlier detection will learn typical traffic volumes and identify unusual combinations once sufficient data is available.",
            "last_anomaly": None,
        }

    anomalies = [e for e in events if e.get("is_anomaly")]
    anomalies.sort(key=lambda e: e["timestamp"], reverse=True)
    last_anomaly = anomalies[0] if anomalies else None

    lstm_desc = (
        "Temporal analysis models the rhythm of activity over time "
        "(logins, application use, network bursts). Deviations in timing or sequence "
        "may indicate a shift in behaviour."
    )
    if_desc = (
        "Outlier detection treats each session as a point in a multi-dimensional space. "
        "Unusual combinations of timing, protocol, and volume are highlighted for review."
    )

    return {
        "lstm_desc": lstm_desc,
        "if_desc": if_desc,
        "last_anomaly": last_anomaly,
    }


def get_latest_explanation(events: List[Dict[str, Any]]) -> Optional[str]:
    if not events:
        return None

    anomalies = [e for e in events if e.get("is_anomaly")]
    anomalies.sort(key=lambda e: e["timestamp"], reverse=True)
    if not anomalies:
        return None

    latest = anomalies[0]
    try:
        meta = json.loads(latest["raw_features_json"])
    except Exception:
        meta = {
            "timestamp": latest.get("timestamp"),
            "node": "S2",
            "src_ip": latest.get("source_ip"),
            "dst_ip": latest.get("dest_ip"),
            "protocol": latest.get("protocol", "TCP"),
            "bytes_sent": latest.get("bytes_sent", 0),
            "bytes_recv": latest.get("bytes_recv", 0),
        }

    explainer = get_explainer()
    explanation = explainer.explain_anomaly(
        anomaly_score=float(latest.get("anomaly_score") or 0.5),
        packet_meta=meta,
        baseline_summary="Normal profile learned from your past 7 days of behavior across S1 and S2 nodes.",
    )
    return explanation


# ============================================================================
# CSS & LAYOUT
# ============================================================================

def inject_css() -> None:
    st.markdown(
        """
        <style>
        /* Base layout */
        .stApp {
            background: radial-gradient(circle at top, #0b1020 0, #02040b 50%, #01020a 100%);
            color: #E6F1FF;
            font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        /* Sidebar glass */
        section[data-testid="stSidebar"] > div {
            background: linear-gradient(145deg, rgba(8,18,40,0.96), rgba(10,25,53,0.92));
            border-right: 1px solid rgba(0,255,194,0.2);
            box-shadow: 0 0 40px rgba(0,0,0,0.85);
        }

        .aura-logo {
            font-weight: 700;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-size: 0.85rem;
            color: #00FFC2;
        }

        .aura-subtitle {
            font-size: 0.80rem;
            color: #8BA1C4;
        }

        .neon-header {
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #E6F1FF;
            margin-bottom: 0.25rem;
        }

        .neon-glow {
            text-shadow: 0 0 8px rgba(0,255,194,0.55), 0 0 18px rgba(0,143,255,0.5);
        }

        .phase-badge {
            border-radius: 999px;
            padding: 0.15rem 0.75rem;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-weight: 600;
        }

        .phase-badge.learning {
            border: 1px solid rgba(0,143,255,0.7);
            color: #9ED4FF;
            background: linear-gradient(120deg, rgba(0,143,255,0.18), transparent);
        }

        .phase-badge.defense {
            border: 1px solid rgba(0,255,194,0.75);
            color: #00FFC2;
            background: linear-gradient(120deg, rgba(0,255,194,0.16), transparent);
        }

        .glass-card {
            border-radius: 18px;
            border: 1px solid rgba(132, 165, 255, 0.35);
            background: radial-gradient(circle at top left, rgba(0,255,194,0.12), transparent 40%),
                        linear-gradient(145deg, rgba(10,22,53,0.90), rgba(4,13,34,0.96));
            box-shadow: 0 0 28px rgba(0,0,0,0.85);
            padding: 1.1rem 1.2rem;
            margin-bottom: 1.1rem;
        }

        .glass-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.45rem;
        }

        .glass-card-title {
            font-size: 0.93rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #9FB6FF;
        }

        .metric-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.05rem 0.55rem;
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            border: 1px solid rgba(0,255,194,0.5);
            color: #00FFC2;
        }

        .chip-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-right: 0.4rem;
            background: radial-gradient(circle, #00FFC2 0, #008F7A 55%, transparent 100%);
            box-shadow: 0 0 10px rgba(0,255,194,0.8);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.12rem 0.6rem;
            margin-right: 0.35rem;
            margin-bottom: 0.25rem;
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .status-pill.online {
            border: 1px solid rgba(0,255,194,0.7);
            color: #00FFC2;
            background: radial-gradient(circle at left, rgba(0,255,194,0.32), transparent 70%);
        }

        .status-pill.offline {
            border: 1px solid rgba(255,92,92,0.7);
            color: #FF9B9B;
            background: radial-gradient(circle at left, rgba(255,92,92,0.30), transparent 70%);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            margin-right: 0.35rem;
            box-shadow: 0 0 10px rgba(0,255,194,0.8);
        }

        .status-dot.online {
            background: radial-gradient(circle, #00FFC2 0, #008F7A 55%, transparent 100%);
        }

        .status-dot.offline {
            background: radial-gradient(circle, #FF6B81 0, #70203C 55%, transparent 100%);
        }

        .xai-alert-text {
            font-size: 0.87rem;
            color: #E6F1FF;
        }

        .xai-label {
            font-size: 0.75rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #8BA1C4;
            margin-bottom: 0.25rem;
        }

        .timeline-item {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            padding: 0.45rem 0.5rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(18,36,80,0.82), rgba(4,10,26,0.9));
            margin-bottom: 0.25rem;
        }

        .timeline-left {
            max-width: 60%;
        }

        .timeline-title {
            font-size: 0.82rem;
            font-weight: 500;
            color: #E6F1FF;
        }

        .timeline-meta {
            font-size: 0.70rem;
            color: #8BA1C4;
        }

        .timeline-badge {
            font-size: 0.70rem;
            padding: 0.12rem 0.55rem;
            border-radius: 999px;
            border: 1px solid rgba(132,165,255,0.5);
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: #9FB6FF;
        }

        .mobile-frame {
            border-radius: 24px;
            border: 1px solid rgba(0,255,194,0.45);
            background: radial-gradient(circle at top, rgba(0,255,194,0.12), transparent 65%),
                        linear-gradient(160deg, rgba(7,14,35,1), rgba(1,4,14,1));
            box-shadow: 0 0 28px rgba(0,0,0,0.9), 0 0 24px rgba(0,255,194,0.4);
            padding: 0.75rem 0.6rem;
        }

        .mobile-status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.7rem;
            color: #9FB6FF;
            margin-bottom: 0.4rem;
        }

        .mobile-pill {
            font-size: 0.70rem;
            border-radius: 999px;
            padding: 0.12rem 0.6rem;
            border: 1px solid rgba(0,255,194,0.6);
            color: #00FFC2;
            text-transform: uppercase;
            letter-spacing: 0.14em;
        }

        .mobile-notification {
            padding: 0.38rem 0.45rem;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(18,36,80,0.96), rgba(5,16,40,0.98));
            margin-bottom: 0.35rem;
            border: 1px solid rgba(132,165,255,0.3);
        }

        .mobile-notification-title {
            font-size: 0.75rem;
            color: #E6F1FF;
            margin-bottom: 0.12rem;
        }

        .mobile-notification-body {
            font-size: 0.70rem;
            color: #9FB6FF;
        }

        .mobile-notification-meta {
            font-size: 0.65rem;
            color: #7087A9;
            margin-top: 0.12rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.6rem;
        }

        .metric-cell {
            border-radius: 14px;
            padding: 0.5rem 0.6rem;
            background: linear-gradient(150deg, rgba(14,31,70,0.85), rgba(6,17,44,0.97));
            border: 1px solid rgba(132,165,255,0.35);
        }

        .metric-label {
            font-size: 0.70rem;
            color: #8BA1C4;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            margin-bottom: 0.1rem;
        }

        .metric-value {
            font-size: 0.96rem;
            font-weight: 600;
            color: #E6F1FF;
        }

        .metric-sub {
            font-size: 0.68rem;
            color: #7FA5D9;
        }

        .threat-widget {
            border-radius: 14px;
            padding: 0.6rem;
            background: linear-gradient(135deg, rgba(255,73,73,0.15), rgba(255,155,155,0.08));
            border: 1px solid rgba(255,73,73,0.4);
            margin-bottom: 0.5rem;
        }

        .threat-level-high {
            color: #FF4949;
            font-weight: 700;
        }

        .threat-level-medium {
            color: #FFD700;
            font-weight: 700;
        }

        .control-button {
            display: inline-block;
            padding: 0.6rem 1.2rem;
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
            border-radius: 8px;
            border: 1px solid rgba(0,255,194,0.5);
            background: linear-gradient(135deg, rgba(0,255,194,0.15), transparent);
            color: #00FFC2;
            font-size: 0.80rem;
            font-weight: 600;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            transition: all 0.3s ease;
        }

        .control-button:hover {
            border-color: rgba(0,255,194,0.8);
            box-shadow: 0 0 12px rgba(0,255,194,0.4);
        }

        .firewall-rule {
            padding: 0.5rem 0.6rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(15,135,255,0.15), rgba(0,255,194,0.08));
            border: 1px solid rgba(132,165,255,0.3);
            margin-bottom: 0.4rem;
            font-size: 0.75rem;
        }

        .network-topology {
            padding: 1rem;
            border-radius: 14px;
            background: linear-gradient(135deg, rgba(7,14,35,0.9), rgba(10,25,53,0.95));
            border: 1px solid rgba(0,255,194,0.25);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# MAIN UI & ROUTING
# ============================================================================

def main() -> None:
    st.set_page_config(
        page_title="AURA: Behavioral Guard",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    get_db()
    engine = get_engine()

    # Sidebar navigation
    with st.sidebar:
        st.markdown('<div class="aura-logo">AURA // BEHAVIORAL GUARD</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="aura-subtitle">Behavioral threat detection across S1 (Local) and S2 (Remote) nodes.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        phase = phase_from_profile()
        st.markdown(compute_phase_badge(phase), unsafe_allow_html=True)

        st.write("")
        st.caption("DASHBOARD NAVIGATION")
        nav_option = st.radio(
            "Select View",
            options=[
                "Unified Control Center",
                "Algorithm Visualization",
                "Real-Time Monitoring",
                "Mobile Companion",
                "Firewall Controls",
            ],
            index=0,
            label_visibility="collapsed",
        )

        st.write("")
        st.caption("ENGINE STATUS")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Processing Iterations", "5", "+5")
        with col_b:
            st.metric("IF Trees", str(engine.config.isolation_forest_estimators), "Stable")

        st.write("")
        st.caption("SECURITY POSTURE")
        events = load_events(limit=250)
        score, assessment, color = calculate_security_score(events)
        st.markdown(
            f'<div style="font-size:2.2rem;color:{color};font-weight:700;text-align:center;">{score}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="text-align:center;color:#8BA1C4;font-size:0.85rem;">{assessment}</div>',
            unsafe_allow_html=True,
        )

        st.write("")
        st.caption("⚙️ OPERATIONS")
        if st.button("Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Load data
    events = load_events(limit=250)
    anomaly_meta = format_anomaly_panels(events)
    explanation = get_latest_explanation(events)
    alerts = load_alerts(limit=50)

    # Route to selected view
    if nav_option == "Unified Control Center":
        st.markdown(
            """
            <div style="display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:1rem;">
                <div>
                    <div class="neon-header neon-glow">Control Center</div>
                    <div style="font-size:0.80rem;color:#8BA1C4;">
                        System status and recent activity.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        left, middle, right = st.columns([2.4, 1.6, 1.4])

        with left:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-header">
                        <div class="glass-card-title">Live Traffic</div>
                        <div class="metric-chip">
                            <span class="chip-dot"></span>
                            Active
                        </div>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            fig = build_traffic_wave_figure(events)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with middle:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-header">
                        <div class="glass-card-title">Explanation</div>
                    </div>
                    <div class="xai-label">Interpretation Layer</div>
                """,
                unsafe_allow_html=True,
            )

            if explanation:
                st.markdown(
                    f'<div class="xai-alert-text">{explanation}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    """<div class="xai-alert-text">
Waiting for activity to analyze.
                    </div>""",
                    unsafe_allow_html=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="glass-card-title">Node Status</div>
                """,
                unsafe_allow_html=True,
            )
            nodes = get_device_status()
            for label in ["S1", "S2"]:
                node = nodes.get(label, {"name": f"Node {label}", "status": "offline"})
                status = (node.get("status") or "offline").lower()
                pill_cls = "online" if status == "online" else "offline"
                st.markdown(
                    f"""
                    <div class="status-pill {pill_cls}">
                        <span class="status-dot {pill_cls}"></span>
                        {label} · {node.get("name","Unknown")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-header">
                        <div class="glass-card-title">Mobile Sync</div>
                    </div>
                    <div class="mobile-frame">
                        <div class="mobile-status-bar">
                            <span>Connected</span>
                            <span>92% Signal</span>
                        </div>
                """,
                unsafe_allow_html=True,
            )
            score, assessment, color = calculate_security_score(events)
            st.markdown(
                f'<div class="mobile-pill" style="background:linear-gradient(135deg, rgba(0,255,194,0.2), transparent);margin-bottom:0.5rem;">Score: {score}</div>',
                unsafe_allow_html=True,
            )

            if not alerts:
                st.markdown(
                    """
                    <div class="mobile-notification">
                        <div class="mobile-notification-title">All Clear</div>
                        <div class="mobile-notification-body">No threats detected.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                for a in alerts[:2]:
                    st.markdown(
                        f"""
                        <div class="mobile-notification">
                            <div class="mobile-notification-title">{a.get('title', 'Alert')}</div>
                            <div class="mobile-notification-body">{a.get('explained_message', a.get('message', ''))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("---")

        col_metrics, col_timeline = st.columns([1.6, 2.4])

        with col_metrics:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Metrics Overview</div>
                """,
                unsafe_allow_html=True,
            )
            total_events = len(events)
            anomalies = [e for e in events if e.get("is_anomaly")]
            anomaly_count = len(anomalies)
            anomaly_rate = f"{(anomaly_count / total_events * 100):.1f}%" if total_events else "0.0%"

            st.metric("Total Events", total_events)
            st.metric("Unusual Activity", anomaly_count)
            st.metric("Unusual Activity Rate", anomaly_rate)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_timeline:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Recent Activity</div>
                """,
                unsafe_allow_html=True,
            )
            parsed_events = []
            for e in events:
                try:
                    ts = datetime.fromisoformat(e["timestamp"])
                    parsed_events.append((ts, e))
                except Exception:
                    continue

            parsed_events.sort(key=lambda t: t[0], reverse=True)

            for ts, e in parsed_events[:10]:
                node = "S1" if "192.168" in (e.get("source_ip") or "") else "S2"
                protocol = e.get("protocol", "TCP")
                total_bytes = (e.get("bytes_sent") or 0) + (e.get("bytes_recv") or 0)
                is_anomaly = bool(e.get("is_anomaly"))
                title = "Unusual" if is_anomaly else "Normal"
                meta = f"{protocol} · {total_bytes} bytes · {node}"

                st.markdown(
                    f"""
                    <div class="timeline-item">
                        <div class="timeline-left">
                            <div class="timeline-title">{title}</div>
                            <div class="timeline-meta">{meta}</div>
                        </div>
                        <div style="font-size:0.68rem;color:#7087A9;">
                            {ts.strftime('%H:%M UTC')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    elif nav_option == "Algorithm Visualization":
        st.markdown(
            """
            <div class="neon-header neon-glow">System Architecture</div>
            <div style="font-size:0.80rem;color:#8BA1C4;margin-bottom:1.5rem;">
            Core components and workflows.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='glass-card-title' style='margin-bottom:1rem;'>System Flow</div>",
            unsafe_allow_html=True,
        )

        fig_flow = build_algorithm_flow_diagram()
        st.plotly_chart(fig_flow, use_container_width=True, config={"displayModeBar": False})

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Pattern Detection</div>
                    <p style="font-size:0.75rem;color:#8BA1C4;margin-top:0.5rem;">
                    Identifies network patterns and anomalies.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Temporal Models</div>
                    <p style="font-size:0.75rem;color:#8BA1C4;margin-top:0.5rem;">
                    Learns timing patterns and detects deviations.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Decision Engine</div>
                    <p style="font-size:0.75rem;color:#8BA1C4;margin-top:0.5rem;">
                    Combines signals for final recommendations.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            fig_lstm = build_lstm_sequence_visual(events)
            st.plotly_chart(fig_lstm, use_container_width=True, config={"displayModeBar": False})

            fig_cnn = build_cnn_feature_heatmap(events)
            st.plotly_chart(fig_cnn, use_container_width=True, config={"displayModeBar": False})

        with viz_col2:
            fig_if = build_isolation_forest_scatter(events)
            st.plotly_chart(fig_if, use_container_width=True, config={"displayModeBar": False})

    elif nav_option == "Real-Time Monitoring":
        st.markdown(
            """
            <div class="neon-header neon-glow">Network Monitoring</div>
            <div style="font-size:0.80rem;color:#8BA1C4;margin-bottom:1.5rem;">
            Live system telemetry.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='glass-card-title' style='margin-bottom:1rem;'>Live Traffic Stream</div>",
            unsafe_allow_html=True,
        )
        fig = build_traffic_wave_figure(events)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown("---")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("📡 Total Events", len(events))
        with metric_col2:
            anomaly_count = len([e for e in events if e.get('is_anomaly')])
            st.metric("⚠️ Anomalies", anomaly_count)
        with metric_col3:
            last_24 = [e for e in events if datetime.fromisoformat(e['timestamp']) >= (datetime.utcnow() - timedelta(hours=24))]
            st.metric("📋 Events (24h)", len(last_24))
        with metric_col4:
            nodes = get_device_status()
            online_count = sum(1 for n in nodes.values() if n.get('status') == 'online')
            st.metric("🔗 Nodes", f"{online_count}/{len(nodes)}")

    elif nav_option == "Mobile Companion":
        st.markdown(
            """
            <div class="neon-header neon-glow">Mobile View</div>
            <div style="font-size:0.80rem;color:#8BA1C4;margin-bottom:1.5rem;">
            Quick status and alerts.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_m1, col_m2, col_m3 = st.columns([1, 1.2, 1])

        with col_m2:
            score, assessment, color = calculate_security_score(events)
            st.markdown(
                f"""
                <div class="mobile-frame">
                    <div class="mobile-status-bar">
                        <span>🔐 AURA Guard</span>
                        <span style="color:{color};">●</span>
                    </div>
                    <div style="margin-bottom:0.75rem;text-align:center;">
                        <div style="font-size:1.8rem;color:{color};font-weight:700;">{score}</div>
                        <div style="font-size:0.75rem;color:#8BA1C4;">{assessment} Protection</div>
                    </div>
                    <div style="font-size:0.70rem;color:#8BA1C4;margin-bottom:0.5rem;">Recent Alerts</div>
                """,
                unsafe_allow_html=True,
            )

            if not alerts:
                st.markdown(
                    """
                    <div class="mobile-notification">
                        <div class="mobile-notification-title">✓ All Clear</div>
                        <div class="mobile-notification-body">No threats detected.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                for a in alerts[:3]:
                    st.markdown(
                        f"""
                        <div class="mobile-notification">
                            <div class="mobile-notification-title">{a.get('title', 'Alert')}</div>
                            <div class="mobile-notification-body">{a.get('explained_message', '')[:80]}...</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)

    elif nav_option == "Firewall Controls":
        st.markdown(
            """
            <div class="neon-header neon-glow">Controls</div>
            <div style="font-size:0.80rem;color:#8BA1C4;margin-bottom:1.5rem;">
            Response rules and sensitivity.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_resp1, col_resp2 = st.columns(2)

        with col_resp1:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Response Triggers</div>
                    <label><input type="checkbox" checked /> <b>Soft Guard</b> - Log-only mode</label><br/>
                    <label><input type="checkbox" checked /> <b>Adaptive Block</b> - Rule injection</label><br/>
                    <label><input type="checkbox" checked /> <b>Credential Shield</b> - After-hours check</label><br/>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_resp2:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="glass-card-title">Sensitivity Tuning</div>
                """,
                unsafe_allow_html=True,
            )
            lstm_sens = st.slider("Temporal Sensitivity", 0.0, 1.0, 0.5, step=0.1, label_visibility="collapsed")
            if_sens = st.slider("Outlier Sensitivity", 0.0, 1.0, 0.5, step=0.1, label_visibility="collapsed")
            st.success(f"Policy updated: Temporal={lstm_sens:.1f}, Outlier={if_sens:.1f}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        st.markdown(
            """
            <div class="glass-card">
                <div class="glass-card-title">High-Threat IPs</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for ip, severity, reason in [
            ('203.0.113.55', 'HIGH', 'Port scanning'),
            ('198.51.100.42', 'MEDIUM', 'Repeated attempts'),
        ]:
            severity_color = '#FF4949' if severity == 'HIGH' else '#FFD700'
            st.markdown(
                f"<div class='firewall-rule' style='color:{severity_color};'>{ip} · {reason}</div>",
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
