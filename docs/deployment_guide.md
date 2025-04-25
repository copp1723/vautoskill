# vAuto Feature Verification System Deployment Guide

This guide provides instructions for deploying the vAuto Feature Verification System in a production environment.

## System Requirements

### Hardware Requirements
- CPU: Minimum 2 cores, recommended 4 cores
- RAM: Minimum 4GB, recommended 8GB
- Disk Space: Minimum 20GB SSD
- Network: Reliable internet connection

### Software Requirements
- Operating System: Linux (Ubuntu 20.04 LTS or newer), Windows Server 2019+, or macOS 11+
- Python: 3.9 or newer
- Browser: Latest version of Chrome (for Nova Act)

## Installation

### 1. Set Up Python Environment

#### For Linux/macOS:
```bash
# Install Python 3.9+ if not already installed
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create a virtual environment
mkdir -p /opt/vauto-verification
cd /opt/vauto-verification
python3 -m venv venv
source venv/bin/activate
```

#### For Windows:
```powershell
# Install Python 3.9+ from python.org if not already installed

# Create a virtual environment
mkdir C:\vauto-verification
cd C:\vauto-verification
python -m venv venv
.\venv\Scripts\activate
```

### 2. Install the Application

```bash
# Clone the repository
git clone <repository_url> .

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure the Application

```bash
# Create and edit the .env file
cp .env.example .env
# Edit .env with your configuration

# Edit dealership configuration
nano configs/dealership_config.json
# Add your dealership information

# Configure system settings if needed
nano configs/system_config.json
```

### 4. Set Up as a Service

#### For Linux (Systemd):
Create a service file:
```bash
sudo nano /etc/systemd/system/vauto-verification.service
```

Add the following content:
```
[Unit]
Description=vAuto Feature Verification System
After=network.target

[Service]
User=<service_user>
Group=<service_group>
WorkingDirectory=/opt/vauto-verification
Environment="PATH=/opt/vauto-verification/venv/bin"
ExecStart=/opt/vauto-verification/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vauto-verification
sudo systemctl start vauto-verification
```

#### For Windows (Windows Service):
Using NSSM (Non-Sucking Service Manager):
1. Download NSSM from https://nssm.cc/
2. Extract and run:
```powershell
nssm.exe install vAuto-Verification
```
3. Set the Path to: `C:\vauto-verification\venv\Scripts\python.exe`
4. Set Arguments to: `C:\vauto-verification\src\main.py`
5. Set Startup Directory to: `C:\vauto-verification`
6. Configure other options as needed

### 5. Set Up Logging

Create a log directory:
```bash
mkdir -p /var/log/vauto-verification
chmod 755 /var/log/vauto-verification
```

Configure log rotation (Linux):
```bash
sudo nano /etc/logrotate.d/vauto-verification
```

Add:
```
/var/log/vauto-verification/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 <service_user> <service_group>
}
```

### 6. Security Considerations

- Store all credentials and API keys securely
- Use environment variables for sensitive information
- Limit file permissions on configuration files
- Run the service with minimal required permissions
- Use a dedicated service account
- Consider using a secrets management service for production deployments

## Monitoring and Maintenance

### Monitoring
- Check system logs: `sudo journalctl -u vauto-verification`
- Review generated reports in the `reports/` directory
- Set up email notifications for errors
- Consider integrating with monitoring systems like Prometheus/Grafana

### Backup and Recovery
- Regularly back up configuration files
- Version control all custom modifications
- Document deployment steps and configurations
- Create a disaster recovery plan

### Updates
- Set up a test environment for testing updates
- Follow a standard change management process
- Test thoroughly before deploying to production
- Create a rollback plan for each update

## Scaling Considerations

### Multiple Dealerships
- Adjust `max_vehicles_per_batch` in system_config.json based on system capacity
- Consider deploying separate instances for large dealership groups
- Implement load balancing for high-volume scenarios

### High Availability
- Consider deploying redundant instances
- Implement health checks and automatic failover
- Use database replication for metrics storage

## Troubleshooting

### Common Issues

#### Service Won't Start
- Check logs: `journalctl -u vauto-verification -n 100`
- Verify Python path in service definition
- Check permissions on files and directories

#### Authentication Failures
- Verify credentials in dealership configuration
- Check for vAuto login page changes
- Test 2FA email retrieval

#### Feature Mapping Issues
- Adjust confidence threshold in system configuration
- Add alternative feature names in feature_mapping.json
- Check for changes in window sticker format

## Support and Contact

For technical support, contact:
- Email: `dev-team@example.com`
- Issue Tracker: `<repository_url>/issues`
