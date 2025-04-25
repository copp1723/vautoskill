# vAuto Feature Verification System

## Overview

The vAuto Feature Verification System automates the merchandising process for new vehicles in vAuto by:
- Identifying inventory with an age of 0-1 days
- Accessing window sticker content
- Parsing features
- Updating Vehicle Attributes checkboxes

This system is built using Amazon Nova Act technology for browser automation to create a reliable, maintainable, and scalable solution.

## Project Structure

```
rd2_vauto/
├── configs/                # Configuration files
│   ├── dealership_config.json    # Dealership-specific configuration
│   ├── feature_mapping.json      # Feature to checkbox mapping
│   ├── system_config.json        # System-wide configuration
├── docs/                   # Documentation
├── reports/                # Generated reports
├── src/                    # Source code
│   ├── core/               # Core nova act engine
│   │   ├── nova_engine.py       # Nova Act Engine implementation
│   ├── modules/            # Feature modules
│   │   ├── authentication/       # Authentication module
│   │   │   ├── auth_module.py         # Login and 2FA handling
│   │   ├── inventory/            # Inventory and vehicle processing
│   │   │   ├── inventory_discovery.py  # Inventory list navigation and filtering
│   │   │   ├── window_sticker.py       # Window sticker processing
│   │   │   ├── checkbox_management.py  # Checkbox updating
│   │   ├── feature_mapping/      # Feature mapping module
│   │   │   ├── feature_mapper.py       # Feature mapping with fuzzy matching
│   │   ├── reporting/            # Reporting module
│   │   │   ├── reporting.py            # Report generation and notifications
│   │   ├── workflow.py           # Workflow orchestration
│   ├── main.py             # Main entry point
├── tests/                  # Test files
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Amazon Nova Act SDK API key
- vAuto dealership credentials

### Setup

1. Clone the repository:
   ```bash
   cd ~/Desktop
   git clone <repository_url>
   cd rd2_vauto
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your Nova Act API key and other settings
   ```

4. Configure dealership settings:
   ```bash
   # Edit configs/dealership_config.json with your dealership information
   ```

## Configuration

### System Configuration (system_config.json)

```json
{
  "nova_act": {
    "timeout": 60,
    "retry_attempts": 3,
    "headless": true
  },
  "feature_mapping": {
    "confidence_threshold": 90,
    "similarity_algorithm": "fuzzywuzzy.ratio"
  },
  "processing": {
    "max_vehicles_per_batch": 100,
    "session_timeout": 25
  },
  "reporting": {
    "email_recipients": ["manager@example.com"],
    "log_level": "INFO",
    "store_logs_days": 30
  }
}
```

### Dealership Configuration (dealership_config.json)

```json
[
  {
    "dealer_id": "dealer123",
    "name": "Downtown Toyota",
    "timezone": "America/Chicago",
    "credentials": {
      "username": "YOUR_USERNAME",
      "password": "YOUR_PASSWORD",
      "auth_email": "auth_email@example.com"
    },
    "schedules": {
      "morning_run": "07:00",
      "afternoon_run": "14:00"
    },
    "report_recipients": ["dealership_manager@example.com"]
  }
]
```

### Feature Mapping (feature_mapping.json)

Maps window sticker feature names to vAuto checkbox names, with alternative names for fuzzy matching:

```json
{
  "Adjustable Pedals": [
    "Adjustable Pedals",
    "Power Adjustable Pedals",
    "Pedals - Power Adjustable"
  ],
  "Bluetooth": [
    "Bluetooth",
    "Bluetooth Connection",
    "Bluetooth Streaming Audio"
  ]
}
```

## Usage

### Running the System

Start the system with scheduled execution:

```bash
cd ~/Desktop/rd2_vauto
python src/main.py
```

Run a test execution for the first dealership:

```bash
python src/main.py --test
```

### Monitoring and Reports

- Reports are generated in the `reports/` directory
- Email notifications are sent after each execution
- Processing metrics are logged to `reports/metrics.csv`

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for all functions and classes
- Keep functions small and single-purpose

### Testing

- Write tests for all new functionality
- Aim for at least 80% code coverage
- Create both unit and integration tests

### Error Handling

- Use try/except blocks for all external interactions
- Log all errors with appropriate detail
- Implement recovery mechanisms where possible

### Documentation

- Document all public interfaces
- Update README and other docs as needed
- Add comments for complex logic

### Commit Practices

- Make small, focused commits
- Write clear commit messages
- Create feature branches for new functionality
- Submit pull requests for review

## Key Components

### Nova Act Engine

Handles browser automation, manages sessions, and provides error recovery mechanisms.

### Authentication Module

Handles login flow with username/password, manages 2FA via email, and monitors session validity.

### Inventory Discovery Module

Navigates to inventory list, applies age filters (0-1 days), and extracts vehicle links.

### Window Sticker Processing Module

Accesses window sticker content, extracts features by section, and processes feature text.

### Feature Mapping Module

Maps window sticker features to vAuto checkboxes using fuzzy matching with confidence thresholds.

### Checkbox Management Module

Updates vAuto checkboxes based on mapped features, saves changes, and confirms successful updates.

### Workflow Module

Orchestrates the entire process, handles authentication, session management, and coordinates all modules.

### Reporting Module

Generates execution reports, sends notifications, and logs processing metrics.

## Roadmap

### Phase 1: Core Functionality (Current)
- Implement Inventory Discovery Module
- Create Window Sticker Processing Module
- Build Checkbox Management Module
- Develop basic workflow orchestration
- Implement basic reporting

### Phase 2: Enhancements
- Improve feature mapping algorithms
- Enhance error handling and recovery
- Add multi-dealership support
- Develop advanced reporting

### Phase 3: Testing and Deployment
- Write comprehensive tests
- Set up monitoring
- Build administrative interfaces
- Prepare user training materials

## Troubleshooting

- Check the log file (`vauto_verification.log`) for detailed error information
- Verify that credentials in the dealership configuration are correct
- Ensure the Nova Act API key is properly set in the `.env` file
- Check network connectivity to vAuto and email servers

## Support and Maintenance

For support with this system, contact the development team at: `dev-team@example.com`
