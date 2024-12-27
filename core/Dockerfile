# 베이스 이미지로 Python 사용
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 필요 파일 복사
COPY requirements.txt requirements.txt
COPY main.py main.py

# 필요한 Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# AWS CLI 설치 (필요한 경우)
RUN apt-get update && apt-get install -y awscli && apt-get clean

# 실행할 스크립트 지정
CMD ["python", "main.py"]