from flask import Flask, render_template, jsonify, request
import subprocess
from datetime import datetime

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("dashboard.html")

