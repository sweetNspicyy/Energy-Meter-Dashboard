import time
import math
import spidev
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import pi_config as config

# ======================================================
# HARDWARE SETUP
# ======================================================

# Setup SPI (Serial Peripheral Interface) to talk to MCP3008 ADC
spi = spidev.SpiDev()
spi.open(0, 0) # Bus 0, Device 0
spi.max_speed_hz = 1350000

# Setup Connection to InfluxDB Cloud
print("Connecting to InfluxDB Cloud...")
try:
    client = InfluxDBClient(
        url=config.INFLUX_URL,
        token=config.INFLUX_TOKEN,
        org=config.INFLUX_ORG
    )
    write_api = client.write_api(write_options=SYNCHRONOUS)
    print("Cloud Connection Successful!")
except Exception as e:
    print(f"Failed to connect to Cloud: {e}")

# ======================================================
# CORE FUNCTIONS
# ======================================================

def read_adc(channel):
    """
    Reads a single value (0-1023) from the MCP3008 ADC.
    channel: 0 to 7 (depending on where you plugged in the sensor)
    """
    if channel < 0 or channel > 7:
        return -1
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def get_rms_values():
    """
    Calculates Root Mean Square (RMS) for Voltage and Current.
    This is required for AC electricity to get the 'True' value.
    """
    num_samples = 1000  # Take 1000 snapshots to capture the full wave
    voltage_sum = 0
    current_sum = 0
    
    # 512 is the midpoint of the 0-1023 range (ADC Zero point)
    # Ideally, you can write a calibration function to find the exact zero.
    offset = 512 

    start_time = time.time()
    
    for _ in range(num_samples):
        # Read raw values
        v_raw = read_adc(1) # Voltage Sensor on Channel 1
        c_raw = read_adc(0) # Current Sensor on Channel 0
        
        # Center the wave around 0
        v_val = v_raw - offset
        c_val = c_raw - offset
        
        # Square the values (remove negatives)
        voltage_sum += (v_val ** 2)
        current_sum += (c_val ** 2)
        
    # Calculate Mean (Average) and Root
    v_rms = math.sqrt(voltage_sum / num_samples) * (3.3 / 1024.0) * config.VOLTAGE_CALIBRATION
    c_rms = math.sqrt(current_sum / num_samples) * (3.3 / 1024.0) * config.CURRENT_CALIBRATION
    
    # Noise Gate: If current is extremely low (ghost noise), set to 0
    if c_rms < 0.05: 
        c_rms = 0.0
    
    return v_rms, c_rms

# ======================================================
# MAIN LOOP
# ======================================================
print("Starting Sensor Logger...")

while True:
    try:
        # 1. Get Readings
        voltage, current = get_rms_values()
        
        # 2. Calculate Power (Apparent Power = V * I)
        power = voltage * current
        
        # 3. Create Data Point
        p = Point("energy_usage") \
            .field("voltage", float(voltage)) \
            .field("current", float(current)) \
            .field("power", float(power))
            
        # 4. Upload to Cloud
        write_api.write(bucket=config.INFLUX_BUCKET, record=p)
        
        # 5. Local Feedback
        print(f"Sent: {voltage:.1f}V | {current:.2f}A | {power:.1f}W")
        
        # 6. Wait before next reading (Save bandwidth/database limits)
        time.sleep(5) 
        
    except KeyboardInterrupt:
        print("Stopping Logger...")
        break
    except Exception as e:
        print(f"Error in Main Loop: {e}")
        time.sleep(5) # Wait before retrying