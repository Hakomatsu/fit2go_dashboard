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

### Deploy to Render

1. Create and Set Up Render Account
- Create a Render account and log in
- Click "New +" and select "Web Service"

2. Configure the Service
- Connect your Git repository to Render
- Configure the following settings:
  * Name: fit2go-dashboard (or your preferred name)
  * Runtime: Python
  * Build Command: `pip install -r requirements.txt`
  * Start Command: `gunicorn wsgi:app`

3. Set Environment Variables
In the Render dashboard, set the following environment variables:
```
DATABASE_URL=postgres://... (PostgreSQL URL from Render service)
SECRET_KEY=your-secret-key
FLASK_ENV=production
```

4. Database Setup
- Create a PostgreSQL database in Render
- The `DATABASE_URL` environment variable will be automatically set

### M5Stack Configuration

1. Edit M5Stack configuration file
- Update the data endpoint URL to your Render application URL
- Configure HTTPS certificates if necessary

### Backup Configuration (Optional)

Render's PostgreSQL provides automatic backups, but if additional backups are needed:

1. Set up cron job on Render
```bash
# Execute daily backup
pg_dump $DATABASE_URL | gzip > /backup/fit2go_$(date +%Y%m%d).sql.gz
```

## Important Notes

- Free tier on Render has sleep mode, which may cause initial load delay
- Paid plan recommended for continuous operation
- HTTPS is automatically enabled
- Application monitoring available through Render dashboard
