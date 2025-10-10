import os
import json
import requests
from datetime import datetime, timezone, timedelta

# --- 사용자 설정 ---
ISSUE_LOG_ID = 1      # 데이터를 기록할 GitHub Issue의 번호
TEMP_THRESHOLD = 30.0 # 온도 위험 임계치
# ------------------

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_NAME = os.getenv('GITHUB_REPOSITORY') 
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
BASE_URL = f"https://api.github.com/repos/{REPO_NAME}"
KST = timezone(timedelta(hours=9))

def post_comment(issue_number, comment_body):
    url = f"{BASE_URL}/issues/{issue_number}/comments"
    requests.post(url, headers=HEADERS, json={"body": comment_body})

def create_alert_issue(title, body, labels):
    url = f"{BASE_URL}/issues"
    requests.post(url, headers=HEADERS, json={"title": title, "body": body, "labels": labels})

def main():
    sensor_payload = os.getenv('SENSOR_DATA')
    if not sensor_payload: return

    data = json.loads(sensor_payload)
    temp, conc = data.get("temperature"), data.get("concentration")
    now_kst_str = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

    post_comment(ISSUE_LOG_ID, f"🌡️ **온도**: `{temp}`°C | 💧 **농도**: `{conc}`µS/cm (백업 시각: {now_kst_str})")

    try:
        with open('data.json', 'r', encoding='utf-8') as f: all_data = json.load(f)
    except: all_data = []
    
    all_data.append({"time": now_kst_str, "temp": temp, "conc": conc})
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data[-100:], f, indent=2, ensure_ascii=False)
    
    if temp > TEMP_THRESHOLD:
        create_alert_issue(f"🚨 [온도 경보] 임계치 초과: {temp}°C", f"위험 수준의 온도(`{temp}`°C)가 감지되었습니다.\n- 확인 시각: {now_kst_str}", ["alert", "temperature"])

if __name__ == "__main__":
    main()
