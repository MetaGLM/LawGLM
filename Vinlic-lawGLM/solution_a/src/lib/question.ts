import fs from "fs-extra";
import _ from "lodash";

import IQuestion from "./interfaces/IQuestion.ts";
import IMessage from "./interfaces/IMessage.ts";
import { MessageType } from "@/lib/enums.ts";
import api from "./api.ts";
import tools from "./tools.ts";
import llm from "./llm.ts";
import config from "./config.ts";
import logger from "./logger.ts";

// 任务的最大交互轮次
const MAX_ROUNDS = config.task.max_rounds;
// 任务的最大重试轮次
const MAX_RETRY_ROUNDS = config.task.max_retry_rounds;
// 题目分类
const QUESTION_CATEGORYS = [
  ["公司信息", "查询指定公司的基本信息、注册信息、子公司等相关信息"],
  [
    "历史案件",
    "根据案号、案由、原告被告等信息查询法律文书历史案件，查询案件的判决所依据的法律条文，查询律师事务所法律代理等信息等",
  ],
  ["法律条文", "查询法律概念或了解法条内容"],
  ["日常聊天", "用户可能只是想跟你聊两句"],
];

async function getQuestions(filename: string): Promise<IQuestion[]> {
  const raw = (await fs.readFile(filename)).toString();
  const list = raw.split("\n");
  if (list[list.length - 1].trim() == "") list.pop();
  return list.map((v) => JSON.parse(v));
}

/**
 * 生成问题答案
 *
 * @param question 问题对象
 */
