#import necessary python packages

import psutil
import sqlite3
import time
import os
from datetime import datetime
from flask import Flask, render_template, jsonify
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import threading
import plotly.graph_objs as go
import plotly
import json
from slack_sdk import WebhookClient
from slack_sdk.errors import SlackApiError
import logging 
import matplotlib.dates as mdates

# define database file and paths
db_file = os.path.expanduser("~/monitor/metrics.db")
plot_file = os.path.expanduser("~/monitor/graphs/metrics_plot.png")
log_file = os.path.expanduser("~/monitor/logs/alerts.log")

# Slack configuration
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"  # Placeholder Replace with actual webhook


# Ensure directories exists
os.makedirs(os.path.dirname(db_file), exist_ok=True)
os.makedirs(os.path.dirname(plot_file), exist_ok=True)
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=log_file, 
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Initialise Flask app and Slack client
app = Flask(__name__)
slack_webhook = WebhookClient(SLACK_WEBHOOK_URL)

# Store recent metrics for plotting
recent_metrics =[]
MAX_METRICS = 50 # Keep only the last 50 records

# Define thresholds
CPU_THRESHOLD = 80  # % CPU Usage
MEMORY_THRESHOLD = 90 # % Memory Usage
DISK_THRESHOLD = 500  # MB Disk Read/Write
NETWORK_THRESHOLD = 500  # MB Network Sent/Received
ALERT_COOLDOWN = 300 # 5minutes
last_alert = 0

# initialize SQLite database and create a table named metrics if it doesn't already exist.
def init_db():
    """Initialize the SQLite database and create the metrics table."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS metrics (
                      timestamp TEXT,
                      cpu_usage REAL,
                      memory_usage REAL,
                      disk_read REAL,
                      disk_write REAL,
                      network_sent REAL,
                      network_received REAL)''')
    conn.commit()
    conn.close()

# collect system metrics and return them as a dictionary
def collect_metrics():
    """Collect system metrics"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    disk_io = psutil.disk_io_counters()
    network_io = psutil.net_io_counters()
    
    metrics = {
        "timestamp": timestamp,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "disk_read": disk_io.read_bytes / (1024 ** 2),  # Convert to MB
        "disk_write": disk_io.write_bytes / (1024 ** 2),  # Convert to MB
        "network_sent": network_io.bytes_sent / (1024 ** 2),  # Convert to MB
        "network_received": network_io.bytes_recv / (1024 ** 2)  # Convert to MB
    }

    # Store recent metrics
    if len(recent_metrics) >= MAX_METRICS:
        recent_metrics.pop(0)
    recent_metrics.append(metrics)

    return metrics


