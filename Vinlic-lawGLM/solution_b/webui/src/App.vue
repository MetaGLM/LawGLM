<script setup lang="ts">
import { ref, reactive, h, nextTick } from 'vue';
import type IMessage from '@/interfaces/IMessage';
import { MessageType } from "@/enums";
import _ from 'lodash';

let controller = new AbortController()
let signal = controller.signal

let messageId = 0;
let messages = reactive<IMessage[]>([]);
const questionTextareaRef = ref<HTMLTextAreaElement>();
const answerTextareaRef = ref<HTMLTextAreaElement>();
const monitorContainer = ref<HTMLDivElement>();
let handling = false;

function sendQuestion(event: any) {
  if (event.key === 'Enter')
    event.preventDefault();
  handling && controller.abort('stop');
  controller = new AbortController();
  signal = controller.signal;
  const query = questionTextareaRef.value?.value || '';
  if (answerTextareaRef.value)
    answerTextareaRef.value.value = '';
  messages.splice(0, messages.length);
  handling = true;
  generateAnswer(query)
    .then(() => handling = false)
    .catch(err => {
      handling = false;
      if(err == 'stop')
        return;
      if(err.message.indexOf('aborted') != -1)
        return;
      console.error(err);
      alert('发送失败：' + err.message);
    })
}

async function messageHandle(msg: IMessage) {
  const { type, title, data, finish, error } = msg;
  if (msg.type == MessageType.RequestAPI)
    return;
  msg.id = `${messageId++}`;
  if (finish || error) {
    let foundMsgIndex = -1;
    for (let i = messages.length - 1; i >= 0; i--) {
      const _msg = messages[i];
      if (_msg.type != type || _msg.title != title || _msg.finish)
        continue;
      _msg.title = title;
      _msg.data = data;
      _msg.error = error;
      _msg.finish = finish;
      foundMsgIndex = i;
      if (error)
        break;
    }
    if (foundMsgIndex == -1)
        messages.push(msg);
    else {
      const foundMsg = messages[foundMsgIndex];
      if(messages[messages.length - 1] && messages[messages.length -  1].type != foundMsg.type) {
        messages.splice(foundMsgIndex, 1);
        messages.push(foundMsg);
      }
    }
  }
  else
    messages.push(msg);
  nextTick(() => {
    if (monitorContainer.value)
      monitorContainer.value.scrollTop = monitorContainer.value.scrollHeight;
  });
  if (msg.type == MessageType.Answer) {
    if (answerTextareaRef.value)
      answerTextareaRef.value.value = data;
  }
}

async function generateAnswer(query: string) {
  const baseUrl = import.meta.env.DEV ? 'http://localhost:8656/' : '';
  const response = await fetch(`${baseUrl}question/generate_answer`,
    {
      method: "post",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query
      }),
      signal
    }
  );
  if (!response.ok || !response.body)
    throw new Error("Network response was not ok");
  const reader = response.body.getReader();
  const textDecoder = new TextDecoder();
  let completed = false;
  let raw = "";
  while (!completed) {
    const { done, value } = await reader.read();
    if (done) {
      completed = true;
      break;
    }
    raw += textDecoder.decode(value);
    try {
      const chunks = raw.split("\n\n")
        .filter(v => v);
      for (let chunk of chunks) {
        await messageHandle(JSON.parse(chunk));
      }
      raw = "";
    }
    catch (err) {

    }
  }
}
</script>

