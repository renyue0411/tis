#!/bin/bash

# ===== 可配置参数 =====
ROUNDS=50
TIMEOUT=15
SERVER_USER=server
SERVER_IP=10.1.0.1
SERVER_BIN=/home/server/Desktop/MPQUICFileTransfer/file-transfer/server
CLIENT_BIN=./client/client-multipath
SLEEP_BEFORE_CLIENT=1

SERVER_PASS="admin@123"

echo "Remote experiment start (password-based SSH)"
echo "Server: $SERVER_USER@$SERVER_IP"
echo "Rounds: $ROUNDS"
echo "--------------------------------------------"

for ((i=1; i<=ROUNDS; i++))
do
    echo "[Round $i] Starting server on remote host..."

    # 启动 server（远程后台）
    sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no \
        $SERVER_USER@$SERVER_IP \
        "nohup $SERVER_BIN > server_$i.log 2>&1 & echo \$! > server.pid"

    sleep $SLEEP_BEFORE_CLIENT

    echo "[Round $i] Starting client locally..."

    EXP_ROUND=$i $CLIENT_BIN &
    CLIENT_PID=$!

    START_TIME=$(date +%s)

    while true
    do
        sleep 1

        # client 正常结束
        if ! kill -0 $CLIENT_PID 2>/dev/null; then
            echo "[Round $i] Client finished normally"
            break
        fi

        NOW=$(date +%s)
        ELAPSED=$((NOW - START_TIME))

        if [ $ELAPSED -ge $TIMEOUT ]; then
            echo "[Round $i] Timeout, killing client & server..."

            # kill client
            kill -9 $CLIENT_PID 2>/dev/null

            # kill server（远程）
            ssh $SERVER_USER@$SERVER_IP \
                "kill -9 \$(cat server.pid) 2>/dev/null"

            break
        fi
    done

    # 确保 server 被杀
    ssh $SERVER_USER@$SERVER_IP \
        "if [ -f server.pid ]; then kill -9 \$(cat server.pid) 2>/dev/null; rm -f server.pid; fi"

    sleep 1
    echo "[Round $i] Done"
    echo "----------------------------------------"
done

echo "All experiments finished."
