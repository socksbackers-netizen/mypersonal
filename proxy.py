import requests
from flask import Flask, request, jsonify
import base64
import json
import re
import uuid

app = Flask(__name__)

# Create session with proper cookies
session = requests.Session()

# First get cookies and CSRF token from main page
def init_session():
    try:
        resp = session.get("https://tathya.uidai.gov.in/retrieveEidUid/en/", timeout=20)
        # Extract CSRF token
        csrf_match = re.search(r'name="csrfToken"\s+value="([^"]+)"', resp.text)
        if not csrf_match:
            csrf_match = re.search(r'csrfToken["\']?\s*:\s*["\']([^"\']+)', resp.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        # Extract transaction ID
        txn_match = re.search(r'transactionId["\']?\s*:\s*["\']([^"\']+)', resp.text)
        txn_id = txn_match.group(1) if txn_match else str(uuid.uuid4())
        
        return csrf_token, txn_id
    except Exception as e:
        print(f"Init error: {e}")
        return None, str(uuid.uuid4())

CSRF_TOKEN, TXN_ID = init_session()
print(f"CSRF: {CSRF_TOKEN}, TXN: {TXN_ID}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://tathya.uidai.gov.in",
    "Referer": "https://tathya.uidai.gov.in/retrieveEidUid/en/",
    "X-Requested-With": "XMLHttpRequest",
    "appID": "MYAADHAAR"
}
if CSRF_TOKEN:
    HEADERS["X-CSRF-TOKEN"] = CSRF_TOKEN

@app.route('/')
def home():
    return "Proxy alive - Tathya UIDAI Bot"

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    name = data.get('name', '')
    mobile = data.get('mobile', '')
    
    url = "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid"
    payload = {
        "mobileNumber": mobile,
        "skipName": not bool(name),
        "skipDOB": True,
        "transactionId": TXN_ID
    }
    if name:
        payload["name"] = name
        payload["skipName"] = False
    
    try:
        print(f"Sending payload: {payload}")
        r = session.post(url, json=payload, headers=HEADERS, timeout=25)
        print(f"Send OTP Response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code == 200:
            resp_data = r.json()
            # Check for success (OTP sent)
            if "errorCode" not in resp_data:
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "txnId": resp_data.get("transactionId", TXN_ID)
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("errorDetails", {}).get("messageEnglish", "Failed")})
    except Exception as e:
        print(f"Send OTP Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "All endpoints failed"})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    otp = data.get('otp')
    tx_id = data.get('tx_id', TXN_ID)
    
    url = "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/validateOtp"
    payload = {
        "otp": otp,
        "transactionId": tx_id
    }
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=20)
        print(f"Verify OTP Response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code == 200:
            resp_data = r.json()
            if "errorCode" not in resp_data:
                # Extract UID/EID
                uid = resp_data.get("eid") or resp_data.get("uid")
                if not uid:
                    match = re.search(r'(\d{12}|\d{16}|\d{28})', r.text)
                    if match:
                        uid = match.group(1)
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "uid": uid
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("errorDetails", {}).get("messageEnglish", "Invalid OTP")})
    except Exception as e:
        print(f"Verify OTP Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Failed"})

@app.route('/send-pdf-otp', methods=['POST'])
def send_pdf_otp():
    data = request.json
    uid = data.get('uid')
    
    url = "https://tathya.uidai.gov.in/aadhaarPdf/ext/v1/generic/downloadRequest"
    payload = {"eid": uid}
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=20)
        print(f"Send PDF OTP Response: {r.status_code} - {r.text[:200]}")
        
        if r.status_code == 200:
            resp_data = r.json()
            if "errorCode" not in resp_data:
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "txnId": resp_data.get("requestId", str(uuid.uuid4()))
                })
            else:
                return jsonify({"success": False, "error": resp_data.get("errorDetails", {}).get("messageEnglish", "Failed")})
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
    
    url = "https://tathya.uidai.gov.in/aadhaarPdf/ext/v1/generic/confirmDownload"
    payload = {
        "eid": uid,
        "otp": otp,
        "requestId": txn_id
    }
    
    try:
        r = session.post(url, json=payload, headers=HEADERS, timeout=30)
        print(f"Download PDF Response: {r.status_code}")
        
        if r.status_code == 200:
            resp_data = r.json()
            pdf_url = resp_data.get("pdfUrl")
            if pdf_url:
                pdf_resp = requests.get(pdf_url, timeout=30)
                if pdf_resp.status_code == 200:
                    return jsonify({
                        "success": True,
                        "pdf": base64.b64encode(pdf_resp.content).decode()
                    })
    except Exception as e:
        print(f"Download PDF Error: {e}")
        return jsonify({"success": False, "error": str(e)})
    
    return jsonify({"success": False, "error": "Failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
