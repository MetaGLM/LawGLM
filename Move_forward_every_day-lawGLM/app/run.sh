#!/bin/bash

# 这里可以放入代码运行命令
echo "program start..."
echo $(date +"%Y-%m-%d %H:%M:%S")
pip3 install requests --index-url=http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
echo $(date +"%Y-%m-%d %H:%M:%S")
pip3 install zhipuai --index-url=http://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
echo $(date +"%Y-%m-%d %H:%M:%S")

python3 run.py
echo $(date +"%Y-%m-%d %H:%M:%S")
echo "FINISHED"