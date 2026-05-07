#!/bin/bash

# 실행 중인 모든 컨테이너 중지
echo "Stopping all containers..."
sudo docker stop $(sudo docker ps -aq) 2>/dev/null || true

# 모든 컨테이너 삭제
echo "Removing all containers..."
sudo docker rm $(sudo docker ps -aq) 2>/dev/null || true

# 사용되지 않는 볼륨 삭제
echo "Removing unused volumes..."
sudo docker volume prune -f

# 사용되지 않는 이미지 삭제
echo "Removing unused images..."
sudo docker image prune -a -f

# 이전에 생성한 프로젝트 디렉토리 삭제
echo "Removing old project directory..."
sudo rm -rf /home/ubuntu/srv/ubuntu

# 정리 완료
echo "Cleanup completed!"
sudo docker ps -a
sudo docker images
