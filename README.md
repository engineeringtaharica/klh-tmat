# KLH-TMAT

## Description
Integrating HOBO Datalogger to Indonesian KLH's TMAT server

## Installation
```bash
# Update local APT repositories and install Python if not installed yet.
sudo apt update && sudo apt install python3 python3-venv python3-pip -y

# Navigate to project directory
cd ~/Documents/klh-tmat

# Create and activate virtual environment
python3 -m venv venv

# Install required libraries
./venv/bin/python -m pip install -r requirements.txt

# Edit the klh-tmat files to suit your project folder directory using Nano file editor
cd etc/systemd/system
nano klh-tmat.service
nano klh-tmat.timer

# Move the klh-tmat files to ~/etc/systemd/system folder
mv klh-tmat.service /etc/systemd/system
mv klh-tmat.timer /etc/systemd/system

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the timer
sudo systemctl enable --now klh-tmat.timer

# Start (forcefully) the service
sudo systemctl start klh-tmat.service
```


