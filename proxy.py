import requests
from flask import Flask, request, jsonify
import base64
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
    "Content-Type": "application/json",
    "Origin": "https://myaadhaar.uidai.gov.in",
    "Referer": "https://myaadhaar.uidai.gov.in/",
    "Connection": "keep-alive",
}

@app.route('/')
def home():
    return "Proxy alive"

@app.route('/send-otp', methods=['POST'])
def send_otp():
    data = request.json
    name = data.get('name')
    mobile = data.get('mobile')
    
    app.logger.info(f"Sending OTP for: {name}, {mobile}")
    
    # Multiple endpoints try karo
    endpoints = [
        {
            "url": "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid",
            "data": {
                "name": name,
                "mobileno": mobile,
                "captcha": "",
                "captchaId": "",
                "retrieveType": "UID"
            }
        },
        {
            "url": "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid",
            "data": {
                "name": name,
                "mobileno": mobile,
                "retrieveType": "UID"
            }
        },
        {
            "url": "https://myaadhaar.uidai.gov.in/uid-retrieval/uidsearch",
            "data": {
                "name": name,
                "mobileno": mobile,
                "retrieveType": "uid"
            }
        },
        {
            "url": "https://tathya.uidai.gov.in/residentOtp/ext/v1/generic/sendOtp",
            "data": {
                "mobileNo": mobile,
                "name": name,
                "type": "LOST_UID"
            }
        },
        {
            "url": "https://myaadhaar.uidai.gov.in/api/uid-retrieval/send-otp",
            "data": {
                "name": name,
                "mobile": mobile,
                "retrieveType": "UID"
            }
        }
    ]
    
    session = requests.Session()
    
    for i, ep in enumerate(endpoints):
        try:
            app.logger.info(f"Trying endpoint {i+1}: {ep['url']}")
            r = session.post(ep["url"], json=ep["data"], headers=HEADERS, timeout=60)
            app.logger.info(f"Response {r.status_code}: {r.text[:200]}")
            
            if r.status_code == 200 and len(r.text) > 20:
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "url": ep["url"],
                    "status": r.status_code
                })
            
            # 400/401 bhi bhejo debug ke liye
            if r.status_code in [400, 401, 403, 422]:
                return jsonify({
                    "success": False,
                    "response": r.text,
                    "url": ep["url"],
                    "status": r.status_code,
                    "error": f"HTTP {r.status_code}"
                })
                
        except requests.exceptions.Timeout:
            app.logger.error(f"Timeout for {ep['url']}")
            continue
        except requests.exceptions.ConnectionError:
            app.logger.error(f"Connection error for {ep['url']}")
            continue
        except Exception as e:
            app.logger.error(f"Error for {ep['url']}: {str(e)}")
            continue
    
    return jsonify({
        "success": False,
        "error": "All endpoints failed",
        "status": 0
    })

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    otp = data.get('otp')
    tx_id = data.get('tx_id', '')
    
    app.logger.info(f"Verifying OTP: {otp}, tx_id: {tx_id}")
    
    endpoints = [
        {
            "url": "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/verifyRetrieveUidEidOtp",
            "data": {
                "otp": otp,
                "transactionId": tx_id
            }
        },
        {
            "url": "https://myaadhaar.uidai.gov.in/uid-retrieval/otp-verify",
            "data": {
                "otp": otp,
                "transactionId": tx_id
            }
        },
        {
            "url": "https://tathya.uidai.gov.in/retrieveEidUid/ext/v1/generic/retrieveuideid",
            "data": {
                "otp": otp,
                "transactionId": tx_id,
                "verifyOTP": "Verify OTP"
            }
        }
    ]
    
    for i, ep in enumerate(endpoints):
        try:
            app.logger.info(f"Trying verify endpoint {i+1}: {ep['url']}")
            r = requests.post(ep["url"], json=ep["data"], headers=HEADERS, timeout=60)
            app.logger.info(f"Verify response {r.status_code}: {r.text[:200]}")
            
            if r.status_code == 200 and len(r.text) > 50:
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "url": ep["url"]
                })
        except Exception as e:
            app.logger.error(f"Verify error: {str(e)}")
            continue
    
    return jsonify({
        "success": False,
        "error": "All verify endpoints failed"
    })

@app.route('/send-pdf-otp', methods=['POST'])
def send_pdf_otp():
    data = request.json
    uid = data.get('uid')
    
    app.logger.info(f"Sending PDF OTP for UID: {uid}")
    
    endpoints = [
        {
            "url": "https://tathya.uidai.gov.in/aadhaarOtp/ext/v1/generic/sendOtp",
            "data": {"uid": uid, "otpType": "pdf"}
        },
        {
            "url": "https://myaadhaar.uidai.gov.in/aadhaar-otp/request",
            "data": {"uid": uid, "otpType": "pdf"}
        },
        {
            "url": "https://tathya.uidai.gov.in/aadhaarOtp/ext/v1/generic/sendOtp",
            "data": {"uid": uid}
        }
    ]
    
    for ep in endpoints:
        try:
            r = requests.post(ep["url"], json=ep["data"], headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return jsonify({
                    "success": True,
                    "response": r.text,
                    "url": ep["url"]
                })
        except:
            continue
    
    return jsonify({"success": False, "error": "PDF OTP failed"})

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    data = request.json
    uid = data.get('uid')
    otp = data.get('otp')
    
    app.logger.info(f"Downloading PDF for UID: {uid}")
    
    endpoints = [
        {
            "url": "https://tathya.uidai.gov.in/downloadAadhaar/ext/v1/generic/downloadAadhaarPdf",
            "data": {"uid": uid, "otp": otp, "downloadType": "pdf"}
        },
        {
            "url": "https://myaadhaar.uidai.gov.in/download-aadhaar/pdf",
            "data": {"uid": uid, "otp": otp}
        }
    ]
    
    for ep in endpoints:
        try:
            r = requests.post(ep["url"], json=ep["data"], headers=HEADERS, timeout=90)
            
            if r.headers.get('Content-Type') == 'application/pdf':
                return jsonify({
                    "success": True,
                    "pdf": base64.b64encode(r.content).decode()
                })
            
            # Check JSON response for base64 PDF
            try:
                resp = r.json()
                if resp.get("pdfData"):
                    return jsonify({
                        "success": True,
                        "pdf": resp["pdfData"]
                    })
                if resp.get("pdfBase64"):
                    return jsonify({
                        "success": True,
                        "pdf": resp["pdfBase64"]
                    })
            except:
                pass
                
        except Exception as e:
            app.logger.error(f"PDF error: {str(e)}")
            continue
    
    return jsonify({"success": False, "error": "PDF download failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
