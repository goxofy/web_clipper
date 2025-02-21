#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}开始部署 Web Clipper 服务...${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker 未安装，开始安装 Docker...${NC}"
    curl -fsSL https://get.docker.com | sh
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Docker Compose 未安装，开始安装 Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 检查配置文件
if [ ! -f config.py ]; then
    echo -e "${YELLOW}未检测到 config.py，将复制示例配置文件...${NC}"
    cp config.example.py config.py
    echo -e "${YELLOW}请编辑 config.py 填写正确的配置信息${NC}"
    exit 1
fi

# 检查并删除旧容器和镜像
echo -e "${YELLOW}检查旧的容器和镜像...${NC}"

# 停止并删除旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^web-clipper$"; then
    echo -e "${YELLOW}发现旧容器，正在停止...${NC}"
    docker stop web-clipper || true
    echo -e "${YELLOW}正在删除旧容器...${NC}"
    docker rm web-clipper || true
fi

# 查找并删除旧镜像
OLD_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "web-clipper")
if [ ! -z "$OLD_IMAGE" ]; then
    echo -e "${YELLOW}发现旧镜像: ${OLD_IMAGE}，正在删除...${NC}"
    docker rmi $OLD_IMAGE || true
fi

# 清理可能存在的悬空镜像（dangling images）
DANGLING_IMAGES=$(docker images -f "dangling=true" -q)
if [ ! -z "$DANGLING_IMAGES" ]; then
    echo -e "${YELLOW}清理悬空镜像...${NC}"
    docker rmi $DANGLING_IMAGES || true
fi

# 构建镜像
echo -e "${GREEN}开始构建 Docker 镜像...${NC}"
docker-compose build

# 启动服务
echo -e "${GREEN}开始启动服务...${NC}"
docker-compose up -d --build

# 检查服务状态
if [ $? -eq 0 ]; then
    echo -e "${GREEN}服务启动成功！${NC}"
    echo -e "可以使用以下命令查看日志：\n${YELLOW}docker-compose logs -f${NC}"
else
    echo -e "${YELLOW}服务启动失败，请检查日志${NC}"
fi