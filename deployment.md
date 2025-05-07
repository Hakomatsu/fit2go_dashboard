# Fit2Go Dashboard Deployment Guide

## Requirements

- Python 3.8 or higher
- pip
- PostgreSQL 12 or higher
- Node.js 14 or higher (for frontend build)
- Redis (recommended for session management)

## Installation Steps

1. Clone the repository
```bash
git clone https://github.com/your-repo/fit2go_dashboard.git
cd fit2go_dashboard
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit the .env file with your configuration
```

5. Initialize database
```bash
flask db upgrade
```

## Google Fit API Setup

1. Create a new project in Google Cloud Console
2. Create OAuth 2.0 client ID
3. Enable the following scopes:
   - fitness.activity.read
   - fitness.body.read
   - fitness.heart_rate.read
   - fitness.location.read
   - fitness.sleep.read

4. Configure credentials:
   Set client_id and client_secret in your .env file

## Health Connect Setup

1. Register your app in Google Play Console
2. Add the following permissions:
   - android.permission.health.READ_STEPS
   - android.permission.health.WRITE_STEPS
   - android.permission.health.READ_EXERCISE
   - android.permission.health.WRITE_EXERCISE
   - android.permission.health.READ_HEART_RATE
   - android.permission.health.WRITE_HEART_RATE

## Production Deployment

### Standard Launch
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### Systemd Service Setup
1. Create service file
```bash
sudo nano /etc/systemd/system/fit2go.service
```

2. Add the following content:
```ini
[Unit]
Description=Fit2Go Dashboard
After=network.target

[Service]
User=fit2go
Group=fit2go
WorkingDirectory=/path/to/fit2go_dashboard
Environment="PATH=/path/to/fit2go_dashboard/venv/bin"
ExecStart=/path/to/fit2go_dashboard/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start service
```bash
sudo systemctl enable fit2go
sudo systemctl start fit2go
```

## Database Backup

1. Configure automatic backup
```bash
# /etc/cron.daily/fit2go-backup
pg_dump fit2go_dashboard | gzip > /backup/fit2go_$(date +%Y%m%d).sql.gz
```

## Important Notes

- Always enable HTTPS in production
- Redis is recommended for session persistence
  ```bash
  pip install redis
  ```
- Configure log rotation
  ```bash
  sudo nano /etc/logrotate.d/fit2go
  ```
  ```
  /var/log/fit2go/*.log {
      daily
      rotate 14
      compress
      delaycompress
      missingok
      notifempty
      create 0640 fit2go fit2go
  }
  ```
- Set up regular database backups
- Consider implementing application monitoring and metrics collection
