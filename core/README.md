# chameleon

route53_records.py 는 하루에 1회 스케줄링 됩니다. 
- aws cli 로 route53 의 records 와 ip 를 가져와, route53_records.json 에 저장합니다. 

main.py
- 30초에 1회 외부 ip 를 체크합니다. 
- 만약 ip 가 변경되었다면, route53_records.json 으로, 기존 IP에 연결된 record의 IP를 변경된 IP로 업데이트합니다.
- 최종적으로, Domain 이 유동아이피의 서버와 연결됩니다. 