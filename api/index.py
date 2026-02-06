from flask import Flask, render_template, jsonify, request
import random
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# --- 24-HOUR PROFILE (The "Real" Data) ---
DEMO_24H_PROFILE = [
    120, 115, 110, 110, 120, 150,  # Sleep
    450, 850, 1100, 900, 400, 350, # Morning
    300, 300, 320, 350, 400, 600,  # Afternoon
    1200, 1450, 1500, 1300, 900, 400 # Evening
]

# STRICT CEBU RATE
CURRENT_RATE = 11.60 

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/live')
def get_live_data():
    current_hour = datetime.now().hour
    base_power = DEMO_24H_PROFILE[current_hour]
    live_power = base_power + random.uniform(-15, 15)
    voltage = 220.0 + random.uniform(-1, 1)
    current = live_power / voltage
    
    return jsonify({
        "voltage": round(voltage, 1),
        "current": round(current, 2),
        "power": round(live_power, 1),
        "status": "Normal" if live_power < 2000 else "High Load"
    })

@app.route('/api/history')
def get_history_data():
    period = request.args.get('period', 'today')
    
    total_watts_today = sum(DEMO_24H_PROFILE)
    daily_kwh = total_watts_today / 1000.0
    avg_watts = total_watts_today / 24.0

    labels = []
    values = []
    summary_kwh = 0.0

    if period == 'today':
        labels = [f"{i:02d}:00" for i in range(24)]
        values = DEMO_24H_PROFILE
        summary_kwh = daily_kwh
    elif period == 'weekly':
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        values = [round(avg_watts * random.uniform(0.9, 1.1), 0) for _ in range(7)]
        summary_kwh = daily_kwh * 7
    elif period == 'monthly':
        labels = [f"Day {i}" for i in range(1, 31)]
        values = [round(avg_watts * random.uniform(0.85, 1.15), 0) for _ in range(30)]
        summary_kwh = daily_kwh * 30
    else: 
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        values = [round(avg_watts * random.uniform(0.8, 1.2), 0) for _ in range(12)]
        summary_kwh = daily_kwh * 365

    # STRICT CALCULATION WITH 11.60
    summary_cost = round(summary_kwh * CURRENT_RATE, 2)
    summary_carbon = round(summary_kwh * 0.702, 2)

    return jsonify({
        "labels": labels,
        "data": values,
        "summary": {
            "total_kwh": round(summary_kwh, 2),
            "total_cost": summary_cost,
            "total_carbon": summary_carbon
        }
    })

if __name__ == '__main__':
    app.run()