async function generateAnswer(
  question: string,
  messageCallback?: (msg: IMessage) => void
) {
  messageCallback = messageCallback || (() => {});
  // 交互轮次
  let rounds = 0;
  // 重试轮次
  let retryRounds = 0;
  // 最后一次工具调用信息
  let latestToolCallTemp;
  // 最后一次答案内容
  let latestAnswer = "";
  // 问题分类
  let classifys;
  // 多个分类生成的答案
  let answers = [];
  // 统计消耗的总Token数量
  let totalTokens = 0;
  // 插入在问题后面的内容
  let afterContent = "";
  // 消息上下文
  let history = [];
  // 禁用工具名称列表
  let disableToolNames = [];
  // 工具调用日志
  let toolCallLog = "";
  while (true) {
    // 判断交互轮次是否超过最大轮次
    if (rounds++ >= MAX_ROUNDS) break;
    if (
      answers.length > 0 &&
      answers.filter((v) => v.content).length == answers.length
    ) {
      // 答案聚合
      const allAnswer = answers.reduce(
        (str, v, i) => `${str}${v.content}\n\n`,
        ""
      );
      messageCallback({ type: MessageType.Consulting, title: "✍️ 优化答案" });
      // 答案整理复述
      latestAnswer = await llm.answerRephrase(
        question,
        allAnswer,
        (tokens) => (totalTokens += tokens)
      );
      // 阶段性答案
      console.log(`阶段性答案：${latestAnswer}`);
      messageCallback({
        type: MessageType.Consulting,
        title: "✍️ 优化答案",
        data: latestAnswer,
        finish: true,
      });
      messageCallback({ type: MessageType.Consulting, title: "🔍 检查答案" });
      // 检查任务是否完成，否则提供进一步指导
      const { completed, explain } = await llm.checkTaskCompleted(
        question,
        latestAnswer,
        history,
        retryRounds,
        (tokens) => (totalTokens += tokens)
      );
      if (!completed) {
        // 判断重试轮次是否超过最大轮次
      if (++retryRounds >= MAX_RETRY_ROUNDS) break;
        messageCallback({
          type: MessageType.Consulting,
          title: "🔍 检查答案",
          data: `答案检查不通过：${explain}`,
          error: true,
        });
        latestToolCallTemp = undefined;
        history = [];
        // 插入答案和进一步指导
        history.push({
          role: "user",
          content: `${latestAnswer}\n\n以上答案不完整，请使用工具来查询完善！\n目前缺失信息：\n${explain}`,
        });
        logger.warn(`[不完整的答案] ${latestAnswer}`);
        logger.warn(`[新一轮任务提示] ${explain}`);
        // 清空分类，下一轮重新分类
        classifys = undefined;
        // 清空答案
        answers = [];
        continue;
      }
      messageCallback({
        type: MessageType.Consulting,
        title: "🔍 检查答案",
        data: "检查通过",
        finish: true,
      });
      break;
    }
    // 问题分类
    if (!classifys) {
      messageCallback({ type: MessageType.Classify, title: "🔀 问题分类" });
      classifys = await llm.questionClassify(
        question,
        QUESTION_CATEGORYS,
        (tokens) => (totalTokens += tokens)
      );
      messageCallback({
        type: MessageType.Classify,
        title: "🔀 问题分类",
        data: classifys,
        finish: true,
      });
    }
    if (classifys.length == 0) {
      classifys = undefined;
      continue;
    }
    // 答案生成
    answers = [];
    for (let classify of classifys) {
      let answer: {
        content: string;
        calls: {
          id: string;
          name: string;
          args: any;
        }[];
      };
      switch (classify) {
        case "法律条文":
          if (
            !history[history.length - 1] ||
            history[history.length - 1].role != "tool"
          )
            messageCallback({
              type: MessageType.Consulting,
              title: "📚️ 咨询法律条文",
            });
          // 生成法律条文答案
          answer = await llm.consultingLegalConcept(
            question,
            history,
            afterContent,
            (tokens) => totalTokens + tokens
          );
          answer.content &&
            messageCallback({
              type: MessageType.Consulting,
              title: "📚️ 咨询法律条文",
              data: answer.content,
              finish: true,
            });
          break;
        case "公司信息":
          if (
            !history[history.length - 1] ||
            history[history.length - 1].role != "tool"
          )
            messageCallback({
              type: MessageType.Consulting,
              title: "🏢 咨询公司信息",
            });
          // 生成公司信息答案
          answer = await llm.consultingCompanyInfo(
            question,
            history,
            afterContent,
            disableToolNames,
            (tokens) => (totalTokens += tokens)
          );
          answer.content &&
            messageCallback({
              type: MessageType.Consulting,
              title: "🏢 咨询公司信息",
              data: answer.content,
              finish: true,
            });
          break;
        case "历史案件":
          if (
            !history[history.length - 1] ||
            history[history.length - 1].role != "tool"
          )
            messageCallback({
              type: MessageType.Consulting,
              title: "⚖️ 咨询历史案件",
            });
          // 生成历史案件答案
          answer = await llm.consultingLegalDocument(
            question,
            history,
            afterContent,
            disableToolNames,
            (tokens) => totalTokens + tokens
          );
          answer.content &&
            messageCallback({
              type: MessageType.Consulting,
              title: "⚖️ 咨询历史案件",
              data: answer.content,
              finish: true,
            });
          break;
        case "日常聊天":
          messageCallback({
            type: MessageType.Consulting,
            title: "😀 回答问题",
          });
          const result = await llm.communication(
            question,
            (tokens) => totalTokens + tokens
          );
          logger.success(`消耗Token数量【${totalTokens}】`);
          messageCallback({
            type: MessageType.Consulting,
            title: "😀 回答问题",
            data: result,
            finish: true,
            tokens: totalTokens,
          });
          return {
            answer: result,
            totalTokens: totalTokens,
          };
        default:
          messageCallback({
            type: MessageType.Consulting,
            title: "🌐 网络检索",
          });
          logger.warn(`[意料之外的问题分类，将使用网络检索] ${classify}`);
          answer = {
            content: await api.webSearch(question),
            calls: [],
          };
          messageCallback({
            type: MessageType.Consulting,
            title: "🌐 网络检索",
            finish: true,
          });
      }
      answers.push(answer);
    }
    // 清空禁用的工具名称
    disableToolNames = [];
    // 调用工具
    for (let answer of answers) {
      for (let call of answer.calls) {
        const callTemp = JSON.stringify(
          `${call.name}${Object.entries(call.args).reduce(
            (str, v) => str + v,
            ""
          )}`
        );
        if (latestToolCallTemp && latestToolCallTemp == callTemp) {
          disableToolNames.push(call.name);
          logger.warn(
            `[本轮已禁用${disableToolNames.join("、")}工具防止重复调用]`
          );
          afterContent = `工具调用日志：\n${toolCallLog}\n\n如果题目还需要其它信息请修改参数调用工具查询相应信息，否则请直接回答问题。`;
        } else {
          latestToolCallTemp = callTemp;
          messageCallback({
            type: MessageType.CallTool,
            title: "🔧 工具调用",
            data: call,
          });
          let toolResult = await tools.toolCallDistribution(
            call.name,
            call.args,
            messageCallback
          );
          toolCallLog += `已调用${call.name}，参数：${Object.entries(
            call.args
          ).reduce((str, v) => str + v[0] + "=" + v[1] + ";", "")}\n`;
          // 工具调用结果
          console.log(`工具调用结果：${toolResult}`);
          history.push({
            role: "tool",
            content: `工具查询结果：\n${toolResult}`,
            tool_call_id: call.id,
          });
          messageCallback({
            type: MessageType.CallTool,
            title: "🔧 工具调用",
            data: toolResult,
            finish: true,
          });
        }
      }
    }
  }
  // 没有找到答案时使用网络检索
  if (!latestAnswer) {
    logger.warn(`[法律API无法解决该问题，将使用网络检索]`);
    latestAnswer = await api.webSearch(question);
  }
  logger.success(`消耗Token数量【${totalTokens}】`);
  return {
    answer: latestAnswer,
    totalTokens,
  };
}

