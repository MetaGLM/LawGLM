# LawGLM

## 大赛介绍

关于本次LawGLM比赛及开源项目的背景情况及台前幕后的故事，请参考文档```remain_true_to_our_original_open-source_aspiration_in_the_legal_industry.md```(
这是一个关于开源的不忘初心的故事)。

## 仓库介绍

本仓库是关于2024年琶洲算法大赛的开源代码汇总， 旨在探索大语言模型在法律行业的应用潜力。

+ 比赛链接和介绍: https://tianchi.aliyun.com/competition/entrance/532221
+ 技术： 参赛选手们使用了 Function Call，RAG，长文本等多项技术，让大模型在法律领域发挥了更大的作用。
+ 模型： 比赛选手的灵活使用 `GLM-4-Air`，`GLM-4-AirX`，`GLM-4-Plus`，`GLM-4-Flash` 等多种 GLM API系列模型。
  充分发挥 `GLM-4-AirX` 响应快，`GLM-4-Flash` 免费，`GLM-4-Plus` 精度高等优势，结合使用，实现高性价比解决方案。

## 项目更新

- 🔥🔥 **News**: ```2024/10/20```: 我们整理开源了第一个参赛队伍的代码。并完成了项目的基础工作。

## 比赛规则

### 答疑和规则

+ 官方QA视频: https://www.bilibili.com/video/BV1k4421U78c/?vd_source=c083324a69ff411499cf1b5f539eaac7
+ QA PPT: [点击这里](assets/qa.pdf)
+ 官方解题思路： https://www.bilibili.com/video/BV1k4421U78c/?vd_source=c083324a69ff411499cf1b5f539eaac7

### BaseLine

+ [伍柒](assets/【baseline分享】伍柒.pdf)
+ [法外张三](assets/【baseline分享】法外张三.pdf)
+ [张江高科](assets/【baseline分享】张江高科.pdf)

以上信息可供参考，进一步了解该比赛。

## 队伍代码

+ [APIWeaver](APIWeaver-lawGLM/README.md): 由 [MeiPixel](https://github.com/MeiPixel) 贡献。
  支持文档召回, 通过大模型对话式优化prompt, 运行记录转化为llama factory训练格式 ,一键部署gradio等多样功能。
+ [Vinlic](Vinlic-lawGLM/README.md): 由 [Vinlic](https://github.com/Vinlic)
  贡献。Vinlic队在第三届琶洲算法大赛GLM法律行业大模型挑战赛道中提出了两种方案：方案A结合多轮迭代与FunctionCall实现Token节省，方案B结合多轮迭代、Planner与CodeAct实现更高自由度。
+ [Move_forward_every_da](Move_forward_every_day-lawGLM/README.md): 每天前进30公里团队的终版（复赛）方案。复赛成绩排名第15名。
+ [NickolasNi](NickolasNi-LawGLM/README.md): 由 NickolasNi 贡献，初赛方案。
+ [LegalHi](LegalHi-LawGLM/README.md): LegalHi 团队方案，通过意图分类，问题改写，思维链、结果判断、外反思等多个步骤，优秀完成任务。
+ [](Buycabbage-semi-LawGLM)
## 开源协议

本代码中无特殊说明或者无注名额外协议的，均使用 [Apache 2.0](LICENSE) 协议。

## 贡献指南

我们欢迎任何参与比赛的队伍提交自己的比赛作品。

如果您想参与贡献，请参考 [这里](assets/contribute_zh.md)

我们感谢来自以下开发者的贡献：

[![lawglm contributors](https://contrib.rocks/image?repo=metaglm/lawglm&max=2000)](https://github.com/metaglm/lawglm/graphs/contributors)
