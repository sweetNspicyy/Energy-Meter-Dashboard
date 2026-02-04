# config.py
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_ADMIN_TOKEN_HERE" # Paste your InfluxDB token here
INFLUX_ORG = "thesis_org"
INFLUX_BUCKET = "energy_data"

# Calibration Constants (You must tune these using a multimeter!)
VOLTAGE_CALIBRATION = 560.0  # Adjust until Vrms matches wall outlet
CURRENT_CALIBRATION = 60.6   # Adjust until Irms matches a known load