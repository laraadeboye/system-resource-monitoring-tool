# System-resource-monitoring-tool
A DevOps tool to monitor system metrics (CPU, memory, disk, network) on Ubuntu-based systems, providing real-time visualizations and Slack alerts. Built for multicloud environments like AWS EC2, it features a Flask web dashboard, Matplotlib static plots, and SQLite storage.

## Features
- **Metrics**: CPU usage (%), memory usage (%), disk I/O (MB), network I/O (MB).
- **Dashboard**: Interactive web interface at `http://<your-ip>:5000/` using Flask and Plotly.
- **Real-time Updates**: Metrics collected every 5 seconds.
- **Plots**: Static graphs saved to `/root/monitor/graphs/metrics_plot.png`.
- **Alerts**: Slack notifications for high usage thresholds (configurable in `monitor.py`).
- **Storage**: Metrics logged to SQLite at `/root/monitor/metrics.db`.

## Prerequisites
- **System**: Ubuntu-based OS (e.g., EC2 Ubuntu AMI).
- **Access**: Root privileges (via `sudo`).
- **Network**: Port 5000 open for the dashboard (e.g., EC2 security group).
- **Optional**: Slack webhook for alerts (edit `monitor.py`).

## Installation
1. **Clone the Repository**:

   ```bash
   git clone https://github.com/laraadeboye/system-resource-monitoring-tool.git
   ```
2. **Navigate to the Directory**:

   ```bash
   cd system-resource-monitoring-tool
   ```
3. **Run the Setup Script**:

   ```bash
   chmod +x setup.sh
   sudo ./setup.sh
   ```
    - Installs dependencies (python3, pip, sqlite3, etc.).
    - Sets up a virtual environment in /root/monitor/venv.
    - Copies monitor.py and dashboard.html to /root/monitor/.
    - Starts the monitoring tool.

## Usage
- **Web Dashboard**: Access at `http://<your-ec2-public-ip>:5000/` (e.g., http://100.26.184.15:5000/).
- **Static Plots**: View graphs at `/root/monitor/graphs/metrics_plot.png` (updated every 30s).
- **Slack Alerts**: Configure SLACK_WEBHOOK_URL in monitor.py for notifications (e.g., CPU > 80%).
- **Logs**:
   - **Setup logs**: /var/log/monitor_setup/setup.log.
   - **Alert logs**: /root/monitor/logs/alerts.log.
- **Metrics Data**: Stored in /root/monitor/metrics.db (SQLite).

## Configuration
**Slack Alerts**:
- Edit monitor.py:

```python
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```
- Adjust thresholds: (e.g., `CPU_THRESHOLD = 80`).

**Plot Frequency**: Change `time.sleep(30)` in `plot_metrics()` for faster/slower updates.
**Port**: Modify `app.run(port=5000)` in `monitor.py` if needed (update security group too).

## Troubleshooting:
**"500 Internal Server Error"**:
- Check: `ls /root/monitor/templates/dashboard.html`—ensure it’s present.
- Restart: `sudo /root/monitor/venv/bin/python3 /root/monitor/monitor.py`.

**Dashboard not accessible**:
- Verify Flask runs on `0.0.0.0:5000`:
```
sudo netstat -tuln | grep 5000  # Should show 0.0.0.0:5000
```
- Ensure port `5000` is open in your EC2 security group and firewall
- Plot Warnings: Matplotlib logs about categorical units are harmless—fixed to show date/time.
- Logs: Check `/root/monitor/logs/alerts.log` or console for errors.

## Development
Repo: Part of **multicloud-devops-ai-projects** as a submodule.
Contribute: Fork, update, and submit a PR to enhance metrics, visuals, or alerting.

## License
[MIT License](LICENSE)


Built by laraadeboye for MULTICLOUD-AI-INFRA-AGENT-DEVOPS exploration, March 2025.