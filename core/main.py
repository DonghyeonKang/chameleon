import os
import time
import requests
import boto3
import logging
import json
import schedule
import threading

# AWS 설정
HOSTED_ZONE_ID = "Z02685223HMS83GDKQP0U"  # secure.env에서 가져옴

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

# 외부 IP를 확인하는 함수
def get_external_ip():
    try:
        response = requests.get("https://api64.ipify.org?format=json")
        response.raise_for_status()
        return response.json().get("ip")
    except requests.RequestException as e:
        logging.error(f"Failed to get external IP: {e}")
        return None

# 도메인 리스트 가져오기
def get_domain_names_by_ip(ip_address, file_path="./core/route53_records.json"):
    # JSON 파일이 없으면 생성
    if not os.path.exists(file_path):
        logging.warning(f"File {file_path} not found. Creating a new file with Route 53 records...")
        all_records = get_records_name_and_ip()
        with open(file_path, "w") as file:
            json.dump(all_records, file, indent=4)  # Route 53 레코드 저장
        logging.info(f"File {file_path} has been created with Route 53 records.")
    
    try:
        # JSON 파일 열기
        with open(file_path, "r") as file:
            records = json.load(file)
        
        # 주어진 IP 주소와 매칭되는 모든 RecordName 수집
        matching_record_names = []
        for record in records:
            print(ip_address)
            print(record.get("IP", []))
            if ip_address in record.get("IP", []):  # "IP" 리스트에서 IP 주소 검색
                matching_record_names.append(record.get("RecordName"))
        
        print(matching_record_names)
        return matching_record_names  # 리스트 반환
    except json.JSONDecodeError:
        logging.error("Invalid JSON format.")
        return []

# Route 53에서 도메인의 A 레코드를 업데이트
def update_route53(new_ip, domainName):
    try:
        client = boto3.client("route53")
        response = client.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                "Comment": "Updating public IP",
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": domainName,
                            "Type": "A",
                            "TTL": 60,
                            "ResourceRecords": [{"Value": new_ip}],
                        },
                    }
                ],
            },
        )
        logging.info(f"Updated Route 53 record: {response}")
    except Exception as e:
        logging.error(f"Failed to update Route 53 record: {e}")

# 메인 로직
def monitor_and_update_ip():
    current_ip = get_external_ip()

    # 무한 루프
    while True:
        logging.info("Checking external IP...")
        new_ip = get_external_ip()

        # IP가 변경되었을 때 로직
        if new_ip and new_ip != current_ip:
            logging.info(f"External IP changed: {new_ip}")
            
            # 이전 IP와 연결된 도메인 리스트 가져오기
            domainList = get_domain_names_by_ip(current_ip)

            # 도메인의 IP 변경
            for domainName in domainList:
                update_route53(new_ip, domainName)

            # IP 갱신
            current_ip = new_ip
        else:
            logging.info(f"No change in IP. Current IP: {current_ip}")
        time.sleep(30)  # 30초마다 확인

# AWS Route 53 클라이언트 생성
client = boto3.client('route53')

def get_records_name_and_ip():
    # 모든 레코드의 RecordName과 IP를 가져오는 함수
    hosted_zones = client.list_hosted_zones()['HostedZones']
    result = []

    for zone in hosted_zones:
        zone_id = zone['Id'].split('/')[-1]  # Hosted Zone ID 추출

        # 해당 호스팅 영역의 레코드 가져오기
        records = client.list_resource_record_sets(HostedZoneId=zone_id)['ResourceRecordSets']
        
        for record in records:
            # IP 주소 또는 레코드 값이 존재할 경우에만 추가
            if 'ResourceRecords' in record:
                result.append({
                    "RecordName": record['Name'],
                    "IP": [r['Value'] for r in record['ResourceRecords']]
                })

    return result

def save_records_to_json():
    # 모든 레코드와 IP 가져오기
    all_records = get_records_name_and_ip()
    
    # JSON 파일로 저장
    with open("./core/route53_records.json", "w") as f:
        json.dump(all_records, f, indent=4)
    
    logging.info("Route 53 records saved to 'route53_records.json'")

def schedule_save_records():
    # 스케줄링: 매 시간마다 실행
    schedule.every(1).hours.do(save_records_to_json)

    # 스케줄 유지
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    # 두 개의 작업을 스레드로 실행
    thread1 = threading.Thread(target=monitor_and_update_ip)
    thread2 = threading.Thread(target=schedule_save_records)

    thread1.start()
    thread2.start()

    # 스레드가 종료되지 않도록 대기
    thread1.join()
    thread2.join()
