from flask import Flask, render_template, request, g
import os
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNTER = Counter(
    "http_requests_total", "Total HTTP Requests",
    ["method", "endpoint", "status_code"]
)

@app.before_request
def start_timer():
    g.request_start = request.path  # for now, just pass through

@app.after_request
def record_request_data(response):
    REQUEST_COUNTER.labels(
        method=request.method,
        endpoint=request.path,
        status_code=response.status_code
    ).inc()
    return response

@app.route("/")
def index():
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    az = os.getenv("TASK_AZ", "AZ unknown")
    return render_template("index.html", lorem=lorem, az=az)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
