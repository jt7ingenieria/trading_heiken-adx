from flask import Flask, render_template, jsonify
import pandas as pd
import os

app = Flask(__name__)

RESULTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'optimization_results.csv')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/results')
def get_results():
    if os.path.exists(RESULTS_FILE):
        df = pd.read_csv(RESULTS_FILE)
        return jsonify(df.to_dict(orient='records'))
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
