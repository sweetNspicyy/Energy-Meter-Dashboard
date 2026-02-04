import time
import math
import spidev
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import config

# Setup SPI for MCP3008
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1350000

# Setup Database
client = InfluxDBClient(url=config.INFLUX_URL, token=config.INFLUX_TOKEN, org=config.INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def read_adc(channel):
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

def get_rms_values():
    # We sample for 200ms (approx 12 cycles at 60Hz)
    num_samples = 1000
    voltage_sum = 0
    current_sum = 0
    
    # Offset (Middle of 3.3V ADC range is approx 512)
    # Use a loop to find the actual DC offset if precise, but 512 is safe for thesis prototype
    offset = 512 

    for _ in range(num_samples):
        v_val = read_adc(1) - offset # Channel 1 is Voltage
        c_val = read_adc(0) - offset # Channel 0 is Current
        
        voltage_sum += (v_val ** 2)
        current_sum += (c_val ** 2)
        
    # Calculate RMS
    v_rms = math.sqrt(voltage_sum / num_samples) * (3.3 / 1024.0) * config.VOLTAGE_CALIBRATION
    c_rms = math.sqrt(current_sum / num_samples) * (3.3 / 1024.0) * config.CURRENT_CALIBRATION
    
    # Filtering noise
    if c_rms < 0.05: c_rms = 0.0
    
    return v_rms, c_rms

print("Starting Energy Monitor Logging...")
while True:
    try:
        voltage, current = get_rms_values()
        power = voltage * current # Apparent Power (Watts)
        
        # Data point for Database
        p = Point("energy_usage") \
            .field("voltage", voltage) \
            .field("current", current) \
            .field("power", power)
            
        write_api.write(bucket=config.INFLUX_BUCKET, record=p)
        print(f"Logged: {voltage:.1f}V | {current:.2f}A | {power:.1f}W")
        
        time.sleep(1) # Log every second
        
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f"Error: {e}")