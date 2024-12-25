import time
import requests
import boto3
import logging

# AWS 설정
HOSTED_ZONE_ID = "YOUR_HOSTED_ZONE_ID"  # Route 53 호스팅 영역 ID
DOMAIN_NAME = "yourdomain.com"  # 갱신할 도메인 이름

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

# Route 53에서 도메인의 A 레코드를 업데이트
def update_route53(ip_address):
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
                            "Name": DOMAIN_NAME,
                            "Type": "A",
                            "TTL": 60,
                            "ResourceRecords": [{"Value": ip_address}],
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
    current_ip = None
    while True:
        logging.info("Checking external IP...")
        new_ip = get_external_ip()
        if new_ip and new_ip != current_ip:
            logging.info(f"External IP changed: {new_ip}")
            update_route53(new_ip)
            current_ip = new_ip
        else:
            logging.info(f"No change in IP. Current IP: {current_ip}")
        time.sleep(30)  # 30초마다 확인

if __name__ == "__main__":
    monitor_and_update_ip()
