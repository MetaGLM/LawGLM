# 方案概述

第三届琶洲算法大赛-GLM法律行业大模型挑战赛道，LegalHi复赛方案

# 方案介绍

方法步骤：先进行意图分类，之后进行问题改写（处理题目中的噪声）、思考-行动-观察（分解+循环）、结果判断（self-judge）、外反思（对于未解决的问题重新解决）

核心思路：边执行边思考，逐步执行分解，每一步确定下一步需要做什么。可以及时根据情况调整行为。先分解第一个子问题，然后解决完第一个子问题后合并到问题里，再分解第二个，每一步都是“思考-行动-观察”的过程。

![img](https://internal-api-drive-stream.feishu.cn/space/api/box/stream/download/wps/auth_code/?code=be6e646134ac7a7a1847729b4f9de81a_7becd5e03aad94a6_3B5CPPB3DO_H7DH2P0E86FQHCE07GU1LIMCSK)

- main.py：代码入口，首先将问题初步分类，之后采用边执行边思考的方案解决每个问题
- action.py：查询检索、排序、求和等行为接口
- execute_plan.py：规划接口，负责逐步分解问题并调用行为接口解决问题
- reflexion.py：反思接口，解决规划失败的问题
- tool_register：工具文件夹，定义官方提供的api和数据表信息
- prompt.py、tools_class.py：大模型执行具体任务时的提示，引导大模型正确思考
- memory.py、memory.json：记忆模块，引导大模型规范思维和行动
- produce_report.py：解决“整合报告”类复杂问题
- produce_sue.py：解决“民事诉讼”类复杂问题
- run.py、run.sh：运行接口或脚本

## 运行代码

1. 安装依赖

```shell
pip install -r requirements.txt
```


2. 运行主函数：

```shell
bash run.sh
```