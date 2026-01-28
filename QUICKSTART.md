# AURA Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
cd c:\Users\HP\Downloads\prototype\prototype
pip install -r requirements.txt
```

### 2. Run Dashboard
```bash
streamlit run app.py
```

Your browser opens to: `http://localhost:8501`

### 3. Explore Views
- **Unified Control Center**: Main dashboard with real-time stats
- **Algorithm Visualization**: See AURA's two-phase learning/defense logic
- **Real-Time Monitoring**: Live network traffic analysis
- **Threat Analytics**: Security trends and threat timeline
- **Mobile Companion**: On-the-go alerts interface
- **Firewall Controls**: Threat response management

---

## 📊 First-Run Experience

1. **Landing Page** shows "Learning Phase" badge
   - AURA is analyzing synthetic baseline data (7 days)
   - Training progress indicator in sidebar
   
2. **Algorithm Visualization** explains how AURA works:
   - **Phase 1** (Days 0-7): Learning your normal behavior
     - CNN extracts packet patterns
     - LSTM learns temporal rhythms (24-hour cycles)
     - Random Forest creates decision boundaries
   - **Phase 2** (Day 7+): Real-time threat detection
     - Live requests compared to learned baseline
     - Instant allow/block/flag decisions

3. **Threat Detection** examples:
   - Unusual 2 AM login from S2 (timing anomaly)
   - 10MB data transfer (volume spike)
   - Unknown protocol combination (pattern anomaly)

4. **Explainable AI** translates to human language:
   - "Unusual 2 AM login from remote device (S2) deviates from your learned S1 baseline."
   - "Network volume 5x higher than normal for TCP connections."
   - "Protocol combination never seen before - possible data exfiltration."

---

## 🎯 Key Features to Try

### Real-Time Traffic Monitoring
1. Go to **Real-Time Monitoring**
2. See live traffic wave (cyan graph)
3. Hover to see exact bytes/time
4. Node status shows S1 (Local) and S2 (Remote) connectivity

### Threat Analytics
1. Click **Threat Analytics**
2. View timeline of detected anomalies
3. See threat severity (HIGH/MEDIUM)
4. Check which IPs caused most incidents
5. Analyze protocol-wise distribution

### Algorithm Deep-Dive
1. Open **Algorithm Visualization**
2. See complete 2-phase flow diagram
3. Review individual model insights:
   - LSTM 24-hour rhythm
   - Isolation Forest outlier plot
   - CNN protocol extraction
4. Understand why AURA made its decision

### Mobile Interface
1. Navigate to **Mobile Companion**
2. See mockup of iOS-style security app
3. Check current protection score
4. Review recent alerts and acknowledge threats
5. Works on any mobile browser

### Firewall Management
1. Go to **Firewall Controls**
2. Enable/disable response modes:
   - **Soft Guard**: Log-only (learning phase)
   - **Adaptive Block**: Progressive blocking
   - **Credential Shield**: After-hours checks
3. Adjust sensitivity sliders
   - LSTM: 0.0 (strict) to 1.0 (lenient)
   - Isolation Forest: Same scale
4. View blocked IPs and add custom rules

---

## 🔧 Configuration Essentials

### Enable LLM Explanations
```bash
export OPENAI_API_KEY=sk-your-key-here
export AURA_LLM_PROVIDER=openai
```

Or use local Ollama:
```bash
export AURA_LLM_PROVIDER=ollama
# Run: ollama pull llama2
# Run: ollama serve
```

### Adjust Learning Duration
```python
# In app.py, line 10
from engine import AuraConfig

cfg = AuraConfig(learning_days=14)  # 14 days instead of 7
```

### Change Anomaly Sensitivity
```python
# Lower = more sensitive to anomalies
LSTM_SENSITIVITY = 0.3    # Default 0.5
IF_SENSITIVITY = 0.4      # Default 0.5
```

---

## 📱 Mobile Experience

### Desktop Preview
- Right sidebar shows iPhone-style app mockup
- Simulates push notifications
- Shows alert acknowledgment UI
- Mobile-optimized styling

### Real Mobile Access
```bash
# On mobile device, access:
http://YOUR_COMPUTER_IP:8501
```

### Mobile Features
✅ Security score display (0-100)
✅ Alert notifications
✅ Quick acknowledge button
✅ Offline-capable (core functions)
✅ Responsive design
✅ Touch-optimized controls

---

## 🎓 Understanding the Models

### CNN (Pattern Extraction)
**What it does**: Recognizes network packet patterns
**Analogy**: Like a fingerprint scanner for packets
**Output**: Features describing packet structure

**In the Dashboard**:
- Shows protocol distribution
- Identifies which protocols are normal/anomalous
- Detects protocol combination anomalies

### LSTM (Temporal Behavior)
**What it does**: Learns when activity happens
**Analogy**: Like learning your daily schedule
**Output**: Baseline of "normal" activity times

**In the Dashboard**:
- 24-hour rhythm graph
- Shows typical traffic by hour
- Flags unusual timing

### Isolation Forest (Outlier Detection)
**What it does**: Finds unusual data points
**Analogy**: Like finding a different-colored ball in a box
**Output**: Outlier score (0=normal, 1=very anomalous)

