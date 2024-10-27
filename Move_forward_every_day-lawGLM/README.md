# Move_forward_every_day-lawGLM

## 说明

此代码是 第三届琶洲算法大赛-GLM法律行业大模型挑战赛，每天前进30公里团队的终版（复赛）方案。复赛成绩排名第15名。


## 快速开始

1、安装依赖

```shell
pip install -r requirements.txt
```

2、运行主函数：

```shell
cd app

OPENAI_API_KEY="your ZhipuAI API Keys" python run.py
```



## 解决方案简述

1、先根据API信息和用户问题，让LLM回答出解题思路和需要使用的API。

2、根据用户问题、解题思路、API信息让LLM生成任务流程（包括API查询/筛选/统计/总结等）。

3、依次执行任务流程中的各个子任务，获得子任务结果。

4、整理各个子任务的结果，并结合中间内容信息，完整回答用户问题。

5、线上预测时，采用多线程方式；并对部分错误问题重新进行回答。
