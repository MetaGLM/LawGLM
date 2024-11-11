## law初赛代码
使用zhipuai和requests库
安装完成后运行answer_comp.py开始答题 
生成答案为saltfire_result.json文件
## 思路
通过解析提问返回的答案，当遇到工具调用tool=none时，截取调用函数内容解析调用
区分query和need_fields
通过多层询问和api调用获取答案
遇到tools调用失败，字符解析

## 复现步骤
python版本：3.8
```commandline
pip install -r requirements.txt
```
填入apikey和token

```commandline
python answer_comp.py
```




