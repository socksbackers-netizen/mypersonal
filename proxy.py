import requests
from flask import Flask, request, jsonify
import base64

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

@app.route('/')
def home():
    return "Proxy alive"

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    name = data.get('name')
    mobile = data.get('mobile')
    
    endpoints = [
        "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid",
        "https://myaadhaar.uidai.gov.in/uid-retrieval/uidsearch",
    ]
    
    for url in endpoints:
        try:
            r = requests.post(url, json={
                "name": name,
                "mobileno": mobile,
                "captcha": "",
                "retrieveType": "UID"
            }, headers=HEADERS, timeout=60)
            if r.status_code == 200 and len(r.text) > 20:
                return jsonify({"success": True, "response": r.text, "url": url})
        except:
            continue
    return jsonify({"success": False, "error": "Failed"})

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    otp = data.get('otp')
    tx_id = data.get('tx_id', '')
    
    endpoints = [
        "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/verifyRetrieveUidEidOtp",
        "https://myaadhaar.uidai.gov.in/uid-retrieval/otp-verify",
        "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid",
    ]
    
    for url in endpoints:
        try:
            r = requests.post(url, json={
                "otp": otp,
                "transactionId": tx_id,
                "verifyOTP": "Verify OTP"
            }, headers=HEADERS, timeout=60)
            if r.status_code == 200 and len(r.text) > 50:
                return jsonify({"success": True, "response": r.text, "url": url})
        except:
            continue
    return jsonify({"success": False, "error": "All verify endpoints failed"})

@app.route('/send-pdf-otp', methods=['POST'])
def send_pdf_otp():
    data = request.json
    uid = data.get('uid')
    
    for url in [
        "https://tathya.uidai.gov.in/aadhaarOtp/ext/v1/generic/sendOtp",
        "https://myaadhaar.uidai.gov.in/aadhaar-otp/request",
    ]:
        try:
            r = requests.post(url, json={"uid": uid, "otpType": "pdf"}, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return jsonify({"success": True, "response": r.text})
        except:
            continue
    return jsonify({"success": False, "error": "Failed"})

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.json
    uid = data.get('uid')
    otp = data.get('otp')
    
    for url in [
        "https://tathya.uidai.gov.in/downloadAadhaar/ext/v1/generic/downloadAadhaarPdf",
        "https://myaadhaar.uidai.gov.in/download-aadhaar/pdf",
    ]:
        try:
            r = requests.post(url, json={"uid": uid, "otp": otp}, headers=HEADERS, timeout=60)
            if r.headers.get('Content-Type') == 'application/pdf':
                return jsonify({"success": True, "pdf": base64.b64encode(r.content).decode()})
        except:
            continue
    return jsonify({"success": False, "error": "Failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
