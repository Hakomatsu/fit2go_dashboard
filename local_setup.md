# Local Development Environment Setup Guide

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher (locally installed)
- pip (Python package manager)

## Setup Steps

1. Clone local_test branch
```bash
git clone <repository-url>
cd fit2go_dashboard
git checkout local_test
```

2. PostgreSQL Setup
- Install PostgreSQL (if not already installed)
- Create database
```bash
psql -U postgres
CREATE DATABASE fit2go_dashboard;
```

3. Create and activate virtual environment
```bash
python -m venv venv
# For Windows
venv\Scripts\activate
# For Linux/macOS
source venv/bin/activate
```

4. Install dependencies
```bash
pip install -r requirements.txt
```

5. Set environment variables
```bash
cp .env.example .env
```
Edit `.env` file as follows:
```env
FLASK_ENV=development
DATABASE_URL=postgresql://localhost/fit2go_dashboard
SECRET_KEY=your-secret-key-for-development
```

6. Initialize database
```bash
flask db upgrade
```

7. Start development server
```bash
flask run --host=0.0.0.0 --port=5000
```

## Insert Test Data

You can insert test data to simulate data transmission from M5Stack:

```bash
python tests/insert_test_data.py
```

## Development Notes

1. Debug Mode
- Development server starts automatically in debug mode
- Detailed errors are displayed in browser
- Code changes are automatically reflected

2. Check Logs
- Application logs are output to `logs/development.log`
- Detailed logs including debug information are available

3. Database Operations
- Use GUI tools like pgAdmin or DBeaver to directly check and manipulate the database
- Connection information:
  - Host: localhost
  - Database: fit2go_dashboard
  - Port: 5432 (default)

## Troubleshooting

1. Database Connection Error
- Verify PostgreSQL service is running
- Check DATABASE_URL setting is correct

2. Dependency Error
- Verify virtual environment is activated
- Re-run `pip install -r requirements.txt`

3. Migration Error
```bash
flask db stamp head
flask db migrate
flask db upgrade
```

## Running Tests

Run unit tests and E2E tests:

```bash
pytest
```

Run specific tests:

```bash
pytest tests/test_api.py
```