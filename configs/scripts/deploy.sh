#!/bin/bash

# Docker 설치 여부를 확인하고, 없으면 설치한다.
if ! type docker > /dev/null
then
    echo "Not exist: docker"
    echo "Start install: docker"
    sudo apt-get update
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key-add -
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
    sudo apt update
    apt-cache policy docker-ce
    sudo apt install -y docker-ce
fi

# Docker Compose 설치 여부를 확인하고, 없으면 설치한다.
if ! type docker-compose > /dev/null
then
    echo "Not exist: docker-compose"
    echo "Start install: docker-compose"
    sudo curl -L "https://github.com/docker/compose/releases/download/1.27.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Docker Compose로 서버를 빌드하고 실행한다. (docker-compose.prod.yml 사용)
echo "Start docker-compose up: ubuntu"
sudo docker-compose -f /home/ubuntu/srv/ubuntu/docker-compose.prod.yml up --build -d
