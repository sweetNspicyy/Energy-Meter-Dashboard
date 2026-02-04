from flask import Flask, render_template, jsonify, request
from influxdb_client import InfluxDBClient
import os
from datetime import datetime

# Initialize Flask
# We explicitly tell it where the 'templates' folder is
app = Flask(__name__, template_folder='../templates')

# --- Cloud Configuration ---
# These are pulled from Vercel Environment Variables
INFLUX_URL = os.environ.get("INFLUX_URL")
INFLUX_TOKEN = os.environ.get("INFLUX_TOKEN")
INFLUX_ORG = os.environ.get("INFLUX_ORG")
INFLUX_BUCKET = os.environ.get("INFLUX_BUCKET")

# Initialize Database Client
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
except:
    print("Warning: Database credentials not found. Ensure Environment Variables are set.")

# --- Routes ---

@app.route('/')
def home():
    """Renders the main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/live')
def get_live_data():
    """API: Gets the single most recent data point for the gauges."""
    if not INFLUX_URL: return jsonify({"error": "Database not configured"})

    # Query: Get the last recorded value within the last 5 minutes
    query = f'from(bucket: "{INFLUX_BUCKET}") |> range(start: -5m) |> last()'
    
    try:
        tables = query_api.query(query)
        data = {"voltage": 0, "current": 0, "power": 0}
        
        for table in tables:
            for record in table.records:
                # Matches the field name ("voltage", "current", etc.) to the value
                if record.get_field() in data:
                    data[record.get_field()] = round(record.get_value(), 2)
        
        # Calculate Estimated Cost (PHP 12 per kWh as an example)
        # Power (W) / 1000 = kW * 12 Pesos
        data["cost_hour"] = round((data["power"] / 1000.0) * 12.00, 2)
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e), "voltage": 0, "current": 0, "power": 0, "cost_hour": 0})

@app.route('/api/history')
def get_history_data():
    """API: Gets aggregated data for the chart."""
    if not INFLUX_URL: return jsonify({"error": "Database not configured"})

    period = request.args.get('period', 'today')
    
    # Determine Time Range and Aggregation Window
    if period == 'today':
        range_start = "-24h"
        window_period = "1h"  # Average every hour
    elif period == 'weekly':
        range_start = "-7d"
        window_period = "1d"  # Average every day
    elif period == 'monthly':
        range_start = "-30d"
        window_period = "1d"  # Average every day
    elif period == 'yearly':
        range_start = "-1y"
        window_period = "1mo" # Average every month
    else:
        # Default
        range_start = "-24h"
        window_period = "1h"

    # Flux Query: Filter for 'power' and calculate the mean (average)
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: {range_start})
      |> filter(fn: (r) => r["_field"] == "power")
      |> aggregateWindow(every: {window_period}, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''
    
    try:
        tables = query_api.query(query)
        labels = []
        values = []
        
        for table in tables:
            for record in table.records:
                dt = record.get_time()
                # Format Date Label based on view
                if period == 'today':
                    label = dt.strftime("%H:%M") # Hour:Minute
                elif period in ['weekly', 'monthly']:
                    label = dt.strftime("%b %d") # Month Day
                else:
                    label = dt.strftime("%B")    # Month Name
                    
                labels.append(label)
                values.append(round(record.get_value(), 2))
                
        return jsonify({"labels": labels, "data": values})
    except Exception as e:
         return jsonify({"error": str(e), "labels": [], "data": []})

# Required for Vercel Serverless Function
if __name__ == '__main__':
    app.run()