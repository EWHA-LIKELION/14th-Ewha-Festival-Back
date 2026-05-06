#!/bin/bash

# Docker 설치 여부를 확인하고, 없으면 설치한다.
if ! type docker > /dev/null
then
    echo "Not exist: docker"
    echo "Start install: docker"
    
    # 기존 Docker 저장소 제거
    sudo rm -f /etc/apt/sources.list.d/docker.list
    
    # 시스템 패키지 업데이트
    sudo apt-get update
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release
    
    # Docker GPG 키 추가
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Docker 저장소 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 패키지 리스트 업데이트
    sudo apt-get update
    
    # Docker 설치
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Docker 서비스 시작
    sudo systemctl start docker
    sudo systemctl enable docker
fi

# Docker Compose 설치 여부를 확인하고, 없으면 설치한다.
if ! type docker-compose > /dev/null
then
    echo "Not exist: docker-compose"
    echo "Start install: docker-compose"
    sudo curl -L "https://github.com/docker/compose/releases/download/1.27.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Docker Compose로 서버를 빌드하고 실행한다.
echo "Start docker-compose up: ubuntu"
sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yml up --build -d
