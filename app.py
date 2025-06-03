from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route("/")
def index():
    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
    az = os.getenv("TASK_AZ", "AZ unknown")
    return render_template("index.html", lorem=lorem, az=az)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
