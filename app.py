from flask import Flask, redirect, url_for, render_template, request, session
import json
from .planetmint import broadcast_tx
app = Flask(__name__)
@app.route("/broadcast", methods=["POST"])
def broadcast_tx_route():
    return broadcast_tx(
            json.loads(request.form.get("asset", "{}") or "{}"),
            json.loads(request.form.get("metadata", "{}") or "{}"),
            request.form.get("ed_public_key"),
            json.loads(request.form.get("data", "{}") or "{}"),
            json.loads(request.form.get("keys", "{}") or "{}"),
            request.form.get("script"),
    )

@app.route('/')
def index():
    return render_template('index.html')
