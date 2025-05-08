# Fit2Go Dashboard

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[日本語版はこちら](README_jp.md)

**Note: All code in this repository was generated using GitHub Copilot Agent.**

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

There are two ways to set up the development environment:

1. **Deployment Environment using Render.com**
For detailed instructions, please refer to the [deployment guide](deployment.md).

2. **Local Development Environment (local_test branch)**
For local development and testing:
- English: Please refer to the [Local Development Setup Guide](local_setup.md)
- 日本語: [ローカル開発環境セットアップガイド](local_setup_jp.md)

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