# store the collected metrics in the SQLite database
def save_metrics(metrics):
    """Save metrics to the SQLite database."""
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (metrics["timestamp"], metrics["cpu_usage"], metrics["memory_usage"], 
                        metrics["disk_read"], metrics["disk_write"], 
                        metrics["network_sent"], metrics["network_received"]))
        conn.commit()
        print("Metrics saved successfully.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

# Send Slack Alert
def send_slack_alert(message):
    """Send a Slack alert via webhook and log it."""
    try:
        response = slack_webhook.send(text=message)
        logger.info(f"Slack alert sent successfully: {message}")
        print(f"Slack Alert Sent: {message}")        
    except SlackApiError as e:
        logger.error(f"Error sending Slack alert: [message] | Error: {e}")
        print(f"Error sending Slack message: {e}")

# Check and send alerts
def check_alerts(metrics):
    """Check metrics against thresholds and send alerts if necessary."""
    global last_alert
    alerts = []    
    
    if metrics["cpu_usage"] > CPU_THRESHOLD:
        alerts.append(f" 🔥 High CPU Usage: {metrics['cpu_usage']}%")
    if metrics["memory_usage"] > MEMORY_THRESHOLD:
        alerts.append(f" 📦 High Memory Usage: {metrics['memory_usage']}%")
    if metrics["disk_read"] > DISK_THRESHOLD or metrics["disk_write"] > DISK_THRESHOLD:
        alerts.append(f" 💾 High Disk Usage: Read {metrics['disk_read']}MB, Write {metrics['disk_write']}MB")
    if metrics["network_sent"] > NETWORK_THRESHOLD or metrics["network_received"] > NETWORK_THRESHOLD:
        alerts.append(f" 🌐 High Network Usage: Sent {metrics['network_sent']}MB, Received {metrics['network_received']}MB")
    
    if alerts and (time.time() - last_alert) > ALERT_COOLDOWN:
        alert_message = f"Alert at {metrics['timestamp']}:\n" + "\n".join(alerts)
        send_slack_alert(alert_message)
        last_alert = time.time()


# Plot and save system metrics periodically
def plot_metrics():
    """Plot and save system metrics periodically with dual Y-axes and readable timestamps."""
    while True:
        if recent_metrics:
            # Convert string timestamps to datetime objects
            timestamps = [datetime.strptime(metric["timestamp"], "%Y-%m-%d %H:%M:%S") 
                         for metric in recent_metrics]
            cpu_usage = [metric["cpu_usage"] for metric in recent_metrics]
            memory_usage = [metric["memory_usage"] for metric in recent_metrics]
            disk_read = [metric["disk_read"] for metric in recent_metrics]
            disk_write = [metric["disk_write"] for metric in recent_metrics]
            network_sent = [metric["network_sent"] for metric in recent_metrics]
            network_recv = [metric["network_received"] for metric in recent_metrics]
            
            fig, ax1 = plt.subplots(figsize=(14, 5))  # Wider figure: 14 inches
            
            # Left Y-axis (CPU/Memory, %)
            ax1.plot(timestamps, cpu_usage, label="CPU Usage (%)", marker="o", color="blue")
            ax1.plot(timestamps, memory_usage, label="Memory Usage (%)", marker="s", color="green")
            ax1.set_xlabel("Time")
            ax1.set_ylabel("Usage (%)", color="blue")
            ax1.tick_params(axis="y", labelcolor="blue")
            ax1.set_ylim(0, 100)
            
            # Right Y-axis (Disk/Network, MB)
            ax2 = ax1.twinx()
            ax2.plot(timestamps, disk_read, label="Disk Read (MB)", marker="^", color="red")
            ax2.plot(timestamps, disk_write, label="Disk Write (MB)", marker="v", color="orange")
            ax2.plot(timestamps, network_sent, label="Network Sent (MB)", marker="x", color="purple")
            ax2.plot(timestamps, network_recv, label="Network Received (MB)", marker="d", color="brown")
            ax2.set_ylabel("Data (MB)", color="red")
            ax2.tick_params(axis="y", labelcolor="red")
            
            # Combine legends
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
            
            # Fix X-axis: fewer ticks, rotated, Format X-axis as datetime
            ax1.set_xticks(timestamps[::6])  # Every 6th timestamp (~30s intervals)
            ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))  # e.g., "2025-03-30 10:05:35"
            ax1.tick_params(axis="x", rotation=45)
            
            plt.title("System Metrics")
            plt.tight_layout()
            plt.savefig(plot_file)
            plt.close()
        time.sleep(30)  # Plot every 30 seconds


# Flask API to serve metrics data
@app.route("/metrics")
def get_metrics():
    """API endpoint to retrieve metrics data."""
    return jsonify(recent_metrics)

# Flask route for dashboard
@app.route("/")
def index():
    """Render the dashboard template."""
    return render_template("dashboard.html")

# main function to run the monitoring tool
def main():
    init_db()
    print("Starting system metrics collection...")
    try:
        while True:
            metrics = collect_metrics()
            save_metrics(metrics)
            check_alerts(metrics)
            print(metrics)
            time.sleep(5)  # Collect every 5 seconds
    except KeyboardInterrupt:
        print("Stopping metrics collection.")

# Start Flask server
if __name__ == "__main__":
    # Start system monitoring in a separate thread
    threading.Thread(target=main, daemon=True).start()
    
    # Start plotting metrics with Matplotlib in a separate thread
    threading.Thread(target=plot_metrics, daemon=True).start()
    
    time.sleep(2)  # Give threads a head start
    print("Starting Flask server...")
    # Start Flask server
    app.run(debug=False, host="0.0.0.0", port=5000)

