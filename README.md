# Fit2Go Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[日本語版はこちら](README_jp.md)

A web dashboard application for the Flexispot Sit2Go fitness chair. This application visualizes fitness data sent from M5Stack devices in real-time and manages exercise records.

## Key Features

### Real-time Monitoring
- Display current speed (km/h), RPM, and METs values in tachometer format
- Real-time display of exercise distance, calories burned, and elapsed time
- Session data visualization

### Daily Summary
- Exercise data aggregation in 15-minute intervals
- Display average speed, RPM, distance, and calories by time period
- Daily cumulative data display

### Calendar Function
- Monthly exercise record viewing
- Detailed data display by date
- Detailed graph display by session

### Cumulative Data Management
- Display total exercise time, total distance, and total calories burned
- Export history data functionality

## Tech Stack

- Backend: Python/Flask
- Database: PostgreSQL
- Frontend: HTML/CSS/JavaScript
- Charts: Plotly.js
- Calendar: FullCalendar
- Hosting: Render

## Development Environment Setup

1. Clone the repository
```bash
git clone <repository-url>
cd fit2go-dashboard
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set environment variables
```bash
cp .env.example .env
# Edit the .env file to set required environment variables
```

5. Setup database
```bash
flask db upgrade
```

6. Start development server
```bash
flask run
```

## Deployment

This application is configured to be deployed on [Render](https://render.com).
For detailed deployment instructions, please refer to the [deployment guide](deployment.md).

## Contributing

1. Fork this repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'feat: add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## Commit Message Convention

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.
Pull request titles should also follow the same convention.

Available types:
- feat: New feature
- fix: Bug fix
- docs: Documentation only changes
- style: Changes that do not affect code behavior
- refactor: Code changes that neither fixes a bug nor adds a feature
- perf: Performance improvement
- test: Adding or modifying tests
- build: Changes to build system or external dependencies
- ci: Changes to CI configuration
- chore: Other changes
- revert: Revert previous commits

## License

This project is released under the MIT License. See the [LICENSE](LICENSE) file for details.