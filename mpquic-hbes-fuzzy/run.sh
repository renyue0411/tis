#!/bin/bash

# 预定义的 (path_1_bandwidth, path_1_delay) 组合
BANDWIDTH_DELAY_LIST=(
#     "10 5"
    # "10 30"
    "10 120"
    "10 360"
#     "5 5"
#     "5 30"
#     "5 120"
#     "5 360"
#     "2 5"
#     "2 30"
#     "2 120"
#     "2 360"
)

# BANDWIDTH_DELAY_LIST=(
#     "10 30 2 s1"
#     "10 120 12 s2"
#     "10 360 72 s3"
#     "5 30 2 s4"
#     "5 120 12 s5"
#     "5 360 72 s6"
# )

# 循环遍历每个 (path_1_bandwidth, path_1_delay) 组合
for params in "${BANDWIDTH_DELAY_LIST[@]}"
do
    # 解析带宽和延迟
    # read -r PATH_1_BANDWIDTH PATH_1_DELAY PATH_1_JITTER SCENARIO <<< "$params"
    read -r PATH_1_BANDWIDTH PATH_1_DELAY <<< "$params"

    # echo "=========================================="
    # echo "Scenario: ${SCENARIO}, Path 1 parameter: "
    # echo "bandwidth: ${PATH_1_BANDWIDTH}Mbps"
    # echo "delay: ${PATH_1_DELAY}ms"
    # echo "jitter: ${PATH_1_JITTER}ms"
    # echo "=========================================="
    
    # 验证参数已正确读取
    # if [ -z "$PATH_1_BANDWIDTH" ] || [ -z "$PATH_1_DELAY" ] || [ -z "$PATH_1_JITTER" ] || [ -z "$SCENARIO" ]; then
    #     echo "错误：参数读取失败"
    #     continue
    # fi

    # 将当前参数写入文件，每次覆盖上次 for pstream
#    echo "$PATH_1_BANDWIDTH $PATH_1_DELAY" > ~/go/src/github.com/lucas-clemente/pstream/current_params.txt

    # 使用 `sed` 修改 Python 文件中的变量
    sed -i "s/path_1_bandwidth = '.*'/path_1_bandwidth = '$PATH_1_BANDWIDTH'/" quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py
    sed -i "s/path_1_delay = '.*'/path_1_delay = '$PATH_1_DELAY'/" quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py
    # sed -i "s/path_1_jitter = '.*'/path_1_jitter = '$PATH_1_JITTER'/" quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py
    # sed -i "s/scenario = '.*'/scenario = '$SCENARIO'/" quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py

    # 运行 Python 文件
    python quic_mptcp_https_tests_expdes_wsp_lowbdp_quic.py

    # 可选：等待一段时间，避免过载
    sleep 1
done
