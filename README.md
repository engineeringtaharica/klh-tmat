# KLH-TMAT

## Description
Middleware for integrating HOBO Datalogger to Indonesian KLH's TMAT server.
The data is grabbed from Li-Cor Cloud and then transferred to KLH's TMAT server.
Most of the data transfer is using request library to GET and POST the data.

## Installation
### Update local APT repositories and install Python if not installed yet.
```bash
sudo apt update && sudo apt install python3 python3-venv python3-pip -y
```

### Create and Navigate to project directory
```bash
cd ~/Documents
mkdir klh-tmat
cd klh-tmat
```

### Clone this repository
```bash
git clone https://github.com/engineeringtaharica/klh-tmat.git
```

### Create and activate virtual environment
```bash
python3 -m venv venv
venv/bin/activate
```

### Install required libraries
```bash
python -m pip install -r requirements.txt
```

### Edit the klh-tmat files to suit your project folder directory using Nano file editor
```bash
cd etc/systemd/system
nano klh-tmat.service
nano klh-tmat.timer
```

### Move the klh-tmat files to ~/etc/systemd/system folder
```bash
mv klh-tmat.service /etc/systemd/system
mv klh-tmat.timer /etc/systemd/system
```

### Reload systemd daemon
```bash
sudo systemctl daemon-reload
```

### Enable and start the timer
```bash
sudo systemctl enable --now klh-tmat.timer
```

### Start (forcefully) the service
```bash
sudo systemctl start klh-tmat.service
```