**In the Dashboard**:
- Scatter plot: Hour vs Volume
- Blue dots = Normal
- Red X = Anomaly
- Shows isolation boundaries

### Random Forest (Ensemble)
**What it does**: Combines all models for final decision
**Analogy**: Like a jury voting
**Output**: Final anomaly/normal verdict with confidence

---

## 🚨 Common Use Cases

### Case 1: Suspicious Login Time
**Scenario**: User logs in at 2 AM (unusual)
**LSTM Detection**: Timing deviation flagged
**LLM Explanation**: "Unusual 2 AM login from S2 deviates from your learned S1 baseline."
**Action**: Flag for review, or auto-challenge with MFA

### Case 2: Data Exfiltration Attempt
**Scenario**: 500 MB transfer in 10 seconds
**IF Detection**: Volume anomaly
**CNN Detection**: Unusual packet patterns
**LLM Explanation**: "Network volume 100x normal + unknown protocol = possible data theft"
**Action**: Block source IP, quarantine connection

### Case 3: Zero-Day Attack
**Scenario**: New attack pattern never seen before
**Ensemble Result**: All 3 models flag as anomalous
**Confidence**: Very high
**LLM Explanation**: "Novel attack pattern detected. Recommend isolation."
**Action**: Immediate blocking + incident notification

---

## 📈 Dashboard Navigation Tips

### Sidebar Controls
- **Phase Badge**: Shows Learning or Defense mode
- **Dashboard Views**: 6 major analysis perspectives
- **ML Engine Status**: Current model state (epochs, trees)
- **Security Posture**: Overall risk score (0-100)
- **Operations**: Refresh data, export logs

### Keyboard Shortcuts (Streamlit)
- `R` - Rerun dashboard
- `C` - Clear cache
- `K` - Open command palette
- `?` - Help menu

### Mobile Responsiveness
- Sidebar hides on narrow screens
- Columns auto-stack on mobile
- Graphs responsive to screen size
- Touch-friendly buttons

---

## 🔍 Troubleshooting

### "Learning Phase takes 7 days"
**Reality**: Synthetic demo data accelerates this
**Solution**: Review Algorithm Visualization to understand phases
**Timeline**: Real systems need ~7 days of clean baseline

### "No anomalies detected"
**Reason**: Synthetic data is mostly normal
**To Test**: 
1. Check threat analytics for demo anomalies
2. Adjust sensitivity sliders lower
3. Review flagged events

### "LLM not responding"
**Cause**: OpenAI API key missing or quota exceeded
**Fix**:
```bash
export OPENAI_API_KEY=sk-...
# Or switch to ollama
export AURA_LLM_PROVIDER=ollama
```

### Dashboard is slow
**Solution**: Clear cache and rerun
```bash
# In Streamlit UI: Menu (☰) → Clear Cache
# Or restart: Ctrl+C in terminal, then streamlit run app.py
```

---

## 📚 Learning Resources

### Understanding the Architecture
1. Read: [README.md](README.md) - Full technical overview
2. Watch: Algorithm Visualization view (visual guide)
3. Try: Adjust sensitivity, watch detection changes

### Deep Dive into Models
1. CNN section: Protocol distribution chart
2. LSTM section: 24-hour rhythm learning
3. IF section: Outlier scatter plot

### Threat Response
1. Firewall Controls view: Response modes
2. Threat Analytics: See historical patterns
3. Mobile: Check how alerts appear

---

## 🎯 Next Steps

1. **Experiment**
   - [ ] Adjust sensitivity sliders
   - [ ] Review different chart views
   - [ ] Check mobile on phone
   - [ ] Try firewall controls

2. **Understand**
   - [ ] Read Algorithm Visualization
   - [ ] Study model explanations
   - [ ] Review threat timeline
   - [ ] Analyze anomaly patterns

3. **Customize**
   - [ ] Enable LLM (OpenAI key)
   - [ ] Adjust learning duration
   - [ ] Add custom firewall rules
   - [ ] Configure response triggers

4. **Deploy**
   - [ ] Connect real network data
   - [ ] Set up logging integrations
   - [ ] Configure alerts/notifications
   - [ ] Establish incident response

---

## 💡 Pro Tips

1. **Understanding Anomalies**
   - Start with "Soft Guard" mode during learning
   - Review explanations to understand baseline
   - Gradually increase sensitivity

2. **Mobile Monitoring**
   - Check mobile view daily
   - Customize alert notifications
   - Acknowledge threats promptly

3. **Performance Tuning**
   - Lower sensitivity = better detection but more false positives
   - Raise sensitivity = fewer alerts but might miss threats
   - Find your organization's sweet spot

4. **Security Best Practice**
   - Always backup database (.aura.db)
   - Keep ML models (.h5 files) secure
   - Regularly review firewall logs
   - Monitor trending threat patterns

---

## 📞 Support

**For issues, questions, or suggestions:**
1. Check CONFIGURATION.md for advanced settings
2. Review README.md for full architecture
3. Examine code comments in source files
4. Study LLM explanations for anomalies

---

**Welcome to AURA!** 🛡️⚡

*Learn first, protect always.*
