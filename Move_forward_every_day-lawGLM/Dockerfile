FROM registry.cn-hangzhou.aliyuncs.com/glm_law/law:v0

# 安装应用程序的依赖
COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
RUN python -m ipykernel install --user --name my_kernel --display-name "My Kernel"
# 下载jieba的词库和分析模块所需的文件
RUN python -c "import jieba; jieba.initialize()"
RUN python -c "import jieba.analyse; jieba.analyse.textrank('劳动合同纠纷')"

# 复制代码到镜像仓库
COPY app /app

# 指定工作目录
WORKDIR /app

# 容器启动运行命令
CMD ["bash", "/app/run.sh"]