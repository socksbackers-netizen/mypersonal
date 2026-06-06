import requests
from flask import Flask, request, jsonify
import base64
import json
import re

app = Flask(__name__)

# Updated working headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://resident.uidai.gov.in",
    "Referer": "https://resident.uidai.gov.in/online-aadhaar-retrieve-eid-uid",
    "X-Requested-With": "XMLHttpRequest"
}

# Session to maintain cookies
session = requests.Session()

# Get CSRF token first
def get_csrf():
    try:
        resp = session.get("https://resident.uidai.gov.in/online-aadhaar-retrieve-eid-uid", timeout=15)
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text)
        return match.group(1) if match else None
    except:
        return None

CSRF_TOKEN = get_csrf()
if CSRF_TOKEN:
    HEADERS["X-CSRF-Token"] = CSRF_TOKEN

@app.route('/')
def home():
    return "Proxy alive - UIDAI Bot"

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    name = data.get('name', '')
    mobile = data.get('mobile', '')
    
    # Updated working endpoint
    url = "https://resident.uidai.gov.in/api/request-otp"
    payload = {
        "mobileNumber": mobile,
        "type": "uid"
    }
    if name:
        payload["name"] = name
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=20)
        print(f"Send OTP Response: {r.status_code} - {r.text}")
        
        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get("status") == "success":
                return jsonify({
                    "success": True, 
                    "response": r.text,
                    "txnId": resp_data.get("txnId", "")
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("message", "Failed")})
    except Exception as e:
        print(f"Send OTP Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "All endpoints failed"})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    otp = data.get('otp')
    txn_id = data.get('tx_id', '')
    
    url = "https://resident.uidai.gov.in/api/verify-otp"
    payload = {
        "txnId": txn_id,
        "otp": otp
    }
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=20)
        print(f"Verify OTP Response: {r.status_code} - {r.text}")
        
        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get("status") == "success":
                uid = resp_data.get("eid") or resp_data.get("uid")
                return jsonify({
                    "success": True, 
                    "response": r.text,
                    "uid": uid
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("message", "Invalid OTP")})
    except Exception as e:
        print(f"Verify OTP Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Failed"})

@app.route('/send-pdf-otp', methods=['POST'])
def send_pdf_otp():
    data = request.json
    uid = data.get('uid')
    
    url = "https://resident.uidai.gov.in/api/request-pdf"
    payload = {"eid": uid}
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=20)
        print(f"Send PDF OTP Response: {r.status_code} - {r.text}")
        
        if r.status_code == 200:
            resp_data = r.json()
            if resp_data.get("status") == "success":
                return jsonify({
                    "success": True, 
                    "response": r.text,
                    "txnId": resp_data.get("txnId", "")
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("message", "Failed")})
    except Exception as e:
        print(f"Send PDF OTP Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Failed"})

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.json
    uid = data.get('uid')
    otp = data.get('otp')
    txn_id = data.get('txn_id', '')
    
    url = "https://resident.uidai.gov.in/api/download-pdf"
    payload = {"txnId": txn_id, "otp": otp}
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=30)
        print(f"Download PDF Response: {r.status_code}")
        
        if r.status_code == 200 and "application/pdf" in r.headers.get("Content-Type", ""):
            return jsonify({
                "success": True, 
                "pdf": base64.b64encode(r.content).decode()
            })
    except Exception as e:
        print(f"Download PDF Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
