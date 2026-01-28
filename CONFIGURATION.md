# AURA Configuration Guide

## Environment Variables

```bash
# LLM Configuration
export AURA_LLM_PROVIDER=openai      # 'openai' or 'ollama'
export OPENAI_API_KEY=sk-...         # Your OpenAI API key
export OLLAMA_MODEL=llama2           # For local Ollama setup

# Database
export AURA_DB_PATH=./aura.db        # SQLite database location

# Training Parameters
export AURA_LEARNING_DAYS=7          # Learning window (days)
export AURA_LSTM_EPOCHS=5            # LSTM training epochs
export AURA_IF_CONTAMINATION=0.01    # Isolation Forest contamination rate

# Sensitivity Thresholds
export AURA_ANOMALY_THRESHOLD=0.2    # LSTM anomaly decision threshold
export AURA_IF_THRESHOLD=0.3         # Isolation Forest threshold
```

## Configuration Files

### .streamlit/config.toml
```toml
[theme]
primaryColor = "#00FFC2"
backgroundColor = "#01020A"
secondaryBackgroundColor = "#0b1020"
textColor = "#E6F1FF"
font = "sans serif"

[client]
showErrorDetails = false
```

## Firewall Policies

### Response Modes
1. **Soft Guard** - Logging only, no blocking
   - Use during baseline learning
   - Observe false positives
   
2. **Adaptive Block** - Progressive escalation
   - First occurrence: Log
   - Repeated: Block IP temporarily
   - Persistent: Permanent blocklist
   
3. **Credential Shield** - Enhanced auth checks
   - After-hours logins: Flag
   - Unusual locations: Challenge
   - Keystroke drift: MFA prompt

## Model Tuning

### LSTM (Temporal Learning)
- Sensitivity slider: 0.0 (very strict) to 1.0 (very lenient)
- Lower values: More false positives, better detection
- Higher values: Fewer alerts, risk of missing threats

### Isolation Forest (Outlier Detection)
- Contamination: Expected ratio of anomalies (0.0-0.5)
- Lower: Stricter outlier detection
- Higher: More tolerance for unusual patterns

### CNN (Pattern Recognition)
- Output dimensions: Feature compression (default 32)
- Kernel size: Pattern locality (default 3)
- Layers: Depth of pattern hierarchy

## Data Retention

```
- Events: 90 days (configurable)
- Alerts: 1 year
- Firewall Actions: 6 months
- Profiles (.h5 models): Indefinite
```

## Performance Tuning

### For High-Volume Networks
```
- Batch processing: True
- Inference batch size: 32
- Model caching: Enabled
- Alert aggregation: 5-minute windows
```

### For Low-Latency Requirements
```
- Real-time mode: Enabled
- Batch size: 1
- Model caching: In-memory
- Alert forwarding: Immediate
```

## Integration Examples

### Slack Alerts
```python
# In engine.py AuraExplainer
def post_to_slack(explanation: str):
    webhook_url = os.getenv("SLACK_WEBHOOK")
    requests.post(webhook_url, json={"text": explanation})
```

### Syslog Forwarding
```python
# In database.py
def log_to_syslog(alert: Dict):
    syslog.syslog(syslog.LOG_ALERT, json.dumps(alert))
```

### Email Notifications
```python
# In app.py
def send_email_alert(alert_message: str):
    # SMTP configuration
    pass
```

## Backup & Recovery

### Daily Backup
```bash
# Backup SQLite database
cp aura.db aura.db.backup.$(date +%Y%m%d)

# Backup ML models
cp -r profiles/ profiles.backup.$(date +%Y%m%d)
```

### Restore from Backup
```bash
cp aura.db.backup.20240128 aura.db
cp -r profiles.backup.20240128/ profiles/
streamlit run app.py  # Reload
```

## Troubleshooting

### "LLM Unavailable" Message
- Check OPENAI_API_KEY environment variable
- Verify API quota hasn't been exceeded
- Check internet connectivity
- Fall back to raw anomaly explanations

### Low Anomaly Detection Rate
- Increase learning window (more baseline data needed)
- Lower sensitivity thresholds
- Check data quality (missing features?)
- Review if threats are actually present

### High False Positive Rate
- Increase sensitivity thresholds
- Extend learning period (more diverse baseline)
- Review flagged "anomalies" manually
- Adjust response mode to "Soft Guard"

### Database Growing Too Large
- Enable data retention policies
- Archive old events to external storage
- Compress alert tables
- Vacuum SQLite (optimize file size)

```sql
-- SQLite optimization
VACUUM;
ANALYZE;
```

## Monitoring AURA's Health

### Key Metrics to Watch
- Learning progress (estimated days remaining)
- Model accuracy on validation set
- False positive rate
- Average inference latency
- Database size growth
- API error rates

### Health Check Query
```sql
SELECT 
    COUNT(*) as total_events,
    SUM(CASE WHEN is_anomaly=1 THEN 1 ELSE 0 END) as anomalies,
    COUNT(DISTINCT date(timestamp)) as days_of_data
FROM events;
```

## Security Best Practices

1. **API Key Management**
   - Never commit .env files
   - Use secrets manager (AWS Secrets, Azure Key Vault)
   - Rotate keys monthly

2. **Database Security**
   - Encrypt SQLite database (SQLCipher)
   - Use strong authentication
   - Restrict file permissions (chmod 600)
   - Regular backups to secure location

3. **Model Security**
   - Sign .h5 model files
   - Verify integrity on load
   - Keep PyTorch/TensorFlow updated
   - Scan for model poisoning

4. **Network Security**
   - Use HTTPS for Streamlit (nginx proxy)
   - Implement rate limiting
   - Enable firewall rules
   - Monitor for unauthorized access

## Compliance Checklist

- [ ] GDPR: Data retention policies configured
- [ ] HIPAA: Encryption at rest and in transit
- [ ] SOC 2: Audit logging enabled
- [ ] PCI-DSS: Sensitive data handling
- [ ] NIST: Incident response procedures documented

---

**AURA Dashboard v1.0** - Production Ready
