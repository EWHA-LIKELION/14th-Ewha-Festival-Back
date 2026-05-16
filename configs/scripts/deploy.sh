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
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# -------------------------------------------------------
# Blue/Green 무중단 배포
# -------------------------------------------------------
WORKDIR=/home/ubuntu/srv/ubuntu
COMPOSE="sudo docker-compose -f $WORKDIR/docker-compose.prod.yml"

# 현재 어느 쪽이 떠 있는지 판별
BLUE_RUNNING=$(sudo docker ps --format '{{.Names}}' | grep -w web_blue || true)
GREEN_RUNNING=$(sudo docker ps --format '{{.Names}}' | grep -w web_green || true)

# 최초 배포 (아무것도 안 떠 있음)
if [ -z "$BLUE_RUNNING" ] && [ -z "$GREEN_RUNNING" ]; then
    echo "▶ 최초 배포: web_blue + nginx 시작"
    $COMPOSE up -d --build web_blue nginx
    echo "✅ 최초 배포 완료 — web_blue 서비스 중"
    exit 0
fi

# active/next 결정
if [ -n "$BLUE_RUNNING" ]; then
    NEXT_CONTAINER="web_green"
    NEXT_PORT="8000"
    NEXT_SERVER="web_green:8000"
    OLD_CONTAINER="web_blue"
else
    NEXT_CONTAINER="web_blue"
    NEXT_PORT="8000"
    NEXT_SERVER="web_blue:8000"
    OLD_CONTAINER="web_green"
fi

echo "▶ 전환: $OLD_CONTAINER → $NEXT_CONTAINER"

# 1. 새 컨테이너 빌드 및 시작
$COMPOSE rm -f $NEXT_CONTAINER
$COMPOSE up -d --build $NEXT_CONTAINER

# 2. 헬스체크 (최대 45초 대기)
echo "▶ 헬스체크 시작..."
for i in $(seq 1 15); do
    if sudo docker exec $NEXT_CONTAINER curl -sf http://localhost:$NEXT_PORT/health/ > /dev/null 2>&1; then
        echo "✅ 헬스체크 통과"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ 헬스체크 실패 — $NEXT_CONTAINER 종료, 기존 유지"
        $COMPOSE stop $NEXT_CONTAINER
        exit 1
    fi
    echo "   대기 중... ($i/15)"
    sleep 3
done

# 3. nginx upstream 전환
echo "▶ nginx upstream → $NEXT_SERVER"
sudo docker exec nginx sed -i \
    "s|server web_.*:.*;|server $NEXT_SERVER;|" \
    /etc/nginx/conf.d/default.conf

# 4. nginx 무중단 reload
sudo docker exec nginx nginx -s reload
echo "▶ nginx reload 완료"

# 5. 구 컨테이너 종료
echo "▶ $OLD_CONTAINER 종료"
$COMPOSE stop $OLD_CONTAINER

echo "✅ 배포 완료 — $NEXT_CONTAINER 서비스 중"