async function generateQuestionAnswer(
  param: string,
  messageCallback?: (msg: IMessage) => void
) {
  try {
    if (!param) throw new Error("Question param must be provided");
    let query: string;
    if (_.isNumber(param)) {
      const id = Number(param);
      const questions = await getQuestions("question.jsonl");
      if (!questions[id]) throw new Error(`Question ${id} not found`);
      query = questions[id].question;
    } else query = param;
    console.log(`\n\n题目：${query}`);
    // 读取结果列表，可在中断处继续
    const results = await getQuestions("result.jsonl");
    messageCallback({
      type: MessageType.Question,
      title: "👀 阅读问题",
      data: query,
      finish: true,
    });
    const { answer, totalTokens } = await generateAnswer(
      query,
      messageCallback
    );
    const result = {
      id: results[results.length - 1].id + 1,
      question: query,
      answer
    };
    await fs.appendFile("result.jsonl", `${JSON.stringify(result)}\n`);
    console.log(`答案：${answer}`);
    messageCallback({
      type: MessageType.Answer,
      title: "🤖 答案输出",
      data: answer,
      finish: true,
      tokens: totalTokens
    });
    return {
      answer,
      totalTokens,
    };
  } catch (err) {
    messageCallback({
      type: MessageType.Consulting,
      title: "❌ 解答失败",
      data: err.message,
      error: true,
    });
  }
}

async function generateQuestionsAnswer() {
  // 创建结果文件
  await fs.ensureFile("result.jsonl");
  // 读取题目列表
  const questions = await getQuestions("question.jsonl");
  // 读取结果列表，可在中断处继续
  const results = await getQuestions("result.jsonl");
  if (questions.length == results.length)
    logger.info("所有题目已经完成回答，如果需要重新回答请删除result.jsonl");
  for (let question of questions.slice(results.length)) {
    await (async () => {
    //   console.time();
      console.log(
        `\n\n题目（${question.id + 1}/${questions.length}）：${
          question.question
        }`
      );
      // 生成问题的答案
      const { answer, totalTokens } = await generateAnswer(question.question);
      const result = {
        id: question.id,
        question: question.question,
        answer,
      };
      // 写入结果
      await fs.appendFile("result.jsonl", `${JSON.stringify(result)}\n`);
      console.log(
        `答案（${question.id + 1}/${questions.length}）：${answer}\n\n`
      );
    //   console.timeEnd();
    })().catch((err) => {
      const result = {
        id: question.id,
        question: question.question,
        answer: `问题处理失败：${err.message}`,
      };
      // 写入失败的结果
      fs.appendFile("result.jsonl", `${JSON.stringify(result)}\n`);
      logger.error(err);
    });
  }
}

export default {
  getQuestions,
  generateQuestionsAnswer,
  generateQuestionAnswer,
};
