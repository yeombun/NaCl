import os
import json
import requests
from datetime import datetime, timezone, timedelta

# --- 사용자 설정 ---
ISSUE_LOG_ID = 1      # 데이터를 기록할 GitHub Issue의 번호
TEMP_THRESHOLD = 22.0 # 온도 위험 임계치
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
    now_kst = datetime.now(KST)
    now_kst_str = now_kst.strftime('%Y-%m-%d %H:%M:%S')

    # --- 데이터 저장 방식 변경 ---
    # 1. 'data' 폴더가 없으면 생성
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 2. 오늘 날짜로 파일 이름 지정 (예: log-2025-10-10.json)
    log_filename = f"{data_dir}/log-{now_kst.strftime('%Y-%m-%d')}.json"

    # 3. 기존에 오늘 날짜 파일이 있으면 읽어오고, 없으면 새로 시작
    try:
        with open(log_filename, 'r', encoding='utf-8') as f:
            daily_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        daily_data = []
    
    # 4. 새로운 데이터를 추가하고 파일에 다시 저장
    daily_data.append({"time": now_kst_str, "temp": temp, "conc": conc})
    with open(log_filename, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {log_filename} 파일에 데이터 저장 완료")
    
    # 알림 및 로그 기능은 그대로 유지
    post_comment(ISSUE_LOG_ID, f"🌡️ **온도**: `{temp}`°C | 💧 **농도**: `{conc}`% (백업 시각: {now_kst_str})")
    
    if temp > TEMP_THRESHOLD:
        create_alert_issue(f"🚨 [온도 경보] 임계치 초과: {temp}°C", f"위험 수준의 온도(`{temp}`°C)가 감지되었습니다.\n- 확인 시각: {now_kst_str}", ["alert", "temperature"])

if __name__ == "__main__":
    main()
