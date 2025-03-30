#!/usr/bin/env bash

set -e  # Exit on any error

if [ "$EUID" -ne 0 ]; then
   echo "This script must be run as root (e.g., sudo ./setup.sh)" 
   exit 1
fi

# Define log file and ensure log directory exists
LOG_FILE="/var/log/monitor_setup/setup.log"
mkdir -p "/var/log/monitor_setup"
touch "$LOG_FILE"
chown "$USER:$USER" "$LOG_FILE"

# Virtual environment directory
VENV_DIR="$HOME/monitor/venv"

# user's home
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_MONITOR=$REPO_DIR/monitor.py
DEST_MONITOR="$HOME/monitor/monitor.py"

# plot template
SOURCE_TEMPLATE=$REPO_DIR/templates/dashboard.html
DEST_TEMPLATE="$HOME/monitor/templates/dashboard.html"


# Function to log messages
log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") - $1" | tee -a "$LOG_FILE"
    logger -t monitor_setup "$1"
}

# Function to manage monitor.py and templates
move_monitor_script() {
    # Check if monitor.py exists in the source directory
    if [ -f "$SOURCE_MONITOR" ]; then
        # Check and delete existing monitor.py in root if it exists
        if [ -f "$DEST_MONITOR" ]; then
            log "Deleting existing monitor.py at $DEST_MONITOR..."
            rm -f "$DEST_MONITOR"
        fi

        # Copy monitor.py to the destination directory
        log "Copying monitor.py from $SOURCE_MONITOR to $DEST_MONITOR..."
        mkdir -p "$HOME/monitor"
        cp "$SOURCE_MONITOR" "$DEST_MONITOR"
        log "monitor.py copied successfully. Source at $SOURCE_MONITOR preserved."
    else
        # Handle error if monitor.py is not found
        log "Error: monitor.py not found at $SOURCE_MONITOR. Please create it in your home directory first."
        echo "Error: monitor.py not found at $SOURCE_MONITOR."
        exit 1
    fi

    # Check if dashboard.html exists in the source directory
    if [ -f "$SOURCE_TEMPLATE" ]; then
        # Copy dashboard.html to the destination directory
        log "Copying dashboard.html from $SOURCE_TEMPLATE to $DEST_TEMPLATE..."
        mkdir -p "$HOME/monitor/templates"
        cp "$SOURCE_TEMPLATE" "$DEST_TEMPLATE"
    else
        # Handle warning if dashboard.html is not found
        log "Warning: dashboard.html not found at $SOURCE_TEMPLATE. Dashboard may fail. Please create it in your home directory first."
    fi
}

# Function to create necessary directories
create_directories() {
    DIRECTORIES=("$HOME/monitor/graphs" "$HOME/monitor/logs")
    for directory in "${DIRECTORIES[@]}"; do
        if [ ! -d "$directory" ]; then            
            log "Creating directory: $directory..."
            mkdir -p "$directory"
            chown "$USER:$USER" "$directory"
        else
            log "Directory $directory already exists."            
        fi
    done   
  
}

# Function to check if a package is installed
is_package_installed() {
    dpkg -s "$1" &> /dev/null
}

# Function to check if a Python package is installed in venv
is_python_package_installed() {
    [ -f "$VENV_DIR/bin/pip3" ] && "$VENV_DIR/bin/pip3" show "$1" &> /dev/null 
}

# Function to install system packages 
install_packages () {    
    log "Updating package lists..."
    sudo apt update -y
    
    PACKAGES=("python3" "python3-pip" "sqlite3" "python3-venv")
    for package in "${PACKAGES[@]}"; do
        if is_package_installed "$package"; then
            log "$package is already installed."                       
        else                       
            log "Installing $package..."
            sudo apt install "$package" -y
            log "$package installed successfully."
        fi
    done

}

# Function to set up virtual environment
setup_virtualenv() {
    if [ -d "$VENV_DIR" ]; then
        log "Removing existing virtual environment at $VENV_DIR..."
        rm -rf "$VENV_DIR"
    fi    
    log "Creating virtual environment at $VENV_DIR..."
    if ! python3 -m venv "$VENV_DIR"; then
        log "❌ Failed to create virtual environment. Ensure python3-venv is installed."
        exit 1
    fi
    log "Virtual environment created successfully at $VENV_DIR."
}


# Function to Install Python libraries in venv
install_python_libraries() {    
    log "Installing python libraries in virtual environment"

    PYTHON_PACKAGES=("psutil" "matplotlib" "plotly" "flask" "slack_sdk")
    for package in "${PYTHON_PACKAGES[@]}"; do
        if  is_python_package_installed "$package"; then
            log "Python package $package is already installed in virtual environment."                       
        else
            log "Installing Python package: $package..."
            if ! "$VENV_DIR/bin/pip3" install "$package"; then
                log "❌ Failed to install critical Python package: $package"
                exit 1
            else
                log "Python package $package installed successfully."
            fi            
            
        fi
    done
}


# Main execution
log "Starting system setup..."
echo "Starting system setup..."
create_directories
move_monitor_script
install_packages
setup_virtualenv
install_python_libraries


# Run the monitoring tool

MONITOR_SCRIPT="$HOME/monitor/monitor.py"
if [ -f "$MONITOR_SCRIPT" ]; then    
    echo "Running the monitoring tool..."
    "$VENV_DIR/bin/python3" "$MONITOR_SCRIPT"
    
else
    log "Error: Monitoring script not found at $MONITOR_SCRIPT. Kindly create the python script first."
    echo "Error: Monitoring script not found at $MONITOR_SCRIPT." 
    exit 1
fi

