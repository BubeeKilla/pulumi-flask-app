import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    az = os.getenv("TASK_AZ", "AZ unknown")
    return f"<p>{lorem}</p><p><b>Running in AZ:</b> {az}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
