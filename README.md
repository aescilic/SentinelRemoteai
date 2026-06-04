# SentinelRemote - Insider Threat Detection System

This is my graduation project for Cybersecurity & Software Engineering. SentinelRemote is a rule-based insider threat detection system designed for small and medium enterprises. It monitors employee security event logs and attempts to detect anomalous behavior using statistical analysis (Z-Score), temporal profiling, and checks for Shadow AI usage.

## Overview

The main idea is to monitor what users are doing on the network and alert administrators if someone starts acting suspiciously (like downloading a massive amount of files at 3 AM). 

### Key Features:
- **Temporal Analysis:** Flags users who are active during deep night hours or significantly outside their normal working hours.
- **Volumetric Analysis (Z-Score):** Compares a user's file operations against the company average. If someone's Z-Score is over 3, it triggers a critical alert.
- **Behavioral Analysis:** Looks for suspicious accounts (like guests doing file operations) or bulk file deletions.
- **Shadow AI Detection:** Checks web visit logs to see if employees are using unauthorized AI tools (ChatGPT, Claude, etc.) which might cause data leakage.
- **Dashboard:** A Streamlit-based web interface to view all these alerts and user profiles.

## How it works

The system is split into a few main components:
1. **Data Layer (`database.py`):** Connects to an SQLite database where the logs are stored.
2. **Baseline Profiling (`baselines.py`):** Calculates normal behavior profiles and Z-Scores for everyone in the network.
3. **Detection Engine (`detection_engine.py`):** Runs the actual checks and generates alerts. Also includes basic False Positive reduction so admins don't get overwhelmed with normal daily activities.
4. **Dashboard (`dashboard.py`):** The frontend built with Streamlit and Plotly for the SOC (Security Operations Center) view.

## How to run it

First, make sure you have Python 3.9+ installed.

1. Clone this repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Generate some sample data (this will create `security_audit.db` with simulated logs):
   ```bash
   python log_generator.py
   ```

3. Run the detection engine to process the logs:
   ```bash
   python run_detection.py
   ```

4. Start the dashboard:
   ```bash
   python -m streamlit run dashboard.py
   ```
   The dashboard will open at `http://localhost:8501`. (Login: `admin` / `admin` - Demo credentials)

### Using the Kaggle Dataset
If you want to test it with more realistic data, you can use the CERT Insider Threat dataset. I wrote a script to parse a small chunk of it.
Download `email.csv` from Kaggle, place it in the folder, and run:
```bash
python fetch_kaggle_cert.py
python run_detection.py
```

## Configuration
You can change the thresholds in `config.py`. For example:
- `ZSCORE_CRITICAL = 3.0`
- `WORK_HOURS_START = 8`
- `SHADOW_AI_DOMAINS = ["chatgpt.com", "openai.com", "claude.ai", ...]`

## Testing
I wrote some tests using `pytest` to make sure the detection logic works as expected.
```bash
python -m pytest tests/ -v
```

## References
Some papers I read while researching for this project:
1. Alzaabi, F. R., & Mehmood, A. (2024). A review of recent advances, challenges, and opportunities in malicious insider threat detection using machine learning methods. *IEEE Access*.
2. Yuan, S., & Wu, X. (2021). Deep learning for insider threat detection: Review, challenges and opportunities. *Computers & Security*.
3. Shantabhushana, B. M. et al. (2025). Profiling user behavior to identify insider threats in enterprise information systems.
4. Chin, T., Li, Q., Mirone, F., & Papa, A. (2025). Conflicting impacts of shadow AI usage on knowledge leakage.
5. Ponemon Institute. (2025). Cost of Insider Risks Global Report.
