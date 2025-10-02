#!/bin/bash
# -*- coding: utf-8 -*-
# 豆包AI聊天程序一键启动脚本

# 网络连接检测函数
check_network() {
    echo "Checking network connection..."
    
    # 检查网卡是否已初始化
    if ! ip link show | grep -q "state UP"; then
        echo "Network card not initialized, waiting for network to be ready..."
        return 1
    fi
    
    # 检查是否有IP地址
    if ! ip addr show | grep -q "inet "; then
        echo "no ip address, waiting for network to be ready..."
        return 1
    fi
    
    # 尝试ping测试网络连通性
    if ping -c 1 -W 3 ark.cn-beijing.volces.com >/dev/null 2>&1; then
        echo "Network connection is ready"
        return 0
    else
        echo "Network connection test failed, waiting for network to be ready..."
        return 1
    fi
}

# 等待网络就绪
wait_for_network() {
    local max_attempts=60  # 最多等待60次，每次1秒，总共60秒
    local attempt=0
    
    echo "Waiting for network connection to be ready..."
    echo -n "Timeout: ["
    
    # 创建进度条背景
    for i in $(seq 1 50); do
        echo -n "="
    done
    echo -n "] 60s"
    
    while [ $attempt -lt $max_attempts ]; do
        if check_network >/dev/null 2>&1; then
            echo -e "\rNetwork connection is ready, starting program..."
            return 0
        fi
        
        attempt=$((attempt + 1))
        local remaining=$((max_attempts - attempt))
        local filled=$((attempt * 50 / max_attempts))
        
        # 更新倒计时进度条
        echo -ne "\rTimeout: ["
        for i in $(seq 1 50); do
            if [ $i -le $filled ]; then
                echo -n " "
            else
                echo -n "="
            fi
        done
        echo -n "] ${remaining}s"
        
        sleep 1
    done
    
    echo -e "\rNetwork connection timeout, please check the network settings and try again"
    echo "You can manually check the network connection and run this script again"
    read -p "Press Enter to exit..."
    exit 1
}

# 等待网络就绪
wait_for_network

# 创建临时执行脚本
TEMP_SCRIPT=$(mktemp)

cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash
echo "⚡通电!激活环境..."
source ~/projects/doubaochat/doubao/bin/activate

echo "( ^•ﻌ•^ ) 开始大胆发言!!!"
cd ~/projects/doubaochat
python main.py

echo "程序已退出,按Enter键关闭...您可以随时通过输入doubao再次启动我"
read
EOF

# 设置临时脚本的执行权限
chmod +x "$TEMP_SCRIPT"

# 启动fbterm并执行临时脚本，使用bash明确执行
fbterm bash "$TEMP_SCRIPT"

# 清理临时脚本
rm -f "$TEMP_SCRIPT"
