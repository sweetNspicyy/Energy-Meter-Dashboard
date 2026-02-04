from flask import Flask, render_template, jsonify, request
from influxdb_client import InfluxDBClient
import config
from datetime import datetime

app = Flask(__name__)
client = InfluxDBClient(url=config.INFLUX_URL, token=config.INFLUX_TOKEN, org=config.INFLUX_ORG)
query_api = client.query_api()

@app.route('/')
def home():
    # Pass current date for the "Jan - Dec" display header
    current_date = datetime.now().strftime("%B %Y") # e.g., "February 2026"
    return render_template('dashboard.html', date_display=current_date)

@app.route('/api/live')
def get_live_data():
    """Fetches the instant 'heartbeat' readings for the gauge cards."""
    query = f'from(bucket: "{config.INFLUX_BUCKET}") |> range(start: -10s) |> last()'
    tables = query_api.query(query)
    
    data = {"voltage": 0, "current": 0, "power": 0}
    for table in tables:
        for record in table.records:
            if record.get_field() in data:
                data[record.get_field()] = round(record.get_value(), 2)
    
    # Calculate instant cost projection (PHP 12/kWh)
    data["cost_hour"] = round((data["power"] / 1000) * 12.00, 2)
    return jsonify(data)

@app.route('/api/history')
def get_history_data():
    """Fetches aggregated data for the Chart and Total Usage calculations."""
    period = request.args.get('period', 'today')
    
    # Define Flux Query parameters based on toggle selection
    if period == 'today':
        range_start = "-24h"
        window_period = "1h"  # Group by Hour
    elif period == 'weekly':
        range_start = "-7d"
        window_period = "1d"  # Group by Day
    elif period == 'monthly':
        range_start = "-30d"
        window_period = "1d"  # Group by Day
    elif period == 'yearly':
        range_start = "-1y"
        window_period = "1mo" # Group by Month
    else:
        range_start = "-24h"
        window_period = "1h"

    # FLUX QUERY: Calculates average power over the window
    query = f'''
    from(bucket: "{config.INFLUX_BUCKET}")
      |> range(start: {range_start})
      |> filter(fn: (r) => r["_field"] == "power")
      |> aggregateWindow(every: {window_period}, fn: mean, createEmpty: false)
      |> yield(name: "mean")
    '''
    
    tables = query_api.query(query)
    
    labels = []
    values = []
    
    for table in tables:
        for record in table.records:
            # Format time label based on period
            dt = record.get_time()
            if period == 'today':
                label = dt.strftime("%H:%M") # 14:00
            elif period in ['weekly', 'monthly']:
                label = dt.strftime("%b %d") # Feb 03
            else:
                label = dt.strftime("%B")    # February
                
            labels.append(label)
            values.append(round(record.get_value(), 2))
            
    return jsonify({"labels": labels, "data": values})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)