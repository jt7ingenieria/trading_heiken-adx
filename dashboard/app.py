import json
from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

OPTIMIZATION_RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'optimization_results.csv')
BACKTEST_RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'backtest_results.json')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/optimization_results')
def get_optimization_results():
    if os.path.exists(OPTIMIZATION_RESULTS_FILE):
        df = pd.read_csv(OPTIMIZATION_RESULTS_FILE)
        return jsonify(df.to_dict(orient='records'))
    return jsonify([])

@app.route('/api/backtest_results')
def get_backtest_results():
    if os.path.exists(BACKTEST_RESULTS_FILE):
        with open(BACKTEST_RESULTS_FILE, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify({})

if __name__ == '__main__':
    app.run(debug=True)
