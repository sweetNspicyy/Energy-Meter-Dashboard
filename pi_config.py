# pi_config.py
# ======================================================
# CONFIGURATION FILE
# ======================================================

# --- InfluxDB Cloud Settings ---
# You get these from your InfluxDB Cloud Account
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com" # Example: Check your specific cloud URL
INFLUX_TOKEN = "YOUR_INFLUXDB_CLOUD_API_TOKEN"
INFLUX_ORG = "YOUR_INFLUXDB_EMAIL_OR_ORG_ID"
INFLUX_BUCKET = "energy_data"

# --- Sensor Calibration ---
# These values act as multipliers to convert raw ADC numbers into real Volts/Amps.
# YOU MUST TUNE THESE using a standard multimeter for accuracy.
# If your reading is too low, increase this number. If too high, decrease it.
VOLTAGE_CALIBRATION = 560.0 
CURRENT_CALIBRATION = 60.6