<template>
  <div class="container">
    <div class="title">
      <h1>👍 GLM法律顾问</h1>
    </div>
    <div class="split-container">
      <div class="monitor">
        <span>📍 流程可视化</span>
        <div id="monitor-contaienr" ref="monitorContainer">
          <div class="message" v-for="msg, index in messages" :key="msg.id">
            <div :class="'message-contaienr message-contaienr-' + msg.type" v-if="msg.error">
              <div class="message-title">
                <span>{{ msg.title }}不通过</span>
                <span>❗</span>
              </div>
              <div class="message-content">
                {{ _.isString(msg.data) ? msg.data : JSON.stringify(msg.data) }}
              </div>
            </div>
            <div :class="'message-contaienr message-contaienr-' + msg.type" v-else-if="msg.finish">
              <div class="message-title">
                <span>{{ msg.title }}完成</span>
                <span>✅</span>
              </div>
              <div class="message-content">
                {{ _.isString(msg.data) ? msg.data : JSON.stringify(msg.data) }}
              </div>
              <div class="total-tokens" v-if="msg.tokens">
                <span>本次解答耗费 {{ msg.tokens }} token</span>
              </div>
            </div>
            <div :class="'message-contaienr message-contaienr-' + msg.type" v-else>
              <div class="message-title">
                <span>{{ msg.title }}</span>
                <span class="loading">⌛</span>
              </div>
              <div class="message-content">
                {{ _.isString(msg.data) ? msg.data : JSON.stringify(msg.data) }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="form">
        <div id="configure" style="overflow:auto;max-height:500px"></div>
        <div>
          <span>🤔 嘿！帮我瞧瞧这个问题：</span>
          <textarea id="question-textarea" ref="questionTextareaRef" placeholder="输入问题"
            @keydown.enter="sendQuestion">1+1=?</textarea>
          <div class="button-group">
            <button @click="sendQuestion">发送</button>
          </div>
        </div>
        <div>
          <span>🤖 解答如下：</span>
          <textarea id="answer-textarea" ref="answerTextareaRef" placeholder="点击发送，让法律顾问为您解答！" readonly></textarea>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.title {
  margin: 15px;
  text-shadow: 0 0 15px #0091ea;
  font-weight: bold;
}

.container {
  margin: 15px;
  height: 100%;
}

.split-container {
  width: 100%;
  height: 100%;
  display: flex;
}

.split-container>div {
  width: 100%;
  height: 100%;
  flex: 1;
  background: #323232;
  border-radius: 10px;
  box-shadow: 0 0 20px 1px #222;
}

.split-container>div:first-child {
  margin-right: 15px;
}

.monitor {
  padding: 15px 20px;
}

.monitor>span:first-child {
  padding: 5px 0;
  display: block;
  background: #323232;
}

#monitor-contaienr {
  max-height: 545px;
  overflow-y: auto;
  overflow-x: hidden;
}

#monitor-network {
  height: 550px;
}

.form {
  padding: 15px 20px;
}

.form>div:last-child {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 2px #999 dashed;
}

.form>div>span {
  color: #fff;
  font-size: 18px;
}

.form textarea {
  margin: 10px 0;
  width: 100%;
  color: #f5f5f5;
  font-size: 18px;
  min-height: 200px;
  background: #666;
  outline-color: #888;
  border-radius: 5px;
  display: block;
}

.form textarea::-webkit-input-placeholder {
  color: #bbb;
}

.button-group {
  margin-top: 13px;
  justify-content: flex-end;
  display: flex;
}

.button-group button {
  width: 100px;
  background: #0091ea;
  color: #fff;
  padding: 5px 0;
  border-radius: 5px;
  font-weight: bold;
  font-size: 18px;
  border: 1px #f5f5f5 solid;
  cursor: pointer;
}

.button-group button:hover {
  background: #009dff;
}

.message {
  margin: 5px;
  padding: 5px;
  padding-bottom: 18px;
  display: flex;
  border-bottom: 1px #666 solid;
}

.message:last-of-type {
  padding-bottom: 0;
  border-bottom: none;
}

.message-contaienr {
  width: 100%;
}

.message-title {
  padding: 10px 0;
}

.message-title>span {
  display: inline-block;
}

.message-title>span:last-child {
  margin-left: 10px;
}

.message-content {
  word-break: break-all;
  white-space: pre-wrap;
}

.loading {
  animation: loading-animate 1.5s ease-in-out infinite;
}

.total-tokens {
  margin-top: 10px;
  font-size: 14px;
  color: yellow;
  text-align: right;
  display: block;
}

::-webkit-scrollbar {
  width: 0;
}

@keyframes loading-animate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
