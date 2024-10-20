# GLM Law Solution B

# 方案介绍

api封装在utils.py
整个解决question的封装在 pipeline.py的pipeline_0711(...)函数

# 方案思路

目前解决的思路是多轮，每一轮:
planner降低搜索空间至单个api
使用code_act的方式生成代码解决这单个api的检索问题
中间有各种提取/总结/筛选的llm调用