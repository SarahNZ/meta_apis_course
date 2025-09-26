# Daily Log Rotation Configuration

## 🔄 Overview

Your Django application now uses **daily log rotation** to prevent log files from growing indefinitely and ensure continuous logging in production environments.

## 📋 Configuration Details

### Handler: `TimedRotatingFileHandler`
- **Rotation**: Daily at midnight (00:00:00)
- **Backup Count**: 30 days (automatically deletes logs older than 30 days)
- **File Naming**: Current log is `littlelemon.log`, archived logs get date suffixes
- **Encoding**: UTF-8 for international character support

### Log File Structure
```
logs/
├── littlelemon.log                # Current day's log
├── littlelemon.log.2025-09-26     # Yesterday's log  
├── littlelemon.log.2025-09-25     # 2 days ago
├── littlelemon.log.2025-09-24     # 3 days ago
└── ...                           # Up to 30 days of history
```

## 🔧 Technical Implementation

### Settings Configuration
```python
'handlers': {
    'file': {
        'level': 'INFO',
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'filename': os.path.join(BASE_DIR, 'logs', 'littlelemon.log'),
        'when': 'midnight',  # Rotate at midnight
        'interval': 1,       # Every 1 day
        'backupCount': 30,   # Keep 30 days of logs
        'formatter': 'verbose',
        'encoding': 'utf-8',
    },
}
```

### Key Benefits
- ✅ **No more log file overflow** - Files won't grow infinitely
- ✅ **Automatic cleanup** - Old logs deleted after 30 days
- ✅ **Continuous logging** - No interruption when rotating
- ✅ **Production ready** - Handles high-volume logging
- ✅ **Easy troubleshooting** - Find logs by date

## 📊 Production Considerations

### File Size Management
- Each daily log file starts fresh at midnight
- Prevents the single-file-grows-forever problem
- Automatic deletion keeps disk usage bounded

### Backup and Monitoring
- Archive daily logs to external storage if needed for compliance
- Monitor disk space in `/logs` directory
- Consider log aggregation tools (ELK stack, Splunk, etc.) for large deployments

### Performance Impact
- Minimal overhead during normal operation
- Brief pause at midnight during rotation (typically <1 second)
- No impact on API response times

## 🚨 Troubleshooting

### If Logs Stop Appearing
1. Check file permissions on `/logs` directory
2. Verify disk space availability
3. Check Django settings for correct `BASE_DIR`

### If Old Logs Aren't Being Deleted
- Ensure `backupCount: 30` is set correctly
- Check file system permissions for deletion rights
- Verify the handler is using `TimedRotatingFileHandler`

### Manual Log Rotation Testing
```python
# Run the test script to verify configuration
pipenv run python test_log_rotation.py
```

## 🔍 Monitoring Log Health

### Check Current Log Status
```powershell
# View current log file info
Get-ChildItem logs\littlelemon.log | Select-Object Name, Length, LastWriteTime

# View recent log entries
Get-Content logs\littlelemon.log -Tail 10

# List all log files with sizes
Get-ChildItem logs\*.log | Sort-Object Name
```

### Log Volume Monitoring
- Monitor daily log file sizes for unusual spikes
- Set up alerts if logs exceed expected size thresholds
- Track log rotation success in deployment monitoring

---
*Updated: September 26, 2025*  
*Configuration applies to: LittleLemon Django API*