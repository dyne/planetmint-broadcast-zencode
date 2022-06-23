from flask import Flask, redirect, url_for, render_template, request, session
import json
from .planetmint import broadcast_tx
app = Flask(__name__)
@app.route("/broadcast", methods=["POST"])
def broadcast_tx_route():
    if not request.form.get("ed_public_key"):
        return {"success": False, "error": "Missing EdDSA public key"}
    try:
        return broadcast_tx(
                json.loads(request.form.get("asset", "{}") or "{}"),
                json.loads(request.form.get("metadata", "{}") or "{}"),
                request.form.get("ed_public_key"),
                json.loads(request.form.get("data", "{}") or "{}"),
                json.loads(request.form.get("keys", "{}") or "{}"),
                request.form.get("script"),
        )
    except Exception as e:
        return {"success": False,
                "error": "{}: {}".format(type(e),
                                         str(e))}

@app.route('/')
def index():
    return render_template('index.html')
