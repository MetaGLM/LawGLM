#!/bin/bash

# 设置超时时间为55分钟
TIMEOUT=55m

# 运行Python脚本并限制其执行时间
timeout $TIMEOUT python run.py

# 检查Python脚本是否因超时被终止
if [ $? -eq 124 ]; then
    echo "The script was terminated due to timeout."
else
    echo "The script finished within the time limit."
fi
