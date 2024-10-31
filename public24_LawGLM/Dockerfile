# Base Images 
FROM registry.cn-hangzhou.aliyuncs.com/glm_law/law:v0 
# 如有安装其他软件的需求
RUN apt-get update && apt-get install -y \
    curl \
    zip \
    unzip
##安装python依赖包 
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
## 把当前文件夹里的文件构建到镜像的根目录下,并设置为默认工作目录 
ADD . /app 
WORKDIR /app 
## 镜像启动后统一执行 sh run.sh 
CMD ["sh", "run.sh"]