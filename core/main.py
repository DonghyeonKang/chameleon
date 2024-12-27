import os
import time
import requests
import boto3
import logging
import json

# AWS 설정
HOSTED_ZONE_ID = "ap-northeast-2"  # secure.env에서 가져옴

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
def get_domain_names_by_ip(ip_address, file_path="route53_records.json"):
    try:
        # JSON 파일 열기
        with open(file_path, "r") as file:
            records = json.load(file)
        
        # 주어진 IP 주소와 매칭되는 모든 RecordName 수집
        matching_record_names = []
        for record in records:
            if ip_address in record.get("IP", []):  # "IP" 리스트에서 IP 주소 검색
                matching_record_names.append(record.get("RecordName"))
        
        return matching_record_names  # 리스트 반환
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON format.")
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

        # ip 변경되면 로직 
        if new_ip and new_ip != current_ip:
            logging.info(f"External IP changed: {new_ip}")
            
            # 이전 IP 와 연결된 도메인 리스트 가져오기
            domainList = get_domain_names_by_ip(current_ip)            

            # 도메인의 IP 변경
            for domainName in domainList:
                update_route53(new_ip, domainName)

            # IP 변환
            current_ip = new_ip
        else:
            logging.info(f"No change in IP. Current IP: {current_ip}")
        time.sleep(30)  # 30초마다 확인

if __name__ == "__main__":
    monitor_and_update_ip()
