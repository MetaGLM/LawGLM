// src/index.ts
import minimist from "minimist";

// src/lib/logger.ts
import path from "path";
import _util from "util";
import "colors";
import _ from "lodash";
import fs2 from "fs-extra";
import { format as dateFormat } from "date-fns";

// src/lib/config.ts
import fs from "fs-extra";
import yaml from "yaml";
if (!fs.pathExistsSync("config.yml"))
  throw new Error("config.yml not found");
var config_default = yaml.parse(fs.readFileSync("config.yml").toString()) || {};

// src/lib/logger.ts
var isVercelEnv = process.env.VERCEL;
var LogWriter = class {
  #buffers = [];
  constructor() {
    !isVercelEnv && fs2.ensureDirSync("logs");
    !isVercelEnv && this.work();
  }
  push(content) {
    const buffer = Buffer.from(content);
    this.#buffers.push(buffer);
  }
  writeSync(buffer) {
    !isVercelEnv && fs2.appendFileSync(path.join("logs", `/${this.getDateString()}.log`), buffer);
  }
  async write(buffer) {
    !isVercelEnv && await fs2.appendFile(path.join("logs", `/${this.getDateString()}.log`), buffer);
  }
  flush() {
    if (!this.#buffers.length) return;
    !isVercelEnv && fs2.appendFileSync(path.join("logs", `/${this.getDateString()}.log`), Buffer.concat(this.#buffers));
  }
  work() {
    if (!this.#buffers.length) return setTimeout(this.work.bind(this), 300);
    const buffer = Buffer.concat(this.#buffers);
    this.#buffers = [];
    this.write(buffer).finally(() => setTimeout(this.work.bind(this), 300)).catch((err) => console.error("Log write error:", err));
  }
  getDateString(format = "yyyy-MM-dd", date = /* @__PURE__ */ new Date()) {
    return dateFormat(date, format);
  }
};
var LogText = class {
  /** @type {string} 日志级别 */
  level;
  /** @type {string} 日志文本 */
  text;
  /** @type {string} 日志来源 */
  source;
  /** @type {Date} 日志发生时间 */
  time = /* @__PURE__ */ new Date();
  constructor(level, ...params) {
    this.level = level;
    this.text = _util.format.apply(null, params);
    this.source = this.#getStackTopCodeInfo();
  }
  #getStackTopCodeInfo() {
    const unknownInfo = { name: "unknown", codeLine: 0, codeColumn: 0 };
    const stackArray = new Error().stack.split("\n");
    const text = stackArray[4];
    if (!text)
      return unknownInfo;
    const match = text.match(/at (.+) \((.+)\)/) || text.match(/at (.+)/);
    if (!match || !_.isString(match[2] || match[1]))
      return unknownInfo;
    const temp = match[2] || match[1];
    const _match = temp.match(/([a-zA-Z0-9_\-\.]+)\:(\d+)\:(\d+)$/);
    if (!_match)
      return unknownInfo;
    const [, scriptPath, codeLine, codeColumn] = _match;
    return {
      name: scriptPath ? scriptPath.replace(/.js$/, "") : "unknown",
      path: scriptPath || null,
      codeLine: parseInt(codeLine || 0),
      codeColumn: parseInt(codeColumn || 0)
    };
  }
  toString() {
    return `[${dateFormat(this.time, "yyyy-MM-dd HH:mm:ss.SSS")}][${this.level}][${this.source.name}<${this.source.codeLine},${this.source.codeColumn}>] ${this.text}`;
  }
};
var Logger = class _Logger {
  /** @type {Object} 系统配置 */
  config = {};
  /** @type {Object} 日志级别映射 */
  static Level = {
    Success: "success",
    Info: "info",
    Log: "log",
    Debug: "debug",
    Warning: "warning",
    Error: "error",
    Fatal: "fatal"
  };
  /** @type {Object} 日志级别文本颜色樱色 */
  static LevelColor = {
    [_Logger.Level.Success]: "green",
    [_Logger.Level.Info]: "brightCyan",
    [_Logger.Level.Debug]: "white",
    [_Logger.Level.Warning]: "brightYellow",
    [_Logger.Level.Error]: "brightRed",
    [_Logger.Level.Fatal]: "red"
  };
  #writer;
  constructor() {
    this.#writer = new LogWriter();
  }
  header() {
    this.#writer.writeSync(Buffer.from(`

===================== LOG START ${dateFormat(/* @__PURE__ */ new Date(), "yyyy-MM-dd HH:mm:ss.SSS")} =====================

`));
  }
  footer() {
    this.#writer.flush();
    this.#writer.writeSync(Buffer.from(`

===================== LOG END ${dateFormat(/* @__PURE__ */ new Date(), "yyyy-MM-dd HH:mm:ss.SSS")} =====================

`));
  }
  success(...params) {
    const content = new LogText(_Logger.Level.Success, ...params).toString();
    console.info("\u2705 " + content[_Logger.LevelColor[_Logger.Level.Success]]);
    this.#writer.push(content + "\n");
  }
  info(...params) {
    const content = new LogText(_Logger.Level.Info, ...params).toString();
    console.info("\u{1F30F} " + content[_Logger.LevelColor[_Logger.Level.Info]]);
    this.#writer.push(content + "\n");
  }
  log(...params) {
    const content = new LogText(_Logger.Level.Log, ...params).toString();
    console.log(content[_Logger.LevelColor[_Logger.Level.Log]]);
    this.#writer.push(content + "\n");
  }
  debug(...params) {
    if (!config_default.service.debug) return;
    const content = new LogText(_Logger.Level.Debug, ...params).toString();
    console.debug(content[_Logger.LevelColor[_Logger.Level.Debug]]);
    this.#writer.push(content + "\n");
  }
  warn(...params) {
    const content = new LogText(_Logger.Level.Warning, ...params).toString();
    console.warn("\u2757 " + content[_Logger.LevelColor[_Logger.Level.Warning]]);
    this.#writer.push(content + "\n");
  }
  error(...params) {
    const content = new LogText(_Logger.Level.Error, ...params).toString();
    console.error("\u274C " + content[_Logger.LevelColor[_Logger.Level.Error]]);
    this.#writer.push(content);
  }
  fatal(...params) {
    const content = new LogText(_Logger.Level.Fatal, ...params).toString();
    console.error(content[_Logger.LevelColor[_Logger.Level.Fatal]]);
    this.#writer.push(content);
  }
  destory() {
    this.#writer.destory();
  }
};
var logger_default = new Logger();

// src/lib/initialize.ts
process.setMaxListeners(Infinity);
process.on("uncaughtException", (err, origin) => {
  logger_default.error(`An unhandled error occurred: ${origin}`, err);
});
process.on("unhandledRejection", (_14, promise) => {
  promise.catch((err) => logger_default.error("An unhandled rejection occurred:", err));
});
process.on("warning", (warning) => logger_default.warn("System warning: ", warning));
process.on("exit", () => {
  logger_default.info("Service exit");
  logger_default.footer();
});
process.on("SIGTERM", () => {
  logger_default.warn("received kill signal");
  process.exit(2);
});
process.on("SIGINT", () => {
  process.exit(0);
});

// src/lib/server.ts
import Koa from "koa";
import KoaRouter from "koa-router";
import koaRange from "koa-range";
import koaCors from "koa2-cors";
import koaBody from "koa-body";
import _8 from "lodash";

// src/lib/exceptions/Exception.ts
import assert from "assert";
import _2 from "lodash";
var Exception = class extends Error {
  /** 错误码 */
  errcode;
  /** 错误消息 */
  errmsg;
  /** 数据 */
  data;
  /** HTTP状态码 */
  httpStatusCode;
  /**
   * 构造异常
   * 
   * @param exception 异常
   * @param _errmsg 异常消息
   */
  constructor(exception, _errmsg) {
    assert(_2.isArray(exception), "Exception must be Array");
    const [errcode, errmsg] = exception;
    assert(_2.isFinite(errcode), "Exception errcode invalid");
    assert(_2.isString(errmsg), "Exception errmsg invalid");
    super(_errmsg || errmsg);
    this.errcode = errcode;
    this.errmsg = _errmsg || errmsg;
  }
  compare(exception) {
    const [errcode] = exception;
    return this.errcode == errcode;
  }
  setHTTPStatusCode(value) {
    this.httpStatusCode = value;
    return this;
  }
  setData(value) {
    this.data = _2.defaultTo(value, null);
    return this;
  }
};

// src/lib/request/Request.ts
import _4 from "lodash";

// src/lib/exceptions/APIException.ts
var APIException = class extends Exception {
  /**
   * 构造异常
   * 
   * @param {[number, string]} exception 异常
   */
  constructor(exception, errmsg) {
    super(exception, errmsg);
  }
};

// src/api/consts/exceptions.ts
var exceptions_default = {
  API_TEST: [-9999, "API\u5F02\u5E38\u9519\u8BEF"],
  API_REQUEST_PARAMS_INVALID: [-2e3, "\u8BF7\u6C42\u53C2\u6570\u975E\u6CD5"],
  API_REQUEST_FAILED: [-2001, "\u8BF7\u6C42\u5931\u8D25"],
  API_TOKEN_EXPIRES: [-2002, "Token\u5DF2\u5931\u6548"],
  API_FILE_URL_INVALID: [-2003, "\u8FDC\u7A0B\u6587\u4EF6URL\u975E\u6CD5"],
  API_FILE_EXECEEDS_SIZE: [-2004, "\u8FDC\u7A0B\u6587\u4EF6\u8D85\u51FA\u5927\u5C0F"],
  API_CHAT_STREAM_PUSHING: [-2005, "\u5DF2\u6709\u5BF9\u8BDD\u6D41\u6B63\u5728\u8F93\u51FA"],
  API_CONTENT_FILTERED: [-2006, "\u5185\u5BB9\u7531\u4E8E\u5408\u89C4\u95EE\u9898\u5DF2\u88AB\u963B\u6B62\u751F\u6210"],
  API_IMAGE_GENERATION_FAILED: [-2007, "\u56FE\u50CF\u751F\u6210\u5931\u8D25"]
};

// src/lib/util.ts
import os from "os";
import path2 from "path";
import crypto from "crypto";
import { Readable, Writable } from "stream";
import "colors";
import mime from "mime";
import axios from "axios";
import fs3 from "fs-extra";
import { v1 as uuid } from "uuid";
import { format as dateFormat2 } from "date-fns";
import randomstring from "randomstring";
import _3 from "lodash";

// src/lib/http-status-codes.ts
var http_status_codes_default = {
  CONTINUE: 100,
  //客户端应当继续发送请求。这个临时响应是用来通知客户端它的部分请求已经被服务器接收，且仍未被拒绝。客户端应当继续发送请求的剩余部分，或者如果请求已经完成，忽略这个响应。服务器必须在请求完成后向客户端发送一个最终响应
  SWITCHING_PROTOCOLS: 101,
  //服务器已经理解了客户端的请求，并将通过Upgrade 消息头通知客户端采用不同的协议来完成这个请求。在发送完这个响应最后的空行后，服务器将会切换到在Upgrade 消息头中定义的那些协议。只有在切换新的协议更有好处的时候才应该采取类似措施。例如，切换到新的HTTP 版本比旧版本更有优势，或者切换到一个实时且同步的协议以传送利用此类特性的资源
  PROCESSING: 102,
  //处理将被继续执行
  OK: 200,
  //请求已成功，请求所希望的响应头或数据体将随此响应返回
  CREATED: 201,
  //请求已经被实现，而且有一个新的资源已经依据请求的需要而建立，且其 URI 已经随Location 头信息返回。假如需要的资源无法及时建立的话，应当返回 '202 Accepted'
  ACCEPTED: 202,
  //服务器已接受请求，但尚未处理。正如它可能被拒绝一样，最终该请求可能会也可能不会被执行。在异步操作的场合下，没有比发送这个状态码更方便的做法了。返回202状态码的响应的目的是允许服务器接受其他过程的请求（例如某个每天只执行一次的基于批处理的操作），而不必让客户端一直保持与服务器的连接直到批处理操作全部完成。在接受请求处理并返回202状态码的响应应当在返回的实体中包含一些指示处理当前状态的信息，以及指向处理状态监视器或状态预测的指针，以便用户能够估计操作是否已经完成
  NON_AUTHORITATIVE_INFO: 203,
  //服务器已成功处理了请求，但返回的实体头部元信息不是在原始服务器上有效的确定集合，而是来自本地或者第三方的拷贝。当前的信息可能是原始版本的子集或者超集。例如，包含资源的元数据可能导致原始服务器知道元信息的超级。使用此状态码不是必须的，而且只有在响应不使用此状态码便会返回200 OK的情况下才是合适的
  NO_CONTENT: 204,
  //服务器成功处理了请求，但不需要返回任何实体内容，并且希望返回更新了的元信息。响应可能通过实体头部的形式，返回新的或更新后的元信息。如果存在这些头部信息，则应当与所请求的变量相呼应。如果客户端是浏览器的话，那么用户浏览器应保留发送了该请求的页面，而不产生任何文档视图上的变化，即使按照规范新的或更新后的元信息应当被应用到用户浏览器活动视图中的文档。由于204响应被禁止包含任何消息体，因此它始终以消息头后的第一个空行结尾
  RESET_CONTENT: 205,
  //服务器成功处理了请求，且没有返回任何内容。但是与204响应不同，返回此状态码的响应要求请求者重置文档视图。该响应主要是被用于接受用户输入后，立即重置表单，以便用户能够轻松地开始另一次输入。与204响应一样，该响应也被禁止包含任何消息体，且以消息头后的第一个空行结束
  PARTIAL_CONTENT: 206,
  //服务器已经成功处理了部分 GET 请求。类似于FlashGet或者迅雷这类的HTTP下载工具都是使用此类响应实现断点续传或者将一个大文档分解为多个下载段同时下载。该请求必须包含 Range 头信息来指示客户端希望得到的内容范围，并且可能包含 If-Range 来作为请求条件。响应必须包含如下的头部域：Content-Range 用以指示本次响应中返回的内容的范围；如果是Content-Type为multipart/byteranges的多段下载，则每一段multipart中都应包含Content-Range域用以指示本段的内容范围。假如响应中包含Content-Length，那么它的数值必须匹配它返回的内容范围的真实字节数。Date和ETag或Content-Location，假如同样的请求本应该返回200响应。Expires, Cache-Control，和/或 Vary，假如其值可能与之前相同变量的其他响应对应的值不同的话。假如本响应请求使用了 If-Range 强缓存验证，那么本次响应不应该包含其他实体头；假如本响应的请求使用了 If-Range 弱缓存验证，那么本次响应禁止包含其他实体头；这避免了缓存的实体内容和更新了的实体头信息之间的不一致。否则，本响应就应当包含所有本应该返回200响应中应当返回的所有实体头部域。假如 ETag 或 Latest-Modified 头部不能精确匹配的话，则客户端缓存应禁止将206响应返回的内容与之前任何缓存过的内容组合在一起。任何不支持 Range 以及 Content-Range 头的缓存都禁止缓存206响应返回的内容
  MULTIPLE_STATUS: 207,
  //代表之后的消息体将是一个XML消息，并且可能依照之前子请求数量的不同，包含一系列独立的响应代码
  MULTIPLE_CHOICES: 300,
  //被请求的资源有一系列可供选择的回馈信息，每个都有自己特定的地址和浏览器驱动的商议信息。用户或浏览器能够自行选择一个首选的地址进行重定向。除非这是一个HEAD请求，否则该响应应当包括一个资源特性及地址的列表的实体，以便用户或浏览器从中选择最合适的重定向地址。这个实体的格式由Content-Type定义的格式所决定。浏览器可能根据响应的格式以及浏览器自身能力，自动作出最合适的选择。当然，RFC 2616规范并没有规定这样的自动选择该如何进行。如果服务器本身已经有了首选的回馈选择，那么在Location中应当指明这个回馈的 URI；浏览器可能会将这个 Location 值作为自动重定向的地址。此外，除非额外指定，否则这个响应也是可缓存的
  MOVED_PERMANENTLY: 301,
  //被请求的资源已永久移动到新位置，并且将来任何对此资源的引用都应该使用本响应返回的若干个URI之一。如果可能，拥有链接编辑功能的客户端应当自动把请求的地址修改为从服务器反馈回来的地址。除非额外指定，否则这个响应也是可缓存的。新的永久性的URI应当在响应的Location域中返回。除非这是一个HEAD请求，否则响应的实体中应当包含指向新的URI的超链接及简短说明。如果这不是一个GET或者HEAD请求，因此浏览器禁止自动进行重定向，除非得到用户的确认，因为请求的条件可能因此发生变化。注意：对于某些使用 HTTP/1.0 协议的浏览器，当它们发送的POST请求得到了一个301响应的话，接下来的重定向请求将会变成GET方式
  FOUND: 302,
  //请求的资源现在临时从不同的URI响应请求。由于这样的重定向是临时的，客户端应当继续向原有地址发送以后的请求。只有在Cache-Control或Expires中进行了指定的情况下，这个响应才是可缓存的。新的临时性的URI应当在响应的 Location 域中返回。除非这是一个HEAD请求，否则响应的实体中应当包含指向新的URI的超链接及简短说明。如果这不是一个GET或者HEAD请求，那么浏览器禁止自动进行重定向，除非得到用户的确认，因为请求的条件可能因此发生变化。注意：虽然RFC 1945和RFC 2068规范不允许客户端在重定向时改变请求的方法，但是很多现存的浏览器将302响应视作为303响应，并且使用GET方式访问在Location中规定的URI，而无视原先请求的方法。状态码303和307被添加了进来，用以明确服务器期待客户端进行何种反应
  SEE_OTHER: 303,
  //对应当前请求的响应可以在另一个URI上被找到，而且客户端应当采用 GET 的方式访问那个资源。这个方法的存在主要是为了允许由脚本激活的POST请求输出重定向到一个新的资源。这个新的 URI 不是原始资源的替代引用。同时，303响应禁止被缓存。当然，第二个请求（重定向）可能被缓存。新的 URI 应当在响应的Location域中返回。除非这是一个HEAD请求，否则响应的实体中应当包含指向新的URI的超链接及简短说明。注意：许多 HTTP/1.1 版以前的浏览器不能正确理解303状态。如果需要考虑与这些浏览器之间的互动，302状态码应该可以胜任，因为大多数的浏览器处理302响应时的方式恰恰就是上述规范要求客户端处理303响应时应当做的
  NOT_MODIFIED: 304,
  //如果客户端发送了一个带条件的GET请求且该请求已被允许，而文档的内容（自上次访问以来或者根据请求的条件）并没有改变，则服务器应当返回这个状态码。304响应禁止包含消息体，因此始终以消息头后的第一个空行结尾。该响应必须包含以下的头信息：Date，除非这个服务器没有时钟。假如没有时钟的服务器也遵守这些规则，那么代理服务器以及客户端可以自行将Date字段添加到接收到的响应头中去（正如RFC 2068中规定的一样），缓存机制将会正常工作。ETag或 Content-Location，假如同样的请求本应返回200响应。Expires, Cache-Control，和/或Vary，假如其值可能与之前相同变量的其他响应对应的值不同的话。假如本响应请求使用了强缓存验证，那么本次响应不应该包含其他实体头；否则（例如，某个带条件的 GET 请求使用了弱缓存验证），本次响应禁止包含其他实体头；这避免了缓存了的实体内容和更新了的实体头信息之间的不一致。假如某个304响应指明了当前某个实体没有缓存，那么缓存系统必须忽视这个响应，并且重复发送不包含限制条件的请求。假如接收到一个要求更新某个缓存条目的304响应，那么缓存系统必须更新整个条目以反映所有在响应中被更新的字段的值
  USE_PROXY: 305,
  //被请求的资源必须通过指定的代理才能被访问。Location域中将给出指定的代理所在的URI信息，接收者需要重复发送一个单独的请求，通过这个代理才能访问相应资源。只有原始服务器才能建立305响应。注意：RFC 2068中没有明确305响应是为了重定向一个单独的请求，而且只能被原始服务器建立。忽视这些限制可能导致严重的安全后果
  UNUSED: 306,
  //在最新版的规范中，306状态码已经不再被使用
  TEMPORARY_REDIRECT: 307,
  //请求的资源现在临时从不同的URI 响应请求。由于这样的重定向是临时的，客户端应当继续向原有地址发送以后的请求。只有在Cache-Control或Expires中进行了指定的情况下，这个响应才是可缓存的。新的临时性的URI 应当在响应的Location域中返回。除非这是一个HEAD请求，否则响应的实体中应当包含指向新的URI 的超链接及简短说明。因为部分浏览器不能识别307响应，因此需要添加上述必要信息以便用户能够理解并向新的 URI 发出访问请求。如果这不是一个GET或者HEAD请求，那么浏览器禁止自动进行重定向，除非得到用户的确认，因为请求的条件可能因此发生变化
  BAD_REQUEST: 400,
  //1.语义有误，当前请求无法被服务器理解。除非进行修改，否则客户端不应该重复提交这个请求 2.请求参数有误
  UNAUTHORIZED: 401,
  //当前请求需要用户验证。该响应必须包含一个适用于被请求资源的 WWW-Authenticate 信息头用以询问用户信息。客户端可以重复提交一个包含恰当的 Authorization 头信息的请求。如果当前请求已经包含了 Authorization 证书，那么401响应代表着服务器验证已经拒绝了那些证书。如果401响应包含了与前一个响应相同的身份验证询问，且浏览器已经至少尝试了一次验证，那么浏览器应当向用户展示响应中包含的实体信息，因为这个实体信息中可能包含了相关诊断信息。参见RFC 2617
  PAYMENT_REQUIRED: 402,
  //该状态码是为了将来可能的需求而预留的
  FORBIDDEN: 403,
  //服务器已经理解请求，但是拒绝执行它。与401响应不同的是，身份验证并不能提供任何帮助，而且这个请求也不应该被重复提交。如果这不是一个HEAD请求，而且服务器希望能够讲清楚为何请求不能被执行，那么就应该在实体内描述拒绝的原因。当然服务器也可以返回一个404响应，假如它不希望让客户端获得任何信息
  NOT_FOUND: 404,
  //请求失败，请求所希望得到的资源未被在服务器上发现。没有信息能够告诉用户这个状况到底是暂时的还是永久的。假如服务器知道情况的话，应当使用410状态码来告知旧资源因为某些内部的配置机制问题，已经永久的不可用，而且没有任何可以跳转的地址。404这个状态码被广泛应用于当服务器不想揭示到底为何请求被拒绝或者没有其他适合的响应可用的情况下
  METHOD_NOT_ALLOWED: 405,
  //请求行中指定的请求方法不能被用于请求相应的资源。该响应必须返回一个Allow 头信息用以表示出当前资源能够接受的请求方法的列表。鉴于PUT，DELETE方法会对服务器上的资源进行写操作，因而绝大部分的网页服务器都不支持或者在默认配置下不允许上述请求方法，对于此类请求均会返回405错误
  NO_ACCEPTABLE: 406,
  //请求的资源的内容特性无法满足请求头中的条件，因而无法生成响应实体。除非这是一个 HEAD 请求，否则该响应就应当返回一个包含可以让用户或者浏览器从中选择最合适的实体特性以及地址列表的实体。实体的格式由Content-Type头中定义的媒体类型决定。浏览器可以根据格式及自身能力自行作出最佳选择。但是，规范中并没有定义任何作出此类自动选择的标准
  PROXY_AUTHENTICATION_REQUIRED: 407,
  //与401响应类似，只不过客户端必须在代理服务器上进行身份验证。代理服务器必须返回一个Proxy-Authenticate用以进行身份询问。客户端可以返回一个Proxy-Authorization信息头用以验证。参见RFC 2617
  REQUEST_TIMEOUT: 408,
  //请求超时。客户端没有在服务器预备等待的时间内完成一个请求的发送。客户端可以随时再次提交这一请求而无需进行任何更改
  CONFLICT: 409,
  //由于和被请求的资源的当前状态之间存在冲突，请求无法完成。这个代码只允许用在这样的情况下才能被使用：用户被认为能够解决冲突，并且会重新提交新的请求。该响应应当包含足够的信息以便用户发现冲突的源头。冲突通常发生于对PUT请求的处理中。例如，在采用版本检查的环境下，某次PUT提交的对特定资源的修改请求所附带的版本信息与之前的某个（第三方）请求向冲突，那么此时服务器就应该返回一个409错误，告知用户请求无法完成。此时，响应实体中很可能会包含两个冲突版本之间的差异比较，以便用户重新提交归并以后的新版本
  GONE: 410,
  //被请求的资源在服务器上已经不再可用，而且没有任何已知的转发地址。这样的状况应当被认为是永久性的。如果可能，拥有链接编辑功能的客户端应当在获得用户许可后删除所有指向这个地址的引用。如果服务器不知道或者无法确定这个状况是否是永久的，那么就应该使用404状态码。除非额外说明，否则这个响应是可缓存的。410响应的目的主要是帮助网站管理员维护网站，通知用户该资源已经不再可用，并且服务器拥有者希望所有指向这个资源的远端连接也被删除。这类事件在限时、增值服务中很普遍。同样，410响应也被用于通知客户端在当前服务器站点上，原本属于某个个人的资源已经不再可用。当然，是否需要把所有永久不可用的资源标记为'410 Gone'，以及是否需要保持此标记多长时间，完全取决于服务器拥有者
  LENGTH_REQUIRED: 411,
  //服务器拒绝在没有定义Content-Length头的情况下接受请求。在添加了表明请求消息体长度的有效Content-Length头之后，客户端可以再次提交该请求 
  PRECONDITION_FAILED: 412,
  //服务器在验证在请求的头字段中给出先决条件时，没能满足其中的一个或多个。这个状态码允许客户端在获取资源时在请求的元信息（请求头字段数据）中设置先决条件，以此避免该请求方法被应用到其希望的内容以外的资源上
  REQUEST_ENTITY_TOO_LARGE: 413,
  //服务器拒绝处理当前请求，因为该请求提交的实体数据大小超过了服务器愿意或者能够处理的范围。此种情况下，服务器可以关闭连接以免客户端继续发送此请求。如果这个状况是临时的，服务器应当返回一个 Retry-After 的响应头，以告知客户端可以在多少时间以后重新尝试
  REQUEST_URI_TOO_LONG: 414,
  //请求的URI长度超过了服务器能够解释的长度，因此服务器拒绝对该请求提供服务。这比较少见，通常的情况包括：本应使用POST方法的表单提交变成了GET方法，导致查询字符串（Query String）过长。重定向URI “黑洞”，例如每次重定向把旧的URI作为新的URI的一部分，导致在若干次重定向后URI超长。客户端正在尝试利用某些服务器中存在的安全漏洞攻击服务器。这类服务器使用固定长度的缓冲读取或操作请求的URI，当GET后的参数超过某个数值后，可能会产生缓冲区溢出，导致任意代码被执行[1]。没有此类漏洞的服务器，应当返回414状态码
  UNSUPPORTED_MEDIA_TYPE: 415,
  //对于当前请求的方法和所请求的资源，请求中提交的实体并不是服务器中所支持的格式，因此请求被拒绝
  REQUESTED_RANGE_NOT_SATISFIABLE: 416,
  //如果请求中包含了Range请求头，并且Range中指定的任何数据范围都与当前资源的可用范围不重合，同时请求中又没有定义If-Range请求头，那么服务器就应当返回416状态码。假如Range使用的是字节范围，那么这种情况就是指请求指定的所有数据范围的首字节位置都超过了当前资源的长度。服务器也应当在返回416状态码的同时，包含一个Content-Range实体头，用以指明当前资源的长度。这个响应也被禁止使用multipart/byteranges作为其 Content-Type
  EXPECTION_FAILED: 417,
  //在请求头Expect中指定的预期内容无法被服务器满足，或者这个服务器是一个代理服务器，它有明显的证据证明在当前路由的下一个节点上，Expect的内容无法被满足
  TOO_MANY_CONNECTIONS: 421,
  //从当前客户端所在的IP地址到服务器的连接数超过了服务器许可的最大范围。通常，这里的IP地址指的是从服务器上看到的客户端地址（比如用户的网关或者代理服务器地址）。在这种情况下，连接数的计算可能涉及到不止一个终端用户
  UNPROCESSABLE_ENTITY: 422,
  //请求格式正确，但是由于含有语义错误，无法响应
  FAILED_DEPENDENCY: 424,
  //由于之前的某个请求发生的错误，导致当前请求失败，例如PROPPATCH
  UNORDERED_COLLECTION: 425,
  //在WebDav Advanced Collections 草案中定义，但是未出现在《WebDAV 顺序集协议》（RFC 3658）中
  UPGRADE_REQUIRED: 426,
  //客户端应当切换到TLS/1.0
  RETRY_WITH: 449,
  //由微软扩展，代表请求应当在执行完适当的操作后进行重试
  INTERNAL_SERVER_ERROR: 500,
  //服务器遇到了一个未曾预料的状况，导致了它无法完成对请求的处理。一般来说，这个问题都会在服务器的程序码出错时出现
  NOT_IMPLEMENTED: 501,
  //服务器不支持当前请求所需要的某个功能。当服务器无法识别请求的方法，并且无法支持其对任何资源的请求
  BAD_GATEWAY: 502,
  //作为网关或者代理工作的服务器尝试执行请求时，从上游服务器接收到无效的响应
  SERVICE_UNAVAILABLE: 503,
  //由于临时的服务器维护或者过载，服务器当前无法处理请求。这个状况是临时的，并且将在一段时间以后恢复。如果能够预计延迟时间，那么响应中可以包含一个 Retry-After 头用以标明这个延迟时间。如果没有给出这个 Retry-After 信息，那么客户端应当以处理500响应的方式处理它。注意：503状态码的存在并不意味着服务器在过载的时候必须使用它。某些服务器只不过是希望拒绝客户端的连接
  GATEWAY_TIMEOUT: 504,
  //作为网关或者代理工作的服务器尝试执行请求时，未能及时从上游服务器（URI标识出的服务器，例如HTTP、FTP、LDAP）或者辅助服务器（例如DNS）收到响应。注意：某些代理服务器在DNS查询超时时会返回400或者500错误
  HTTP_VERSION_NOT_SUPPORTED: 505,
  //服务器不支持，或者拒绝支持在请求中使用的HTTP版本。这暗示着服务器不能或不愿使用与客户端相同的版本。响应中应当包含一个描述了为何版本不被支持以及服务器支持哪些协议的实体
  VARIANT_ALSO_NEGOTIATES: 506,
  //服务器存在内部配置错误：被请求的协商变元资源被配置为在透明内容协商中使用自己，因此在一个协商处理中不是一个合适的重点
  INSUFFICIENT_STORAGE: 507,
  //服务器无法存储完成请求所必须的内容。这个状况被认为是临时的
  BANDWIDTH_LIMIT_EXCEEDED: 509,
  //服务器达到带宽限制。这不是一个官方的状态码，但是仍被广泛使用
  NOT_EXTENDED: 510
  //获取资源所需要的策略并没有没满足
};

// src/lib/util.ts
var autoIdMap = /* @__PURE__ */ new Map();
var util = {
  is2DArrays(value) {
    return _3.isArray(value) && (!value[0] || _3.isArray(value[0]) && _3.isArray(value[value.length - 1]));
  },
  uuid: (separator = true) => separator ? uuid() : uuid().replace(/\-/g, ""),
  autoId: (prefix = "") => {
    let index = autoIdMap.get(prefix);
    if (index > 999999) index = 0;
    autoIdMap.set(prefix, (index || 0) + 1);
    return `${prefix}${index || 1}`;
  },
  ignoreJSONParse(value) {
    const result = _3.attempt(() => JSON.parse(value));
    if (_3.isError(result)) return null;
    return result;
  },
  generateRandomString(options) {
    return randomstring.generate(options);
  },
  getResponseContentType(value) {
    return value.headers ? value.headers["content-type"] || value.headers["Content-Type"] : null;
  },
  mimeToExtension(value) {
    let extension = mime.getExtension(value);
    if (extension == "mpga") return "mp3";
    return extension;
  },
  extractURLExtension(value) {
    const extname = path2.extname(new URL(value).pathname);
    return extname.substring(1).toLowerCase();
  },
  getDateString(format = "yyyy-MM-dd", date = /* @__PURE__ */ new Date()) {
    return dateFormat2(date, format);
  },
  getIPAddressesByIPv4() {
    const interfaces = os.networkInterfaces();
    const addresses = [];
    for (let name in interfaces) {
      const networks = interfaces[name];
      const results = networks.filter(
        (network) => network.family === "IPv4" && network.address !== "127.0.0.1" && !network.internal
      );
      if (results[0] && results[0].address) addresses.push(results[0].address);
    }
    return addresses;
  },
  getMACAddressesByIPv4() {
    const interfaces = os.networkInterfaces();
    const addresses = [];
    for (let name in interfaces) {
      const networks = interfaces[name];
      const results = networks.filter(
        (network) => network.family === "IPv4" && network.address !== "127.0.0.1" && !network.internal
      );
      if (results[0] && results[0].mac) addresses.push(results[0].mac);
    }
    return addresses;
  },
  generateSSEData(event, data, retry) {
    return `event: ${event || "message"}
data: ${(data || "").replace(/\n/g, "\\n").replace(/\s/g, "\\s")}
retry: ${retry || 3e3}

`;
  },
  buildDataBASE64(type, ext, buffer) {
    return `data:${type}/${ext.replace("jpg", "jpeg")};base64,${buffer.toString(
      "base64"
    )}`;
  },
  isLinux() {
    return os.platform() !== "win32";
  },
  isIPAddress(value) {
    return _3.isString(value) && (/^((2[0-4]\d|25[0-5]|[01]?\d\d?)\.){3}(2[0-4]\d|25[0-5]|[01]?\d\d?)$/.test(
      value
    ) || /\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*/.test(
      value
    ));
  },
  isPort(value) {
    return _3.isNumber(value) && value > 0 && value < 65536;
  },
  isReadStream(value) {
    return value && (value instanceof Readable || "readable" in value || value.readable);
  },
  isWriteStream(value) {
    return value && (value instanceof Writable || "writable" in value || value.writable);
  },
  isHttpStatusCode(value) {
    return _3.isNumber(value) && Object.values(http_status_codes_default).includes(value);
  },
  isURL(value) {
    return !_3.isUndefined(value) && /^(http|https)/.test(value);
  },
  isSrc(value) {
    return !_3.isUndefined(value) && /^\/.+\.[0-9a-zA-Z]+(\?.+)?$/.test(value);
  },
  isBASE64(value) {
    return !_3.isUndefined(value) && /^[a-zA-Z0-9\/\+]+(=?)+$/.test(value);
  },
  isBASE64Data(value) {
    return /^data:/.test(value);
  },
  extractBASE64DataFormat(value) {
    const match = value.trim().match(/^data:(.+);base64,/);
    if (!match) return null;
    return match[1];
  },
  removeBASE64DataHeader(value) {
    return value.replace(/^data:(.+);base64,/, "");
  },
  isDataString(value) {
    return /^(base64|json):/.test(value);
  },
  isStringNumber(value) {
    return _3.isFinite(Number(value));
  },
  isUnixTimestamp(value) {
    return /^[0-9]{10}$/.test(`${value}`);
  },
  isTimestamp(value) {
    return /^[0-9]{13}$/.test(`${value}`);
  },
  isEmail(value) {
    return /^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$/.test(
      value
    );
  },
  isAsyncFunction(value) {
    return Object.prototype.toString.call(value) === "[object AsyncFunction]";
  },
  async isAPNG(filePath) {
    let head;
    const readStream = fs3.createReadStream(filePath, { start: 37, end: 40 });
    const readPromise = new Promise((resolve, reject) => {
      readStream.once("end", resolve);
      readStream.once("error", reject);
    });
    readStream.once("data", (data) => head = data);
    await readPromise;
    return head.compare(Buffer.from([97, 99, 84, 76])) === 0;
  },
  unixTimestamp() {
    return parseInt(`${Date.now() / 1e3}`);
  },
  timestamp() {
    return Date.now();
  },
  urlJoin(...values) {
    let url = "";
    for (let i = 0; i < values.length; i++)
      url += `${i > 0 ? "/" : ""}${values[i].replace(/^\/*/, "").replace(/\/*$/, "")}`;
    return url;
  },
  millisecondsToHmss(milliseconds) {
    if (_3.isString(milliseconds)) return milliseconds;
    milliseconds = parseInt(milliseconds);
    const sec = Math.floor(milliseconds / 1e3);
    const hours = Math.floor(sec / 3600);
    const minutes = Math.floor((sec - hours * 3600) / 60);
    const seconds = sec - hours * 3600 - minutes * 60;
    const ms = milliseconds % 6e4 - seconds * 1e3;
    return `${hours > 9 ? hours : "0" + hours}:${minutes > 9 ? minutes : "0" + minutes}:${seconds > 9 ? seconds : "0" + seconds}.${ms}`;
  },
  millisecondsToTimeString(milliseconds) {
    if (milliseconds < 1e3) return `${milliseconds}ms`;
    if (milliseconds < 6e4)
      return `${parseFloat((milliseconds / 1e3).toFixed(2))}s`;
    return `${Math.floor(milliseconds / 1e3 / 60)}m${Math.floor(
      milliseconds / 1e3 % 60
    )}s`;
  },
  rgbToHex(r, g, b) {
    return ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
  },
  hexToRgb(hex) {
    const value = parseInt(hex.replace(/^#/, ""), 16);
    return [value >> 16 & 255, value >> 8 & 255, value & 255];
  },
  md5(value) {
    return crypto.createHash("md5").update(value).digest("hex");
  },
  arrayParse(value) {
    return _3.isArray(value) ? value : [value];
  },
  booleanParse(value) {
    return value === "true" || value === true ? true : false;
  },
  encodeBASE64(value) {
    return Buffer.from(value).toString("base64");
  },
  decodeBASE64(value) {
    return Buffer.from(value, "base64").toString();
  },
  async fetchFileBASE64(url) {
    const result = await axios.get(url, {
      responseType: "arraybuffer"
    });
    return result.data.toString("base64");
  }
};
var util_default = util;

// src/lib/request/Request.ts
var Request = class {
  /** 请求方法 */
  method;
  /** 请求URL */
  url;
  /** 请求路径 */
  path;
  /** 请求载荷类型 */
  type;
  /** 请求headers */
  headers;
  /** 请求原始查询字符串 */
  search;
  /** 请求查询参数 */
  query;
  /** 请求URL参数 */
  params;
  /** 请求载荷 */
  body;
  /** 上传的文件 */
  files;
  /** 客户端IP地址 */
  remoteIP;
  /** 请求接受时间戳（毫秒） */
  time;
  constructor(ctx, options = {}) {
    const { time } = options;
    this.method = ctx.request.method;
    this.url = ctx.request.url;
    this.path = ctx.request.path;
    this.type = ctx.request.type;
    this.headers = ctx.request.headers || {};
    this.search = ctx.request.search;
    this.query = ctx.query || {};
    this.params = ctx.params || {};
    this.body = ctx.request.body || {};
    this.files = ctx.request.files || {};
    this.remoteIP = this.headers["X-Real-IP"] || this.headers["x-real-ip"] || this.headers["X-Forwarded-For"] || this.headers["x-forwarded-for"] || ctx.ip || null;
    this.time = Number(_4.defaultTo(time, util_default.timestamp()));
  }
  validate(key, fn, errorMessage) {
    try {
      const value = _4.get(this, key);
      if (fn) {
        if (fn(value) === false)
          throw `[Mismatch] -> ${fn}`;
      } else if (_4.isUndefined(value))
        throw "[Undefined]";
    } catch (err) {
      logger_default.warn(`Params ${key} invalid:`, err);
      throw new APIException(exceptions_default.API_REQUEST_PARAMS_INVALID, errorMessage || `Params ${key} invalid`);
    }
    return this;
  }
};

// src/lib/response/Response.ts
import mime2 from "mime";
import _6 from "lodash";

// src/lib/response/Body.ts
import _5 from "lodash";
var Body = class _Body {
  /** 状态码 */
  code;
  /** 状态消息 */
  message;
  /** 载荷 */
  data;
  /** HTTP状态码 */
  statusCode;
  constructor(options = {}) {
    const { code, message, data, statusCode } = options;
    this.code = Number(_5.defaultTo(code, 0));
    this.message = _5.defaultTo(message, "OK");
    this.data = _5.defaultTo(data, null);
    this.statusCode = Number(_5.defaultTo(statusCode, 200));
  }
  toObject() {
    return {
      code: this.code,
      message: this.message,
      data: this.data
    };
  }
  static isInstance(value) {
    return value instanceof _Body;
  }
};

// src/lib/response/Response.ts
var Response = class _Response {
  /** 响应HTTP状态码 */
  statusCode;
  /** 响应内容类型 */
  type;
  /** 响应headers */
  headers;
  /** 重定向目标 */
  redirect;
  /** 响应载荷 */
  body;
  /** 响应载荷大小 */
  size;
  /** 响应时间戳 */
  time;
  constructor(body, options = {}) {
    const { statusCode, type, headers, redirect, size, time } = options;
    this.statusCode = Number(_6.defaultTo(statusCode, Body.isInstance(body) ? body.statusCode : void 0));
    this.type = type;
    this.headers = headers;
    this.redirect = redirect;
    this.size = size;
    this.time = Number(_6.defaultTo(time, util_default.timestamp()));
    this.body = body;
  }
  injectTo(ctx) {
    this.redirect && ctx.redirect(this.redirect);
    this.statusCode && (ctx.status = this.statusCode);
    this.type && (ctx.type = mime2.getType(this.type) || this.type);
    const headers = this.headers || {};
    if (this.size && !headers["Content-Length"] && !headers["content-length"])
      headers["Content-Length"] = this.size;
    ctx.set(headers);
    if (Body.isInstance(this.body))
      ctx.body = this.body.toObject();
    else
      ctx.body = this.body;
  }
  static isInstance(value) {
    return value instanceof _Response;
  }
};

// src/lib/response/FailureBody.ts
import _7 from "lodash";

// src/lib/consts/exceptions.ts
var exceptions_default2 = {
  SYSTEM_ERROR: [-1e3, "\u7CFB\u7EDF\u5F02\u5E38"],
  SYSTEM_REQUEST_VALIDATION_ERROR: [-1001, "\u8BF7\u6C42\u53C2\u6570\u6821\u9A8C\u9519\u8BEF"],
  SYSTEM_NOT_ROUTE_MATCHING: [-1002, "\u65E0\u5339\u914D\u7684\u8DEF\u7531"]
};

// src/lib/response/FailureBody.ts
var FailureBody = class _FailureBody extends Body {
  constructor(error, _data) {
    let errcode, errmsg, data = _data, httpStatusCode = http_status_codes_default.OK;
    ;
    if (_7.isString(error))
      error = new Exception(exceptions_default2.SYSTEM_ERROR, error);
    else if (error instanceof APIException || error instanceof Exception)
      ({ errcode, errmsg, data, httpStatusCode } = error);
    else if (_7.isError(error))
      ({ errcode, errmsg, data, httpStatusCode } = new Exception(exceptions_default2.SYSTEM_ERROR, error.message));
    super({
      code: errcode || -1,
      message: errmsg || "Internal error",
      data,
      statusCode: httpStatusCode
    });
  }
  static isInstance(value) {
    return value instanceof _FailureBody;
  }
};

// src/lib/server.ts
var Server = class {
  app;
  router;
  constructor() {
    this.app = new Koa();
    this.app.use(koaCors());
    this.app.use(koaRange);
    this.router = new KoaRouter({ prefix: config_default.service.urlPrefix });
    this.app.use(async (ctx, next) => {
      if (ctx.request.type === "application/xml" || ctx.request.type === "application/ssml+xml")
        ctx.req.headers["content-type"] = "text/xml";
      try {
        await next();
      } catch (err) {
        logger_default.error(err);
        const failureBody = new FailureBody(err);
        new Response(failureBody).injectTo(ctx);
      }
    });
    this.app.use(koaBody({
      enableTypes: ["json", "form", "text", "xml"],
      encoding: "utf-8",
      formLimit: "100mb",
      jsonLimit: "100mb",
      textLimit: "100mb",
      xmlLimit: "100mb",
      formidable: {
        maxFileSize: "100mb"
      },
      multipart: true,
      parsedMethods: ["POST", "PUT", "PATCH"]
    }));
    this.app.on("error", (err) => {
      if (["ECONNRESET", "ECONNABORTED", "EPIPE", "ECANCELED"].includes(err.code)) return;
      logger_default.error(err);
    });
    logger_default.success("Server initialized");
  }
  /**
   * 附加路由
   * 
   * @param routes 路由列表
   */
  attachRoutes(routes) {
    routes.forEach((route) => {
      const prefix = route.prefix || "";
      for (let method in route) {
        if (method === "prefix") continue;
        if (!_8.isObject(route[method])) {
          logger_default.warn(`Router ${prefix} ${method} invalid`);
          continue;
        }
        for (let uri in route[method]) {
          this.router[method](`${prefix}${uri}`, async (ctx) => {
            const { request: request2, response } = await this.#requestProcessing(ctx, route[method][uri]);
            if (response != null && config_default.service.requestLog)
              logger_default.info(`<- ${request2.method} ${request2.url} ${response.time - request2.time}ms`);
          });
        }
      }
      logger_default.info(`Route ${config_default.service.urlPrefix || ""}${prefix} attached`);
    });
    this.app.use(this.router.routes());
    this.app.use((ctx) => {
      const request2 = new Request(ctx);
      logger_default.debug(`-> ${ctx.request.method} ${ctx.request.url} request is not supported - ${request2.remoteIP || "unknown"}`);
      const failureBody = new FailureBody(new Exception(exceptions_default2.SYSTEM_NOT_ROUTE_MATCHING, "Request is not supported"));
      const response = new Response(failureBody);
      response.injectTo(ctx);
      if (config_default.service.requestLog)
        logger_default.info(`<- ${request2.method} ${request2.url} ${response.time - request2.time}ms`);
    });
  }
  /**
   * 请求处理
   * 
   * @param ctx 上下文
   * @param routeFn 路由方法
   */
  #requestProcessing(ctx, routeFn) {
    return new Promise((resolve) => {
      const request2 = new Request(ctx);
      try {
        if (config_default.service.requestLog)
          logger_default.info(`-> ${request2.method} ${request2.url}`);
        routeFn(request2).then((response) => {
          try {
            if (!Response.isInstance(response)) {
              const _response = new Response(response);
              _response.injectTo(ctx);
              return resolve({ request: request2, response: _response });
            }
            response.injectTo(ctx);
            resolve({ request: request2, response });
          } catch (err) {
            logger_default.error(err);
            const failureBody = new FailureBody(err);
            const response2 = new Response(failureBody);
            response2.injectTo(ctx);
            resolve({ request: request2, response: response2 });
          }
        }).catch((err) => {
          try {
            logger_default.error(err);
            const failureBody = new FailureBody(err);
            const response = new Response(failureBody);
            response.injectTo(ctx);
            resolve({ request: request2, response });
          } catch (err2) {
            logger_default.error(err2);
            const failureBody = new FailureBody(err2);
            const response = new Response(failureBody);
            response.injectTo(ctx);
            resolve({ request: request2, response });
          }
        });
      } catch (err) {
        logger_default.error(err);
        const failureBody = new FailureBody(err);
        const response = new Response(failureBody);
        response.injectTo(ctx);
        resolve({ request: request2, response });
      }
    });
  }
  /**
   * 监听端口
   */
  async listen() {
    const host = config_default.service.host;
    const port = config_default.service.port;
    await Promise.all([
      new Promise((resolve, reject) => {
        if (host === "0.0.0.0" || host === "localhost" || host === "127.0.0.1")
          return resolve(null);
        this.app.listen(port, "localhost", (err) => {
          if (err) return reject(err);
          resolve(null);
        });
      }),
      new Promise((resolve, reject) => {
        this.app.listen(port, host, (err) => {
          if (err) return reject(err);
          resolve(null);
        });
      })
    ]);
    logger_default.success(`Server listening on port ${port} (${host})`);
  }
};
var server_default = new Server();

// src/lib/question.ts
import fs4 from "fs-extra";
import _12 from "lodash";

// src/lib/api.ts
import axios2 from "axios";
import _9 from "lodash";
var LAW_API_ENDPOINT = config_default.law_api.endpoint;
var LAW_API_TOKEN = config_default.law_api.token;
var LAW_API_CONCURRENT = config_default.law_api.concurrent;
var WEB_SEARCH_MODEL = config_default.web_search.model;
var WEB_SEARCH_ENDPOINT = config_default.web_search.endpoint;
var WEB_SEARCH_TOKEN = config_default.web_search.token;
async function getCompanyInfoByCompanyName(companyName, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u516C\u53F8\u540D\u79F0\u67E5\u8BE2\u516C\u53F8\u4FE1\u606F] ${companyName}`);
  const [
    info,
    register
  ] = await Promise.all([
    requestObj("/get_company_info", {
      company_name: companyName
    }, messageCallback),
    getCompanyRegisterByCompanyName(companyName, messageCallback)
  ]);
  if (info) {
    delete info["\u7ECF\u8425\u8303\u56F4"];
    register ? logger_default.success(`[\u6210\u529F\u627E\u5230\u516C\u53F8\u4FE1\u606F\u548C\u6CE8\u518C\u4FE1\u606F] ${companyName}`) : logger_default.success(`[\u6210\u529F\u627E\u5230\u516C\u53F8\u4FE1\u606F] ${companyName}`);
    return Object.assign(info, register);
  }
  const _companyName = (await Promise.all([
    searchCompanyNameByInfo({ "\u516C\u53F8\u7B80\u79F0": companyName }, messageCallback),
    searchCompanyNameByInfo({ "\u82F1\u6587\u540D\u79F0": companyName }, messageCallback),
    searchCompanyNameByInfo({ "\u66FE\u7528\u7B80\u79F0": companyName }, messageCallback)
  ])).filter((v) => v)[0];
  if (!_companyName) {
    register ? logger_default.success(`[\u672A\u627E\u5230\u516C\u53F8\u4FE1\u606F\u4F46\u627E\u5230\u6CE8\u518C\u4FE1\u606F] ${companyName}`) : logger_default.error(`[\u672A\u627E\u5230\u6B64\u516C\u53F8\u4FE1\u606F] ${companyName}`);
    return register;
  }
  const [_info, _register] = await Promise.all([
    requestObj("/get_company_info", {
      company_name: _companyName
    }, messageCallback),
    getCompanyRegisterByCompanyName(_companyName, messageCallback)
  ]);
  if (_info) {
    delete _info["\u7ECF\u8425\u8303\u56F4"];
    logger_default.success(`[\u6210\u529F\u627E\u5230\u516C\u53F8\u4FE1\u606F] ${_companyName}`);
    return Object.assign(_info, _register || {});
  }
  if (!_register)
    logger_default.error(`[\u672A\u627E\u5230\u6B64\u516C\u53F8\u4FE1\u606F] ${_companyName}`);
  logger_default.success(`[\u6210\u529F\u627E\u5230\u516C\u53F8\u4FE1\u606F] ${_companyName}`);
  return _register;
}
async function getCompanyInfoByStockCode(stockCode, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u80A1\u7968\u4EE3\u7801\u67E5\u8BE2\u516C\u53F8\u540D\u79F0] ${stockCode}`);
  const companyName = await searchCompanyNameByInfo({ "\u516C\u53F8\u4EE3\u7801": stockCode.trim() }, messageCallback);
  if (!companyName) {
    logger_default.error(`[\u672A\u627E\u5230\u80A1\u7968\u4EE3\u7801\u4E3A${stockCode}\u7684\u516C\u53F8]`);
    return null;
  }
  const result = await getCompanyInfoByCompanyName(companyName, messageCallback);
  if (!result)
    logger_default.error(`[\u672A\u627E\u5230\u80A1\u7968\u4EE3\u7801\u4E3A${stockCode}\u7684\u516C\u53F8]`);
  else
    logger_default.success(`[\u5DF2\u627E\u5230\u80A1\u7968\u4EE3\u7801\u4E3A${stockCode}\u7684\u516C\u53F8] ${companyName}`);
  return result;
}
async function getCompanyInfoByRegisterCode(registerCode, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u6CE8\u518C\u53F7\u67E5\u8BE2\u516C\u53F8\u540D\u79F0] ${registerCode}`);
  const companyName = await searchCompanyNameByRegister({ "\u6CE8\u518C\u53F7": registerCode.trim() }, messageCallback);
  if (!companyName) {
    logger_default.error(`[\u672A\u627E\u5230\u6CE8\u518C\u53F7\u4E3A${registerCode}\u7684\u516C\u53F8]`);
    return null;
  }
  const result = await getCompanyInfoByCompanyName(companyName, messageCallback);
  if (!result)
    logger_default.error(`[\u672A\u627E\u5230\u6CE8\u518C\u53F7\u4E3A${registerCode}\u7684\u516C\u53F8]`);
  else
    logger_default.success(`[\u5DF2\u627E\u5230\u6CE8\u518C\u53F7\u4E3A${registerCode}\u7684\u516C\u53F8] ${companyName}`);
  return result;
}
async function getCompanyInfoListTextByIndustry(industry, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u6240\u5C5E\u884C\u4E1A\u67E5\u8BE2\u516C\u53F8\u540D\u79F0] ${industry}`);
  const companyNames = await searchCompanyNamesByInfo({
    "\u6240\u5C5E\u884C\u4E1A": industry.trim()
  }, messageCallback);
  if (companyNames.length == 0) {
    logger_default.error(`[\u672A\u627E\u5230\u5F52\u5C5E${industry}\u884C\u4E1A\u7684\u516C\u53F8]`);
    return [];
  }
  let infos = [];
  let tasks = [];
  while (infos.length != companyNames.length) {
    const name = companyNames[infos.length + tasks.length];
    if (tasks.length < Math.min(LAW_API_CONCURRENT, companyNames.length - infos.length)) {
      tasks.push(getCompanyInfoByCompanyName(name, messageCallback));
      continue;
    }
    infos = infos.concat((await Promise.all(tasks)).filter((v) => v));
    tasks = [];
  }
  logger_default.success(`[\u5DF2\u627E\u5230\u5F52\u5C5E${industry}\u884C\u4E1A\u7684\u516C\u53F8] ${infos.length}\u5BB6`);
  return infos;
}
async function searchCompanyNameByInfo(options, messageCallback) {
  const result = await requestObj("/search_company_name_by_info", optionsConvert(options), messageCallback);
  if (!result)
    return null;
  return result["\u516C\u53F8\u540D\u79F0"];
}
async function searchCompanyNamesByInfo(options, messageCallback) {
  const list = await requestList("/search_company_name_by_info", optionsConvert(options), messageCallback);
  return list.map((v) => v["\u516C\u53F8\u540D\u79F0"]);
}
async function getCompanyRegisterByCompanyName(companyName, messageCallback) {
  return await requestObj("/get_company_register", {
    company_name: companyName.trim()
  }, messageCallback);
}
async function searchCompanyNameByRegister(options, messageCallback) {
  const result = await requestObj("/search_company_name_by_register", optionsConvert(options), messageCallback);
  if (!result)
    return null;
  return result["\u516C\u53F8\u540D\u79F0"];
}
async function getSubCompanyInfoListByCompanyName(companyName, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u6BCD\u516C\u53F8\u540D\u79F0\u67E5\u8BE2\u5B50\u516C\u53F8\u4FE1\u606F] ${companyName}`);
  let subCompanyNames = (await Promise.all([
    searchSubCompanyNamesBySubInfo({ "\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u5168\u79F0": companyName }, messageCallback),
    searchSubCompanyNamesBySubInfo({ "\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u80A1\u7968\u7B80\u79F0": companyName }, messageCallback)
  ])).reduce((arr, v) => [...arr, ...v], []);
  if (subCompanyNames.length == 0) {
    const companyInfo = await getCompanyInfoByCompanyName(companyName, messageCallback);
    if (!companyInfo) {
      logger_default.error(`[\u672A\u627E\u5230${companyName}\u7684\u5B50\u516C\u53F8]`);
      return [];
    }
    subCompanyNames = await searchSubCompanyNamesBySubInfo({ "\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u5168\u79F0": companyInfo["\u516C\u53F8\u540D\u79F0"] }, messageCallback);
    if (subCompanyNames.length == 0) {
      logger_default.error(`[\u672A\u627E\u5230${companyName}\u7684\u5B50\u516C\u53F8]`);
      return [];
    }
  }
  let infos = [];
  let tasks = [];
  while (infos.length != subCompanyNames.length) {
    const name = subCompanyNames[infos.length + tasks.length];
    if (tasks.length < Math.min(LAW_API_CONCURRENT, subCompanyNames.length - infos.length)) {
      tasks.push(getSubCompanyInfoBySubCompanyName(name, messageCallback));
      continue;
    }
    infos = infos.concat((await Promise.all(tasks)).filter((v) => v));
    tasks = [];
  }
  logger_default.success(`[\u5DF2\u627E\u5230${companyName}\u7684\u5B50\u516C\u53F8] ${infos.length}\u5BB6`);
  return infos;
}
async function getSubCompanyInfoBySubCompanyName(subCompanyName, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u5B50\u516C\u53F8\u540D\u79F0\u67E5\u8BE2\u5B50\u516C\u53F8\u4FE1\u606F] ${subCompanyName}`);
  const result = await requestObj("/get_sub_company_info", {
    company_name: subCompanyName.trim().trim()
  }, messageCallback);
  if (!result)
    logger_default.error(`[\u672A\u627E\u5230\u6B64\u5B50\u516C\u53F8\u4FE1\u606F] ${subCompanyName}`);
  else
    logger_default.success(`[\u5DF2\u627E\u5230\u5B50\u516C\u53F8\u4FE1\u606F] ${subCompanyName}`);
  return result;
}
async function searchSubCompanyNamesBySubInfo(options, messageCallback) {
  const list = await requestList("/search_company_name_by_sub_info", optionsConvert(options), messageCallback);
  return list.map((v) => v["\u516C\u53F8\u540D\u79F0"]);
}
async function getLegalDocumentByCaseNum(caseNum, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u6848\u53F7\u67E5\u8BE2\u6CD5\u5F8B\u6587\u4E66] ${caseNum}`);
  const result = await requestObj("/get_legal_document", {
    case_num: caseNum.trim().replace("\uFF08", "(").replace("\uFF09", ")")
  }, messageCallback);
  if (!result)
    logger_default.error(`[\u672A\u627E\u5230\u6848\u53F7${caseNum}\u7684\u6CD5\u5F8B\u6587\u4E66]`);
  else
    logger_default.success(`[\u5DF2\u627E\u5230\u6848\u53F7${caseNum}\u7684\u6CD5\u5F8B\u6587\u4E66]`);
  return result;
}
async function getLegalDocumentListByReason(reason, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u6848\u7531\u67E5\u8BE2\u6CD5\u5F8B\u6587\u4E66] ${reason}`);
  const caseNums = await searchCaseNumByLegalDocument({
    "\u6848\u7531": reason.trim()
  }, messageCallback);
  if (caseNums.length == 0) {
    logger_default.error(`[\u672A\u627E\u5230\u6848\u7531\u4E3A${reason}\u7684\u6CD5\u5F8B\u6587\u4E66]`);
    return [];
  }
  let docs = [];
  let tasks = [];
  while (docs.length != caseNums.length) {
    const caseNum = caseNums[docs.length + tasks.length];
    if (tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
      tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
      continue;
    }
    docs = docs.concat((await Promise.all(tasks)).filter((v) => v));
    tasks = [];
  }
  logger_default.success(`[\u5DF2\u627E\u5230\u6848\u7531\u4E3A${reason}\u7684\u6CD5\u5F8B\u6587\u4E66] ${docs.length}\u4EF6`);
  return docs;
}
async function getLegalDocumentListByPlaintiff(plaintiff, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u539F\u544A\u67E5\u8BE2\u6CD5\u5F8B\u6587\u4E66] ${plaintiff}`);
  const caseNums = await searchCaseNumByLegalDocument({
    "\u539F\u544A": plaintiff.trim()
  }, messageCallback);
  if (caseNums.length == 0) {
    logger_default.error(`[\u672A\u627E\u5230\u539F\u544A\u4E3A${plaintiff}\u7684\u6CD5\u5F8B\u6587\u4E66]`);
    return [];
  }
  let docs = [];
  let tasks = [];
  while (docs.length != caseNums.length) {
    const caseNum = caseNums[docs.length + tasks.length];
    if (tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
      tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
      continue;
    }
    docs = docs.concat((await Promise.all(tasks)).filter((v) => v));
    tasks = [];
  }
  logger_default.success(`[\u5DF2\u627E\u5230\u539F\u544A\u4E3A${plaintiff}\u7684\u6CD5\u5F8B\u6587\u4E66] ${docs.length}\u4EF6`);
  return docs;
}
async function getLegalDocumentListByDefendant(defendant, messageCallback) {
  logger_default.info(`[\u6B63\u901A\u8FC7\u88AB\u544A\u67E5\u8BE2\u6CD5\u5F8B\u6587\u4E66] ${defendant}`);
  const caseNums = await searchCaseNumByLegalDocument({
    "\u88AB\u544A": defendant.trim()
  }, messageCallback);
  if (caseNums.length == 0) {
    logger_default.error(`[\u672A\u627E\u5230\u88AB\u544A\u4E3A${defendant}\u7684\u6CD5\u5F8B\u6587\u4E66]`);
    return [];
  }
  let docs = [];
  let tasks = [];
  while (docs.length != caseNums.length) {
    const caseNum = caseNums[docs.length + tasks.length];
    if (tasks.length < Math.min(LAW_API_CONCURRENT, caseNums.length - docs.length)) {
      tasks.push(getLegalDocumentByCaseNum(caseNum, messageCallback));
      continue;
    }
    docs = docs.concat((await Promise.all(tasks)).filter((v) => v));
    tasks = [];
  }
  logger_default.success(`[\u5DF2\u627E\u5230\u88AB\u544A\u4E3A${defendant}\u7684\u6CD5\u5F8B\u6587\u4E66] ${docs.length}\u4EF6`);
  return docs;
}
async function searchCaseNumByLegalDocument(options, messageCallback) {
  const list = await requestList("/search_case_num_by_legal_document", optionsConvert(options), messageCallback);
  return list.map((v) => v["\u6848\u53F7"]);
}
function optionsConvert(options) {
  let _options = {};
  for (let key in options) {
    _options.key = key;
    _options.value = options[key];
  }
  return _options;
}
async function requestObj(url, data = {}, messageCallback) {
  const result = await request(url, data, messageCallback);
  if (_9.isArray(result)) {
    if (!result[0])
      return null;
    return result[0];
  }
  return result;
}
async function requestList(url, data = {}, messageCallback) {
  const result = await request(url, data, messageCallback);
  if (_9.isArray(result))
    return result;
  return [];
}
async function request(url, data = {}, messageCallback) {
  console.log(`[\u8C03\u7528\u63A5\u53E3] ${url} ${JSON.stringify(data)}`);
  messageCallback({ type: 4 /* RequestAPI */, title: "\u{1F310} \u8C03\u7528\u5916\u90E8API", data: { method: "POST", url, data } });
  const result = await axios2.request({
    method: "POST",
    url: `${LAW_API_ENDPOINT}${url}`,
    data,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${LAW_API_TOKEN}`
    }
  });
  if (result.status != 200)
    throw new Error(`Request failed: [${result.status}]${result.statusText || "Unknown"}`);
  messageCallback({ type: 4 /* RequestAPI */, title: "\u{1F310} \u8C03\u7528\u5916\u90E8API", data: result.data, finish: true });
  return result.data;
}
async function webSearch(content) {
  logger_default.info(`[\u6B63\u5728\u7F51\u7EDC\u68C0\u7D22] ${content}`);
  const result = await axios2.request({
    method: "POST",
    url: `${WEB_SEARCH_ENDPOINT}/chat/completions`,
    data: {
      model: WEB_SEARCH_MODEL,
      messages: [
        {
          "role": "user",
          "content": `\u8BF7\u68C0\u7D22\u95EE\u9898\u5E76\u63D0\u4F9B\u5B8C\u6574\u7B54\u6848\uFF1A${content}`
        }
      ]
    },
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${WEB_SEARCH_TOKEN}`
    }
  });
  if (result.status != 200)
    throw new Error(`Request failed: [${result.status}]${result.statusText || "Unknown"}`);
  if (!result.data || !result.data.choices || !result.data.choices[0])
    throw new Error(`Request failed: [${result.data.code}]${result.data.message}`);
  logger_default.success(`[\u5B8C\u6210\u7F51\u7EDC\u68C0\u7D22] ${content}`);
  return result.data.choices[0].message.content;
}
var api_default = {
  getCompanyInfoByCompanyName,
  getCompanyInfoByStockCode,
  getCompanyInfoByRegisterCode,
  getCompanyInfoListTextByIndustry,
  getSubCompanyInfoListByCompanyName,
  getSubCompanyInfoBySubCompanyName,
  getLegalDocumentByCaseNum,
  getLegalDocumentListByReason,
  getLegalDocumentListByPlaintiff,
  getLegalDocumentListByDefendant,
  webSearch
};

// src/lib/tools.ts
import _10 from "lodash";
var TOOLS = {
  getCompanyInfoTextByCompanyName,
  getCompanyInfoTextByStockCode,
  getCompanyInfoTextByRegisterCode,
  getCompanyInfoListTextByIndustry: getCompanyInfoListTextByIndustry2,
  getSubCompanyInfoListTextByCompanyName,
  getSubCompanyInfoTextBySubCompanyName,
  getParentCompanyInfoTextBySubCompanyName,
  getLegalDocumentTextByCaseNum,
  getLegalDocumentListTextByReason,
  getLegalDocumentListTextByPlaintiff,
  getLegalDocumentListTextByDefendant,
  calculate
};
async function toolCallDistribution(name, args = {}, messageCallback) {
  logger_default.info(`[\u8C03\u7528\u5DE5\u5177${name}]`, args);
  if (Object.keys(args).length == 0) {
    logger_default.error(`[\u8C03\u7528\u5DE5\u5177${name}\u65F6\u672A\u63D0\u4F9B\u4EFB\u4F55\u53C2\u6570]`);
    return `\u8C03\u7528\u5DE5\u5177${name}\u5FC5\u987B\u63D0\u4F9B\u5408\u6CD5\u7684\u53C2\u6570\uFF0C\u8BF7\u68C0\u67E5\u91CD\u8BD5\u3002`;
  }
  if (!TOOLS[name]) {
    logger_default.error(`[\u672A\u627E\u5230${name}\u5DE5\u5177]`);
    return `\u5DE5\u5177${name}\u672A\u627E\u5230\uFF0C\u8BF7\u68C0\u67E5\u5DE5\u5177\u540D\u79F0\u91CD\u8BD5\u3002`;
  }
  const result = await TOOLS[name](args, messageCallback);
  logger_default.success(`[\u5DE5\u5177${name}\u8C03\u7528\u6210\u529F]`);
  return result;
}
async function getCompanyInfoTextByCompanyName({ companyName }, messageCallback) {
  let info = await api_default.getCompanyInfoByCompanyName(companyName, messageCallback);
  if (!info)
    return `\u672A\u627E\u5230${companyName}\u7684\u516C\u53F8\u4FE1\u606F\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  info = companyInfoFilter(info, ["\u516C\u53F8\u540D\u79F0"]);
  let text = `\u5DF2\u67E5\u627E\u5230${companyName}\u7684\u516C\u53F8\u4FE1\u606F\uFF1A

`;
  for (let key in info)
    text += `${key}\uFF1A${info[key] || "\u65E0\u6570\u636E"}
`;
  text += `
\u4EE5\u4E0A\u4FE1\u606F\u4E0D\u5305\u542B\u6BCD\u516C\u53F8\u4FE1\u606F\uFF0C\u5982\u9700\u6BCD\u516C\u53F8\u4FE1\u606F\u53EF\u4EE5\u8C03\u7528getParentCompanyInfoTextBySubCompanyName\u5DE5\u5177\u83B7\u53D6\u3002`;
  return text;
}
async function getCompanyInfoTextByStockCode({ stockCode }, messageCallback) {
  let info = await api_default.getCompanyInfoByStockCode(stockCode, messageCallback);
  if (!info)
    return `\u672A\u627E\u5230\u516C\u53F8\u4EE3\u7801\uFF08\u80A1\u7968\u4EE3\u7801\uFF09\u4E3A${stockCode}\u7684\u516C\u53F8\u4FE1\u606F\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  info = companyInfoFilter(info);
  let text = `\u5DF2\u67E5\u627E\u5230\u516C\u53F8\u4EE3\u7801\uFF08\u80A1\u7968\u4EE3\u7801\uFF09\u4E3A${stockCode}\u7684\u516C\u53F8\u4FE1\u606F\uFF1A

`;
  for (let key in info)
    text += `${key}\uFF1A${info[key] || "\u65E0\u6570\u636E"}
`;
  return text;
}
async function getCompanyInfoTextByRegisterCode({ registerCode }, messageCallback) {
  let info = await api_default.getCompanyInfoByRegisterCode(registerCode, messageCallback);
  if (!info)
    return `\u672A\u627E\u5230\u6CE8\u518C\u53F7\u4E3A${registerCode}\u7684\u516C\u53F8\u4FE1\u606F`;
  info = companyInfoFilter(info, ["\u6CE8\u518C\u53F7"]);
  let text = `\u5DF2\u67E5\u627E\u5230\u6CE8\u518C\u53F7\u4E3A${registerCode}\u7684\u516C\u53F8\u4FE1\u606F\uFF1A

`;
  for (let key in info)
    text += `${key}\uFF1A${info[key] || "\u65E0\u6570\u636E"}
`;
  return text;
}
async function getCompanyInfoListTextByIndustry2({ industry }, messageCallback) {
  const infos = await api_default.getCompanyInfoListTextByIndustry(industry, messageCallback);
  if (!infos.length)
    return `\u672A\u627E\u5230\u5F52\u5C5E\u884C\u4E1A\u4E3A${industry}\u7684\u516C\u53F8\u4FE1\u606F\u5217\u8868\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  let text = "";
  infos.sort((a, b) => amountParse(b["\u6CE8\u518C\u8D44\u672C"]) - amountParse(a["\u6CE8\u518C\u8D44\u672C"]));
  text += `\u6240\u5C5E\u884C\u4E1A\u4E3A${industry}\u7684\u5B50\u516C\u53F8\u5171\u6709${infos.length}\u5BB6\uFF0C\u6CE8\u518C\u8D44\u672C\u524D3\u7684\u516C\u53F8\u4E3A\uFF1A` + infos.slice(0, 3).map((v) => `${v["\u516C\u53F8\u540D\u79F0"]}\uFF08${v["\u6CE8\u518C\u8D44\u672C"] ? v["\u6CE8\u518C\u8D44\u672C"] + "\u4E07\u5143" : "\u65E0\u6570\u636E"}\uFF09`).join("\u3001");
  return text;
}
async function getSubCompanyInfoListTextByCompanyName({ companyName, excessInvestmentAmount, isHolding, isWhollyOwned }, messageCallback) {
  let infos = await api_default.getSubCompanyInfoListByCompanyName(companyName, messageCallback);
  if (!infos.length)
    return `\u672A\u627E\u5230\u5F52\u5C5E\u4E8E${companyName}\u7684\u5B50\u516C\u53F8\u4FE1\u606F\u5217\u8868\uFF0C\u4E5F\u8BB8\u4F60\u63D0\u4F9B\u7684\u662F\u4E00\u5BB6\u5B50\u516C\u53F8\u540D\u79F0\uFF0C\u4F60\u53EF\u4EE5\u5C1D\u8BD5\u8C03\u7528getParentCompanyInfoTextBySubCompanyName\u83B7\u53D6\u5176\u6BCD\u516C\u53F8\u4FE1\u606F\uFF0C\u8BF7\u91CD\u8BD5\u3002`;
  const totalCount = infos.length;
  const totalInvestmentAmount = infos.reduce((total, v) => Math.ceil(total + amountParse(v["\u4E0A\u5E02\u516C\u53F8\u6295\u8D44\u91D1\u989D"])), 0);
  const listContent = "| \u516C\u53F8\u540D\u79F0 | \u53C2\u80A1\u6BD4\u4F8B | \u6295\u8D44\u91D1\u989D |\n| --- | --- | --- |\n" + infos.reduce((str, v) => str += `| ${v["\u516C\u53F8\u540D\u79F0"]} | ${v["\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"] ? v["\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"] + "%" : "\u65E0\u6570\u636E"} | ${v["\u4E0A\u5E02\u516C\u53F8\u6295\u8D44\u91D1\u989D"] || "\u65E0\u6570\u636E"} |
`, "");
  let maxShareholdingRatio = 0;
  let maxShareholdingCompanyNames = [];
  let holdingInfos = [];
  if (isHolding) {
    holdingInfos = infos.filter((v) => {
      const ratio = Number(v["\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"]) || 0;
      if (ratio > maxShareholdingRatio) {
        maxShareholdingRatio = ratio;
        maxShareholdingCompanyNames = [];
      }
      if (ratio == maxShareholdingRatio)
        maxShareholdingCompanyNames.push(v["\u516C\u53F8\u540D\u79F0"]);
      return ratio > 50;
    });
  }
  let whollyOwnedInfos = [];
  if (isWhollyOwned) {
    whollyOwnedInfos = infos.filter((v) => {
      const ratio = Number(v["\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"]) || 0;
      return ratio == 100;
    });
  }
  let maxInvestmentAmount = 0;
  let maxInvestmentAmountCompanyNames = [];
  let excessInvestmentAmountInfos = [];
  const _excessInvestmentAmount = amountParse(excessInvestmentAmount || "0");
  const targetInfos = isHolding ? holdingInfos : isWhollyOwned ? whollyOwnedInfos : infos;
  excessInvestmentAmountInfos = targetInfos.filter((v) => {
    const amount = amountParse(v["\u4E0A\u5E02\u516C\u53F8\u6295\u8D44\u91D1\u989D"]);
    if (amount > maxInvestmentAmount) {
      maxInvestmentAmount = amount;
      maxInvestmentAmountCompanyNames = [];
    }
    if (amount == maxInvestmentAmount)
      maxInvestmentAmountCompanyNames.push(v["\u516C\u53F8\u540D\u79F0"]);
    return amount > _excessInvestmentAmount;
  });
  return [
    listContent,
    `\u4EE5\u4E0A\u662F${companyName}\u7684\u5B50\u516C\u53F8\u5217\u8868\uFF0C\u5171\u6709${totalCount}\u5BB6\uFF0C\u6295\u8D44\u7684\u603B\u91D1\u989D\u4E3A${totalInvestmentAmount}\u4EBA\u6C11\u5E01;`,
    `\u53C2\u80A1\u6BD4\u4F8B\u8D85\u8FC750%\u7684${isHolding ? "\u63A7\u80A1" : ""}\u5B50\u516C\u53F8\u6709${holdingInfos.length}\u5BB6` + (isWhollyOwned ? `\uFF0C\u5176\u4E2D\u5168\u8D44\u5B50\u516C\u53F8\u6709${whollyOwnedInfos.length}\u5BB6;` : ";"),
    excessInvestmentAmount ? `${isHolding || isWhollyOwned ? "\u5176\u4E2D\uFF0C" : ""}\u6295\u8D44\u91D1\u989D\u8D85\u8FC7${excessInvestmentAmount}\u7684\u6709${excessInvestmentAmountInfos.length}\u5BB6;` : "",
    `${isHolding ? "\u63A7\u80A1\u5B50\u516C\u53F8\u4E2D" : "\u5B50\u516C\u53F8\u4E2D"}\u53C2\u80A1\u6BD4\u4F8B\u6700\u9AD8\u7684\u6709\uFF1A${maxShareholdingCompanyNames.join("\u3001")}; \u53C2\u80A1\u6BD4\u4F8B\u6700\u9AD8\u8FBE\u5230${maxShareholdingRatio.toFixed(2)}%;`,
    `${isHolding ? "\u63A7\u80A1\u5B50\u516C\u53F8\u4E2D" : "\u5B50\u516C\u53F8\u4E2D"}\u6295\u8D44\u91D1\u989D\u6700\u9AD8\u7684\u6709\uFF1A${maxInvestmentAmountCompanyNames.join("\u3001")}; \u6295\u8D44\u91D1\u989D\u6700\u9AD8\u8FBE\u5230${Math.ceil(maxInvestmentAmount)}\u4EBA\u6C11\u5E01\u3002`
  ].join("\n");
}
async function getSubCompanyInfoTextBySubCompanyName({ subCompanyName }, messageCallback) {
  let info = await api_default.getSubCompanyInfoBySubCompanyName(subCompanyName, messageCallback);
  if (!info)
    return `\u672A\u627E\u5230${subCompanyName}\u4FE1\u606F`;
  info = subCompanyInfoFilter(info, ["\u516C\u53F8\u540D\u79F0"]);
  let text = `\u5DF2\u67E5\u627E\u5230\u8BE5${subCompanyName}\u4FE1\u606F\uFF1A

`;
  for (let key in info)
    text += `${key}\uFF1A${info[key] || "\u65E0\u6570\u636E"}
`;
  return text;
}
async function getParentCompanyInfoTextBySubCompanyName({ subCompanyName }, messageCallback) {
  const info = await api_default.getSubCompanyInfoBySubCompanyName(subCompanyName, messageCallback);
  if (!info)
    return "\u672A\u627E\u5230\u8BE5\u5B50\u516C\u53F8\u4FE1\u606F\uFF0C\u65E0\u6CD5\u83B7\u5F97\u5173\u8054\u6BCD\u516C\u53F8\u4FE1\u606F";
  const parentCompanyName = info["\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u5168\u79F0"] || info["\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u80A1\u7968\u7B80\u79F0"];
  let parentInfo = await api_default.getCompanyInfoByCompanyName(parentCompanyName, messageCallback);
  parentInfo = companyInfoFilter(parentInfo);
  let text = `\u5DF2\u67E5\u627E\u5230${subCompanyName}\u7684\u6BCD\u516C\u53F8\u4FE1\u606F\uFF1A

`;
  for (let key in parentInfo)
    text += `${key}\uFF1A${parentInfo[key] || "\u65E0\u6570\u636E"}
`;
  text += `
${subCompanyName}\u662F${parentInfo["\u516C\u53F8\u540D\u79F0"]}\u7684\u5B50\u516C\u53F8`;
  return text;
}
async function getLegalDocumentTextByCaseNum({ caseNum }, messageCallback) {
  let doc = await api_default.getLegalDocumentByCaseNum(caseNum, messageCallback);
  if (!doc)
    return `\u672A\u627E\u5230\u6848\u53F7\u4E3A${caseNum}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\uFF0C\u6709\u53EF\u80FD\u7F3A\u5931\u62EC\u53F7\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  doc = legalDocumentFilter(doc, ["\u6848\u53F7"]);
  let text = `\u5DF2\u67E5\u627E\u5230\u6848\u53F7\u4E3A${caseNum}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\uFF1A

`;
  for (let key in doc)
    text += `${key}\uFF1A${doc[key] || "\u65E0\u6570\u636E"}
`;
  return text;
}
async function getLegalDocumentListTextByReason({ reason }, messageCallback) {
  const docs = await api_default.getLegalDocumentListByReason(reason, messageCallback);
  if (!docs.length)
    return `\u672A\u627E\u5230\u6848\u7531\u4E3A${reason}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5185\u5BB9\u5217\u8868\uFF0C\u53EF\u80FD\u4E3A0\u4EF6\u3002`;
  let text = `\u5DF2\u67E5\u627E\u5230\u6848\u7531\u4E3A${reason}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5217\u8868\uFF08\u5171${docs.length}\u4EF6\uFF09\uFF1A

`;
  for (let i = 0; i < docs.length; i++) {
    const doc = legalDocumentFilter(docs[i], ["\u6848\u7531"]);
    text += `${i + 1}.${doc["\u6807\u9898"] || "\u672A\u77E5\u6848\u4EF6"}
`;
    delete doc["\u6807\u9898"];
    for (let key in doc) {
      text += `   ${key}\uFF1A${doc[key] || "\u65E0\u6570\u636E"}
`;
    }
    text += "\n";
  }
  text += `
\u4EE5\u4E0A${docs.length}\u4EF6\u6CD5\u5F8B\u6587\u4E66\u6848\u4EF6\u7684\u6848\u7531\u90FD\u662F${reason}`;
  return text;
}
async function getLegalDocumentListTextByPlaintiff({ plaintiff }, messageCallback) {
  const docs = await api_default.getLegalDocumentListByPlaintiff(plaintiff, messageCallback);
  if (!docs.length)
    return `\u672A\u627E\u5230\u539F\u544A\u4E3A${plaintiff}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5185\u5BB9\u5217\u8868\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  let text = `\u5DF2\u67E5\u627E\u5230\u539F\u544A\u4E3A${plaintiff}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5185\u5BB9\u5217\u8868\uFF08\u5171${docs.length}\u4EF6\uFF09\uFF1A

`;
  const lawOfficeCounts = {};
  for (let i = 0; i < docs.length; i++) {
    const doc = legalDocumentFilter(docs[i], ["\u539F\u544A"]);
    text += `${i + 1}.${doc["\u6807\u9898"] || "\u672A\u77E5\u6848\u4EF6"}
`;
    delete doc["\u6807\u9898"];
    if (doc["\u539F\u544A\u5F8B\u5E08"]) {
      const lawOffices = lawOfficesExtract(doc["\u539F\u544A\u5F8B\u5E08"]);
      lawOffices.forEach((name) => lawOfficeCounts[name] ? lawOfficeCounts[name]++ : lawOfficeCounts[name] = 1);
    }
    for (let key in doc) {
      text += `   ${key}\uFF1A${doc[key] || "\u65E0\u6570\u636E"}
`;
    }
    text += "\n";
  }
  const lawOfficesDetail = Object.entries(lawOfficeCounts).reduce((str, v) => str + `${v[0]}\uFF1A${v[1]}\u6B21
`, "");
  text += `
${plaintiff}\u662F\u4EE5\u4E0A${docs.length}\u4EF6\u6CD5\u5F8B\u6587\u4E66\u6848\u4EF6\u7684\u539F\u544A\u3002` + (lawOfficesDetail ? `
\u539F\u544A\u5408\u4F5C\u7684\u4E8B\u52A1\u6240\u9891\u6B21\u5982\u4E0B\uFF1A
${lawOfficesDetail}\u3002` : "\u539F\u544A\u6CA1\u6709\u548C\u5F8B\u5E08\u4E8B\u52A1\u6240\u5408\u4F5C\uFF0C\u5408\u4F5C\u6B21\u6570\u4E3A0\u3002");
  return text;
}
async function getLegalDocumentListTextByDefendant({ defendant }, messageCallback) {
  const docs = await api_default.getLegalDocumentListByDefendant(defendant, messageCallback);
  if (!docs)
    return `\u672A\u627E\u5230\u88AB\u544A\u4E3A${defendant}\u7684\u6CD5\u5F8B\u6587\u4E66\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  if (!docs.length)
    return `\u672A\u627E\u5230\u88AB\u544A\u4E3A${defendant}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5185\u5BB9\u5217\u8868\uFF0C\u8BF7\u68C0\u67E5\u540E\u91CD\u8BD5\u3002`;
  let text = `\u5DF2\u67E5\u627E\u5230\u88AB\u544A\u4E3A${defendant}\u7684\u5386\u53F2\u6CD5\u5F8B\u6587\u4E66\u5185\u5BB9\u5217\u8868\uFF08\u5171${docs.length}\u4EF6\uFF09\uFF1A

`;
  const lawOfficeCounts = {};
  for (let i = 0; i < docs.length; i++) {
    const doc = legalDocumentFilter(docs[i], ["\u88AB\u544A"]);
    text += `${i + 1}.${doc["\u6807\u9898"] || "\u672A\u77E5\u6848\u4EF6"}
`;
    delete doc["\u6807\u9898"];
    if (doc["\u88AB\u544A\u5F8B\u5E08"]) {
      const lawOffices = lawOfficesExtract(doc["\u88AB\u544A\u5F8B\u5E08"]);
      lawOffices.forEach((name) => lawOfficeCounts[name] ? lawOfficeCounts[name]++ : lawOfficeCounts[name] = 1);
    }
    for (let key in doc) {
      text += `   ${key}\uFF1A${doc[key] || "\u65E0\u6570\u636E"}
`;
    }
    text += "\n";
  }
  const lawOfficesDetail = Object.entries(lawOfficeCounts).reduce((str, v) => str + `${v[0]}\uFF1A${v[1]}\u6B21
`, "");
  text += `
${defendant}\u662F\u4EE5\u4E0A${docs.length}\u4EF6\u6CD5\u5F8B\u6587\u4E66\u6848\u4EF6\u7684\u88AB\u544A\u3002` + (lawOfficesDetail ? `
b\u88AB\u544A\u5408\u4F5C\u7684\u4E8B\u52A1\u6240\u9891\u6B21\u5982\u4E0B\uFF1A
${lawOfficesDetail}\u3002` : "\u88AB\u544A\u6CA1\u6709\u548C\u5F8B\u5E08\u4E8B\u52A1\u6240\u5408\u4F5C\uFF0C\u5408\u4F5C\u6B21\u6570\u4E3A0\u3002");
  return text;
}
function companyInfoFilter(info, fields = []) {
  info = _10.omit(info, [
    "\u5173\u8054\u8BC1\u5238",
    "\u516C\u53F8\u4EE3\u7801",
    "\u6240\u5C5E\u5E02\u573A",
    "\u5B98\u65B9\u7F51\u5740",
    "\u5165\u9009\u6307\u6570",
    "\u7ECF\u8425\u8303\u56F4",
    "\u673A\u6784\u7B80\u4ECB",
    "\u6BCF\u80A1\u9762\u503C",
    ...fields
  ]);
  return companyRegisterFilter(info);
}
function companyRegisterFilter(register, fields = []) {
  return _10.omit(register, [
    "\u53C2\u4FDD\u4EBA\u6570",
    "\u7701\u4EFD",
    "\u57CE\u5E02",
    "\u533A\u53BF",
    ...fields
  ]);
}
function subCompanyInfoFilter(info, fields = []) {
  info["\u6BCD\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"] = info["\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B"];
  info["\u6BCD\u516C\u53F8\u6295\u8D44\u91D1\u989D"] = info["\u4E0A\u5E02\u516C\u53F8\u6295\u8D44\u91D1\u989D"];
  return _10.omit(info, [
    "\u5173\u8054\u4E0A\u5E02\u516C\u53F8\u80A1\u7968\u4EE3\u7801",
    "\u4E0A\u5E02\u516C\u53F8\u5173\u7CFB",
    "\u4E0A\u5E02\u516C\u53F8\u53C2\u80A1\u6BD4\u4F8B",
    "\u4E0A\u5E02\u516C\u53F8\u6295\u8D44\u91D1\u989D",
    ...fields
  ]);
}
function legalDocumentFilter(doc, fields = []) {
  return _10.omit(doc, [
    "\u6587\u4E66\u7C7B\u578B",
    "\u6587\u4EF6\u540D",
    "\u5224\u51B3\u7ED3\u679C",
    ...fields
  ]);
}
function amountParse(text) {
  if (!text)
    return 0;
  if (_10.isFinite(text))
    return Number(text);
  text = text.replace(/\>|\<|\=|\,|\，/g, "");
  let times = 1;
  if (text.includes("\u4EBF"))
    times = 1e8;
  else if (text.includes("\u5343\u4E07"))
    times = 1e7;
  else if (text.includes("\u4E07"))
    times = 1e4;
  return parseFloat(text) * times;
}
function lawOfficesExtract(text) {
  const match = text.match(/,(.+?律师事务所)/g);
  if (!match)
    return [];
  return match.map((v) => v.replace(/^,\s*/, "").trim());
}
function calculate({ nums }) {
  console.log(nums);
  return nums.reduce((total, num) => total + amountParse(num), 0);
}
var tools_default = {
  toolCallDistribution,
  ...TOOLS
};

// src/lib/llm.ts
import OpenAI from "openai";
import _11 from "lodash";
var MODEL = config_default.zhipuai.model || "glm-4-0520";
var ENDPOINT = config_default.zhipuai.endpoint;
var API_KEY = config_default.zhipuai.api_key;
var MAX_TOKENS = config_default.zhipuai.max_tokens;
var client = new OpenAI({
  baseURL: ENDPOINT,
  apiKey: API_KEY
});
async function questionClassify(question, categorys, usageCallback) {
  logger_default.info(`[\u6B63\u5728\u5206\u7C7B\u95EE\u9898] ${question}`);
  const categorysDescription = categorys.reduce((str, v) => str + `${v[0]}\uFF1A${v[1]}
`, "");
  const result = await chatCompletions([
    {
      "role": "system",
      "content": `\u4F60\u662F\u4E00\u4E2A\u6CD5\u5F8B\u95EE\u9898\u5206\u7C7B\u52A9\u624B\uFF0C\u9700\u8981\u6839\u636E\u7528\u6237\u8F93\u5165\u5224\u65AD\u5B83\u5C5E\u4E8E\u4EE5\u4E0B\u54EA\u4E00\u4E2A\u5206\u7C7B\uFF1A
${categorysDescription}
\u8BF7\u76F4\u63A5\u8F93\u51FA\u5206\u7C7B\u540D\u79F0\uFF0C\u4E0D\u9700\u8981\u89E3\u91CA\u3002
\u901A\u5E38\u53EA\u9700\u8981\u4E00\u4E2A\u5206\u7C7B\uFF0C\u9664\u975E\u95EE\u9898\u660E\u786E\u6D89\u53CA\u591A\u4E2A\u5206\u7C7B\u624D\u63D0\u4F9B\u591A\u4E2A\uFF0C\u8BF7\u4F7F\u7528\u82F1\u6587\u9017\u53F7\u9694\u5F00\u5B83\u4EEC\u3002`
      // "content": `你是一个法律问题分类助手，需要根据用户输入判断它属于以下哪一个分类，如果问题明确涉及多个分类请使用英文逗号隔开：\n[${categorys.join(',')}]`
    },
    {
      "role": "user",
      "content": `\u95EE\u9898\uFF1A${question}

\u5206\u7C7B\uFF1A`
    }
  ], usageCallback);
  const choices = [];
  for (let v of categorys) {
    if (result.includes(v[0]))
      choices.push(v[0]);
  }
  if (choices.length == 0)
    logger_default.error(`[\u6B64\u95EE\u9898\u65E0\u6CD5\u5224\u65AD\u5206\u7C7B] ${question}`);
  else
    logger_default.success(`[\u95EE\u9898\u5206\u7C7B\u5B8C\u6210] ${choices.join("\u3001")}`);
  return choices;
}
async function consultingLegalConcept(question, history = [], afterContent = "", usageCallback) {
  logger_default.info(`[\u6B63\u5728\u54A8\u8BE2\u6CD5\u5F8B\u6761\u6587] ${question}`);
  const result = await toolCalls([
    {
      "role": "system",
      "content": `\u4F60\u662F\u4E00\u4E2A\u6CD5\u5F8B\u6761\u6587\u7B54\u9898\u52A9\u624B\uFF0C\u9700\u8981\u6839\u636E\u7528\u6237\u63D0\u4F9B\u7684\u95EE\u9898\uFF0C\u7CBE\u786E\u5B8C\u6574\u7684\u63D0\u4F9B\u4E00\u4EFD\u6807\u51C6\u7684\u7B54\u6848\uFF0C\u4E0D\u9700\u8981\u8F93\u51FA\u63D0\u793A\u8BED\u548C\u6CE8\u610F\u4E8B\u9879\uFF0C\u4EFB\u4F55\u9898\u76EE\u90FD\u9700\u8981\u4F5C\u7B54\uFF0C\u5982\u679C\u6570\u636E\u4E3A0\u4E5F\u8BF7\u5982\u5B9E\u56DE\u7B54\u3002`
    },
    ...history,
    {
      "role": "user",
      "content": `\u8BF7\u7CBE\u786E\u5B8C\u6574\u7684\u56DE\u7B54\u6B64\u95EE\u9898\uFF1A${question}
${afterContent}

\u7B54\u6848\uFF1A`
    }
  ], [], usageCallback);
  logger_default.success(`[\u6CD5\u5F8B\u6761\u6587\u54A8\u8BE2\u5B8C\u6210]`);
  return result;
}
async function consultingCompanyInfo(question, history = [], afterContent = "", disableToolNames = [], usageCallback) {
  logger_default.info(`[\u6B63\u5728\u54A8\u8BE2\u516C\u53F8\u4FE1\u606F] ${question}`);
  const result = await toolCalls([
    {
      "role": "system",
      "content": `\u4F60\u662F\u4E00\u4E2A\u516C\u53F8\u4FE1\u606F\u7B54\u9898\u52A9\u624B\uFF0C\u4F60\u80FD\u591F\u8C03\u7528\u5DE5\u5177\u67E5\u8BE2\u4E00\u5BB6\u6216\u591A\u5BB6\u516C\u53F8\u7684\u57FA\u672C\u4FE1\u606F\u3001\u6CE8\u518C\u4FE1\u606F\u3001\u884C\u4E1A\u4FE1\u606F\u3001\u5B50\u516C\u53F8\u4FE1\u606F\u3001\u5B50\u516C\u53F8\u7684\u6BCD\u516C\u53F8\u4FE1\u606F\u7B49\u6765\u7CBE\u51C6\u5B8C\u6574\u7684\u63D0\u4F9B\u4F60\u7684\u7B54\u6848\u3002
\u4E0D\u9700\u8981\u8F93\u51FA\u63D0\u793A\u8BED\u548C\u6CE8\u610F\u4E8B\u9879\u3002`
    },
    ...history,
    {
      "role": "user",
      "content": `
\u8BF7\u7CBE\u786E\u5B8C\u6574\u7684\u56DE\u7B54\u6B64\u95EE\u9898\uFF1A${question}

\u5982\u679C\u4E0A\u6587\u5B58\u5728\u672A\u67E5\u8BE2\u5230\u7684\u6570\u636E\u4F60\u53EF\u4EE5\u7EE7\u7EED\u8C03\u7528\u5DE5\u5177
${afterContent}

\u7B54\u6848\uFF1A`
    }
  ], [
    {
      "type": "function",
      "function": {
        "name": "getCompanyInfoTextByCompanyName",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u516C\u53F8\u540D\u79F0\u6216\u7B80\u79F0\u6216\u82F1\u6587\u540D\u79F0\uFF0C\u67E5\u8BE2\u8BE5\u516C\u53F8\u7684\u57FA\u672C\u4FE1\u606F\u548C\u6CE8\u518C\u4FE1\u606F",
        "parameters": {
          "type": "object",
          "properties": {
            "companyName": {
              "type": "string",
              "description": "\u516C\u53F8\u540D\u79F0\u6216\u7B80\u79F0\u6216\u82F1\u6587\u540D\u79F0"
            }
          },
          "required": ["companyName"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getCompanyInfoTextByRegisterCode",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u516C\u53F8\u6CE8\u518C\u53F7\uFF0C\u67E5\u8BE2\u8BE5\u516C\u53F8\u7684\u57FA\u672C\u4FE1\u606F\u548C\u6CE8\u518C\u4FE1\u606F",
        "parameters": {
          "type": "object",
          "properties": {
            "registerCode": {
              "type": "string",
              "description": "\u516C\u53F8\u6CE8\u518C\u53F7"
            }
          },
          "required": ["registerCode"]
        }
      }
    },
    // {
    //     "type": "function",
    //     "function": {
    //         "name": "getCompanyInfoTextByStockCode",
    //         "description": "根据提供的公司代码（股票代码）查询该公司的基本信息和注册信息",
    //         "parameters": {
    //             "type": "object",
    //             "properties": {
    //                 "stockCode": {
    //                     "type": "string",
    //                     "description": "公司代码（股票代码）",
    //                 }
    //             },
    //             "required": ["stockCode"],
    //         },
    //     }
    // },
    {
      "type": "function",
      "function": {
        "name": "getCompanyInfoListTextByIndustry",
        "description": "\u67E5\u8BE2\u6240\u5C5E\u8BE5\u884C\u4E1A\u7684\u516C\u53F8\u5217\u8868\uFF0C\u6839\u636E\u63D0\u4F9B\u7684\u884C\u4E1A\u540D\u79F0\uFF0C\u53EF\u4EE5\u83B7\u5F97\u5305\u542B\u6BCF\u5BB6\u516C\u53F8\u7684\u57FA\u672C\u4FE1\u606F\u548C\u6CE8\u518C\u4FE1\u606F\u5217\u8868",
        "parameters": {
          "type": "object",
          "properties": {
            "industry": {
              "type": "string",
              "description": "\u884C\u4E1A\u540D\u79F0"
            }
          },
          "required": ["industry"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getParentCompanyInfoTextBySubCompanyName",
        "description": "\u67E5\u8BE2\u6BCD\u516C\u53F8\u7684\u4FE1\u606F\uFF0C\u6839\u636E\u63D0\u4F9B\u7684\u5B50\u516C\u53F8\u540D\u79F0\u67E5\u8BE2\u6BCD\u516C\u53F8\u6216\u63A7\u80A1\u516C\u53F8\u7684\u516C\u53F8\u4FE1\u606F\uFF0C\u65B9\u4FBF\u83B7\u53D6\u5B50\u516C\u53F8\u5C5E\u4E8E\u54EA\u4E2A\u516C\u53F8\u65D7\u4E0B\u3002",
        "parameters": {
          "type": "object",
          "properties": {
            "subCompanyName": {
              "type": "string",
              "description": "\u5B50\u516C\u53F8\u540D\u79F0"
            }
          },
          "required": ["subCompanyName"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getSubCompanyInfoListTextByCompanyName",
        "description": "\u67E5\u8BE2\u5B50\u516C\u53F8\u4FE1\u606F\u5217\u8868\uFF0C\u6839\u636E\u63D0\u4F9B\u7684\u516C\u53F8\u540D\u79F0\u6216\u7B80\u79F0\u6216\u82F1\u6587\u540D\u79F0\uFF0C\u53EF\u4EE5\u83B7\u5F97\u8BE5\u516C\u53F8\u7684\u6240\u6709\u5B50\u516C\u53F8\u4FE1\u606F\u5217\u8868",
        "parameters": {
          "type": "object",
          "properties": {
            "companyName": {
              "type": "string",
              "description": "\u516C\u53F8\u540D\u79F0"
            },
            "excessInvestmentAmount": {
              "type": "string",
              "description": "\u6BCD\u516C\u53F8\u6295\u8D44\u5B50\u516C\u53F8\u8D85\u8FC7\u7684\u91D1\u989D\uFF0C\u5305\u542B\u5355\u4F4D\uFF08\u59825000\u4E07\uFF09"
            },
            "isHolding": {
              "type": "boolean",
              "description": "\u662F\u5426\u67E5\u8BE2\u63A7\u80A1\u516C\u53F8\uFF08\u53C2\u80A1\u6BD4\u4F8B\u8D85\u8FC750%\u7684\u516C\u53F8\uFF09"
            },
            "isWhollyOwned": {
              "type": "boolean",
              "description": "\u662F\u5426\u67E5\u8BE2\u5168\u8D44\u5B50\u516C\u53F8\uFF08\u53C2\u80A1\u6BD4\u4F8B\u4E3A100%\u7684\u516C\u53F8\uFF09"
            }
          },
          "required": ["companyName", "isHolding", "isWhollyOwned"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getSubCompanyInfoTextBySubCompanyName",
        "description": "\u6839\u636E\u5B50\u516C\u53F8\u540D\u79F0\u67E5\u8BE2\u5B50\u516C\u53F8\u7684\u4FE1\u606F\uFF0C\u53EF\u4EE5\u67E5\u8BE2\u5B50\u516C\u53F8\u5173\u8054\u7684\u6BCD\u516C\u53F8\u540D\u79F0\u548C\u6BCD\u516C\u53F8\u5BF9\u8BE5\u5B50\u516C\u53F8\u7684\u6295\u8D44\u91D1\u989D\u3001\u53C2\u80A1\u6BD4\u4F8B\u3001\u63A7\u80A1\u60C5\u51B5\u7B49",
        "parameters": {
          "type": "object",
          "properties": {
            "subCompanyName": {
              "type": "string",
              "description": "\u5B50\u516C\u53F8\u540D\u79F0"
            }
          },
          "required": ["subCompanyName"]
        }
      }
    }
    // {
    //     "type": "function",
    //     "function": {
    //         "name": "calculate",
    //         "description": "加法计算器，可用于统计总投资金额，单位是元。",
    //         "parameters": {
    //             "type": "object",
    //             "properties": {
    //                 "nums": {
    //                     "type": "array",
    //                     "description": "金额列表",
    //                 }
    //             },
    //             "required": ["nums"],
    //         },
    //     }
    // }
  ].filter((f) => !disableToolNames.includes(f.function.name)), usageCallback);
  logger_default.success(`[\u516C\u53F8\u4FE1\u606F\u54A8\u8BE2\u5B8C\u6210]`);
  return result;
}
async function consultingLegalDocument(question, history = [], afterContent = "", disableToolNames = [], usageCallback) {
  logger_default.info(`[\u6B63\u5728\u54A8\u8BE2\u6CD5\u5F8B\u6587\u4E66] ${question}`);
  const result = await toolCalls([
    {
      "role": "system",
      "content": `\u4F60\u662F\u4E00\u4E2A\u6CD5\u5F8B\u6587\u4E66\u7B54\u9898\u52A9\u624B\uFF0C\u4F60\u80FD\u591F\u8C03\u7528\u5DE5\u5177\u6839\u636E\u6848\u53F7\u7B49\u4FE1\u606F\u67E5\u8BE2\u76F8\u5E94\u6CD5\u5F8B\u6587\u4E66\u7684\u5185\u5BB9\u6216\u5224\u51B3\u7684\u6CD5\u5F8B\u6761\u6587\u4F9D\u636E\u7B49\uFF0C\u5E76\u6839\u636E\u9898\u76EE\u8981\u6C42\uFF0C\u7CBE\u786E\u5B8C\u6574\u7684\u63D0\u4F9B\u4E00\u4EFD\u6807\u51C6\u7684\u7B54\u6848\uFF0C\u4E0D\u9700\u8981\u8F93\u51FA\u63D0\u793A\u8BED\u548C\u6CE8\u610F\u4E8B\u9879\u3002`
    },
    ...history,
    {
      "role": "user",
      "content": `
\u8BF7\u7CBE\u786E\u5B8C\u6574\u7684\u56DE\u7B54\u6B64\u95EE\u9898\uFF1A${question}

\u5982\u679C\u4E0A\u6587\u5B58\u5728\u672A\u67E5\u8BE2\u5230\u7684\u6570\u636E\u4F60\u53EF\u4EE5\u7EE7\u7EED\u8C03\u7528\u5DE5\u5177
${afterContent}

\u7B54\u6848\uFF1A`
    }
  ], [
    {
      "type": "function",
      "function": {
        "name": "getLegalDocumentTextByCaseNum",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u6848\u53F7\u67E5\u8BE2\u8BE5\u6CD5\u5F8B\u6587\u4E66\u6216\u67E5\u8BE2\u5224\u51B3\u7684\u6CD5\u5F8B\u6761\u6587\u4F9D\u636E",
        "parameters": {
          "type": "object",
          "properties": {
            "caseNum": {
              "type": "string",
              "description": "\u6848\u53F7"
            }
          },
          "required": ["caseNum"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getLegalDocumentListTextByReason",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u6848\u7531\uFF0C\u67E5\u8BE2\u8BE5\u6848\u7531\u7684\u6CD5\u5F8B\u6587\u4E66\u5217\u8868",
        "parameters": {
          "type": "object",
          "properties": {
            "reason": {
              "type": "string",
              "description": "\u6848\u7531"
            }
          },
          "required": ["reason"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getLegalDocumentListTextByPlaintiff",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u539F\u544A\uFF0C\u67E5\u8BE2\u51FA\u73B0\u8BE5\u539F\u544A\u7684\u6CD5\u5F8B\u6587\u4E66\u5217\u8868\uFF0C\u9762\u4E34\u8BC9\u8BBC\u65F6\u516C\u53F8\u5C06\u662F\u539F\u544A",
        "parameters": {
          "type": "object",
          "properties": {
            "plaintiff": {
              "type": "string",
              "description": "\u539F\u544A\u540D\u79F0"
            }
          },
          "required": ["plaintiff"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "getLegalDocumentListTextByDefendant",
        "description": "\u6839\u636E\u63D0\u4F9B\u7684\u88AB\u544A\uFF0C\u67E5\u8BE2\u51FA\u73B0\u8BE5\u88AB\u544A\u7684\u6CD5\u5F8B\u6587\u4E66\u5217\u8868",
        "parameters": {
          "type": "object",
          "properties": {
            "defendant": {
              "type": "string",
              "description": "\u88AB\u544A\u540D\u79F0"
            }
          },
          "required": ["defendant"]
        }
      }
    }
  ].filter((f) => !disableToolNames.includes(f.function.name)), usageCallback);
  logger_default.success(`[\u6CD5\u5F8B\u6587\u4E66\u54A8\u8BE2\u5B8C\u6210]`);
  return result;
}
async function checkTaskCompleted(question, answer, history = [], rounds, usageCallback) {
  if (!answer)
    return { completed: false, explain: "" };
  logger_default.info(`[\u6B63\u5728\u68C0\u67E5\u4EFB\u52A1\u662F\u5426\u5DF2\u5B8C\u6210] \u7B2C${rounds}\u8F6E`);
  const result = await chatCompletions([
    ...history,
    {
      "role": "user",
      "content": `\u95EE\u9898\uFF1A\u5E2E\u6211\u67E5\u4E00\u4E0B\u5065\u5E06\u751F\u7269\u79D1\u6280\u96C6\u56E2\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u7684\u884C\u4E1A\u5F52\u5C5E\uFF0C\u5E76\u544A\u77E5\u8BE5\u884C\u4E1A\u5185\u7684\u4F01\u4E1A\u603B\u6570\u662F\u591A\u5C11\uFF1F
\u56DE\u7B54\uFF1A\u5065\u5E06\u751F\u7269\u79D1\u6280\u96C6\u56E2\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u7684\u884C\u4E1A\u5F52\u5C5E\u662F\u4E13\u7528\u8BBE\u5907\u5236\u9020\u4E1A\uFF0C\u8BE5\u884C\u4E1A\u5185\u7684\u4F01\u4E1A\u603B\u6570\u4E3A62\u5BB6\u3002

\u5B8C\u6574\u5EA6\uFF1A100%
\u5DF2\u5B8C\u6210\uFF1Ayes
\u5F85\u8865\u5145\u4FE1\u606F\uFF1A\u65E0

\u4EE5\u4E0A\u662F\u4EFB\u52A1\u68C0\u67E5\u6837\u4F8B\u3002

\u4F60\u662F\u4E00\u4E2A\u4EFB\u52A1\u5B8C\u6210\u72B6\u6001\u68C0\u67E5\u52A9\u624B\uFF0C\u4F60\u4E0D\u9700\u8981\u5173\u6CE8\u7B54\u6848\u6B63\u786E\u7387\uFF0C\u4EC5\u4ECE\u7B54\u9898\u5B8C\u6574\u6027\u5165\u624B\uFF0C\u4F60\u4F1A\u5148\u8BC4\u4F30\u5E76\u8F93\u51FA\u4E00\u4E2A\u5B8C\u6574\u5EA6\uFF0C\u5F53\u5B8C\u6574\u5EA6\u9AD8\u4E8E50%\u65F6\u518D\u662F\u5426\u5B8C\u6210\u4F4D\u7F6E\u8F93\u51FA\u201Cyes\u201D\uFF0C\u5426\u5219\u5728\u662F\u5426\u5B8C\u6210\u4F4D\u7F6E\u8F93\u51FA\u201Cno\u201D\u5E76\u5728\u5F85\u8865\u5145\u4FE1\u606F\u4F4D\u7F6E\u63D0\u4F9B\u7B54\u6848\u7F3A\u5931\u7684\u4FE1\u606F\u3002

\u793A\u4F8B\u8F93\u51FA\uFF1A
\u5B8C\u6574\u5EA6\uFF1A{\u5B8C\u6574\u5EA6}
\u5DF2\u5B8C\u6210\uFF1A{\u662F\u5426\u5B8C\u6210}
\u5F85\u8865\u5145\u4FE1\u606F\uFF1A{\u5F85\u8865\u5145\u4FE1\u606F\u6216\u65E0}

\uFF0C\u53EA\u9700\u5173\u6CE8\u662F\u5426\u6709\u67D0\u4E9B\u6570\u636E\u6CA1\u6709\u67E5\u8BE2\u5230\u6216\u6570\u503C\u4E0D\u660E\u786E\u3002

\u95EE\u9898\uFF1A${question}\u3002
\u56DE\u7B54\uFF1A${answer}\u3002`
    }
  ], usageCallback, "glm-4-0520");
  const completed = result.toLowerCase().includes("yes");
  completed ? logger_default.success(`[\u4EFB\u52A1\u5DF2\u5B8C\u6210] \u7B2C${rounds}\u8F6E`) : logger_default.warn(`[\u4EFB\u52A1\u672A\u5B8C\u6210\uFF0C\u5373\u5C06\u91CD\u8BD5] \u7B2C${rounds}\u8F6E`);
  return {
    completed,
    explain: result
  };
}
async function infoExtract(question, content, usageCallback) {
  logger_default.info("[\u6B63\u5728\u62BD\u53D6\u4FE1\u606F]");
  let result = await chatCompletions([
    {
      "role": "system",
      "content": "\u4F60\u662F\u4E00\u4E2A\u53C2\u8003\u5185\u5BB9\u5173\u952E\u4FE1\u606F\u63D0\u53D6\u52A9\u624B\uFF0C\u4F60\u7684\u76EE\u6807\u662F\u63D0\u53D6\u548C\u9898\u76EE\u76F8\u5173\u7684\u4FE1\u606F\u4F46\u4E0D\u6539\u5199\u4E0D\u7F29\u5199\u4FE1\u606F\u5185\u5BB9\u3002\n\u4ECE\u63D0\u4F9B\u7684\u53C2\u8003\u5185\u5BB9\u4E2D\u63D0\u53D6\u4E0E\u9898\u76EE\u76F8\u5173\u7684\u4FE1\u606F\u5E76\u5B8C\u6574\u5217\u51FA\uFF0C\u4F60\u4E0D\u9700\u8981\u56DE\u7B54\u9898\u76EE\uFF0C\u4E0D\u80FD\u7F3A\u5931\u9898\u76EE\u9700\u8981\u7684\u5173\u952E\u4FE1\u606F\u3002"
    },
    {
      "role": "user",
      "content": `${content}

\u4EE5\u4E0A\u4E3A\u53C2\u8003\u5185\u5BB9\u3002

\u9898\u76EE\uFF1A${question}\u3002

\u6CE8\u610F\uFF0C\u4F60\u4E0D\u9700\u8981\u56DE\u7B54\u9898\u76EE\uFF0C\u63D0\u53D6\u5230\u7684\u4FE1\u606F\uFF08\u5982\u679C\u90E8\u5206\u4FE1\u606F\u672A\u627E\u5230\u65E0\u9700\u5217\u51FA\uFF09\uFF1A
`
    }
  ], usageCallback);
  return result;
}
async function answerRephrase(question, answer, usageCallback) {
  logger_default.info("[\u6B63\u5728\u603B\u7ED3\u590D\u8FF0\u7B54\u6848]");
  let result = await chatCompletions([
    {
      "role": "system",
      "content": "Q: \u6211\u60F3\u4E86\u89E3\u91CD\u5E86\u83B1\u7F8E\u836F\u4E1A\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u7684\u6CE8\u518C\u72B6\u51B5\u3001\u4F01\u4E1A\u7C7B\u522B\u4EE5\u53CA\u6210\u7ACB\u65E5\u671F\u3002\nA: \u91CD\u5E86\u83B1\u7F8E\u836F\u4E1A\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u7684\u6CE8\u518C\u72B6\u51B5\u4E3A\u5B58\u7EED\uFF0C\u4F01\u4E1A\u7C7B\u522B\u662F\u80A1\u4EFD\u6709\u9650\u516C\u53F8\uFF08\u4E0A\u5E02\u516C\u53F8\uFF09\uFF0C\u6210\u7ACB\u65E5\u671F\u4E3A1999\u5E7409\u670806\u65E5\u3002\n\nQ: \u6211\u60F3\u4E86\u89E306865 \u798F\u83B1\u7279\u73BB\u7483\u8FD9\u4E2A\u80A1\u7968\u4EE3\u7801\u7684\u4E0A\u5E02\u516C\u53F8\u4FE1\u606F\uFF0C\u53EF\u4EE5\u63D0\u4F9B\u516C\u53F8\u7684\u82F1\u6587\u540D\u79F0\u5417\uFF1F\nA: 06865 \u798F\u83B1\u7279\u73BB\u7483\u80A1\u7968\u4EE3\u7801\u7684\u4E0A\u5E02\u516C\u53F8\u7684\u82F1\u6587\u540D\u79F0\u662FFlat Glass Group Co., Ltd.\u3002\n\nQ: \u6211\u60F3\u4E86\u89E3\u5316\u5B66\u539F\u6599\u548C\u5316\u5B66\u5236\u54C1\u5236\u9020\u4E1A\u8FD9\u4E2A\u884C\u4E1A\u7684\u516C\u53F8\u6709\u54EA\u4E9B\uFF0C\u8BF7\u5217\u51FA\u6CE8\u518C\u8D44\u672C\u6700\u5927\u76843\u5BB6\u5934\u90E8\u516C\u53F8\uFF0C\u5E76\u7ED9\u51FA\u4ED6\u4EEC\u7684\u5177\u4F53\u6CE8\u518C\u8D44\u672C\u6570\u989D\nA: \u5728\u5316\u5B66\u539F\u6599\u548C\u5316\u5B66\u5236\u54C1\u5236\u9020\u4E1A\u884C\u4E1A\u4E2D\uFF0C\u5934\u90E8\u76843\u5BB6\u516C\u53F8\u5206\u522B\u662F\u6D59\u6C5F\u9F99\u76DB\u96C6\u56E2\u80A1\u4EFD\u6709\u9650\u516C\u53F8, \u9633\u7164\u5316\u5DE5\u80A1\u4EFD\u6709\u9650\u516C\u53F8, \u5317\u4EAC\u6D77\u65B0\u80FD\u6E90\u79D1\u6280\u80A1\u4EFD\u6709\u9650\u516C\u53F8\uFF0C\u5B83\u4EEC\u7684\u6CE8\u518C\u8D44\u672C\u5206\u522B\u4E3A325333.186, 237598.1952, 234972.0302\u3002\n\nQ: \u4E0A\u6D77\u5BB6\u5316\u8054\u5408\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u4E3A\u539F\u544A\u65F6\u4ED6\u4E3B\u8981\u548C\u54EA\u5BB6\u5F8B\u5E08\u4E8B\u52A1\u6240\u5408\u4F5C?\u5408\u4F5C\u6B21\u6570\u4E3A\u51E0\u6B21\u3002\nA: \u4E0A\u6D77\u5BB6\u5316\u8054\u5408\u80A1\u4EFD\u6709\u9650\u516C\u53F8\u4E3B\u8981\u548C\u6D59\u6C5F\u82E5\u5C48\u5F8B\u5E08\u4E8B\u52A1\u6240\u5F8B\u5E08\u5408\u4F5C\uFF0C\u5408\u4F5C\u4E8611\u6B21\u3002\n\n\u53C2\u8003\u4EE5\u4E0A\u5BF9\u8BDD\u4F8B\u5B50\u4E2DAnswer\u7684\u56DE\u590D\u98CE\u683C, \u91CD\u65B0\u590D\u8FF0(rephrase)\u4EE5\u4E0B\u95EE\u7B54\u4E2D\u7684A\uFF0C\u6CE8\u610F:\n- \u56DE\u7B54\u7B80\u8981\u5207\u9898, \u8F93\u51FA\u4E00\u884C\u56DE\u7B54\u4E0D\u6362\u884C\uFF0C\u4F7F\u7528\u4E2D\u6587\n- \u95EE\u9898\u6D89\u53CA\u7684\u540D\u8BCD\u3001\u5173\u952E\u8BCD\u3001\u82F1\u6587\u3001\u6570\u5B57\u8981\u5B8C\u6574\u586B\u5199\uFF0C\u4E0D\u7F29\u5199\u4E0D\u6539\u5199\u4FE1\u606F\uFF0C\u4E0D\u80FD\u9057\u6F0F\u5173\u952E\u4FE1\u606F\n- \u590D\u8FF0\u90E8\u5206\u95EE\u9898\u5185\u5BB9\u7B49"
    },
    {
      "role": "user",
      "content": `Q\uFF1A${question}\u3002
A\uFF1A${answer}\uFF08\u5B8C\u6574\u590D\u8FF0\u548C\u5217\u51FA\u5185\u5BB9\uFF09\u3002

\u76F4\u63A5\u63D0\u4F9B\u7B54\u6848\u5B8C\u6574\u590D\u8FF0\uFF0C\u4E0D\u7F29\u5199\u4E0D\u6539\u5199\uFF0C\u4E0D\u5141\u8BB8\u7701\u7565\u516C\u53F8\u540D\u79F0\u7B49\u4FE1\u606F\u3002\u4EE5\u4E0B\u662F\u590D\u8FF0\uFF1A`
    }
  ], usageCallback);
  result = result.replace(/Q(:|：).+\n*A(:|：)\s?/, "").replace(/A(:|：)\s?/, "").replace(/写\n/, "").replace(/^(,|，)/, "");
  return result;
}
async function communication(question, usageCallback) {
  logger_default.info("[\u6B63\u5728\u65E5\u5E38\u6C9F\u901A\u4EA4\u6D41]");
  const result = await chatCompletions([
    {
      "role": "system",
      "content": "\u4F60\u662F\u4E00\u4E2A\u4E13\u4E1A\u7684\u6CD5\u5F8B\u52A9\u624B\uFF0C\u540D\u5B57\u662FGLM\u6CD5\u5F8B\u987E\u95EE\uFF0C\u9700\u8981\u4E25\u8C28\u53EF\u9760\u7684\u56DE\u7B54\u7528\u6237\u7684\u4EFB\u4F55\u95EE\u9898\u3002"
    },
    {
      "role": "user",
      "content": question
    }
  ], usageCallback);
  return result;
}
async function chatCompletions(messages, usageCallback, model) {
  const response = await client.chat.completions.create({
    model: model || MODEL,
    messages,
    tools: [
      {
        "type": "web_search",
        "web_search": {
          "enable": false
        }
      }
    ],
    tool_choice: "auto",
    max_tokens: MAX_TOKENS
  });
  if (!response.choices || !response.choices[0])
    throw new Error("LLM response error");
  if (usageCallback && response.usage && _11.isFinite(response.usage.total_tokens))
    usageCallback(response.usage.total_tokens);
  return response.choices[0].message.content;
}
async function toolCalls(messages, tools = [], usageCallback, model) {
  tools.push({
    "type": "web_search",
    "web_search": {
      "enable": false
    }
  });
  const response = await client.chat.completions.create({
    model: model || MODEL,
    messages,
    tools,
    tool_choice: "auto",
    max_tokens: MAX_TOKENS
  });
  if (!response.choices || !response.choices[0])
    throw new Error("LLM response error");
  if (usageCallback && response.usage && _11.isFinite(response.usage.total_tokens))
    usageCallback(response.usage.total_tokens);
  const callResults = response.choices[0].message.tool_calls || [];
  return {
    content: response.choices[0].message.content || null,
    calls: callResults.filter((v) => v.type == "function").map((v) => {
      const { id, function: _function } = v;
      const { name, arguments: argsJson } = _function;
      const args = _11.attempt(() => JSON.parse(argsJson));
      return {
        id,
        name,
        args: !_11.isError(args) ? args : {}
      };
    })
  };
}
var llm_default = {
  questionClassify,
  consultingLegalConcept,
  consultingCompanyInfo,
  consultingLegalDocument,
  infoExtract,
  checkTaskCompleted,
  answerRephrase,
  communication
};

// src/lib/question.ts
var MAX_ROUNDS = config_default.task.max_rounds;
var MAX_RETRY_ROUNDS = config_default.task.max_retry_rounds;
var QUESTION_CATEGORYS = [
  ["\u516C\u53F8\u4FE1\u606F", "\u67E5\u8BE2\u6307\u5B9A\u516C\u53F8\u7684\u57FA\u672C\u4FE1\u606F\u3001\u6CE8\u518C\u4FE1\u606F\u3001\u5B50\u516C\u53F8\u7B49\u76F8\u5173\u4FE1\u606F"],
  [
    "\u5386\u53F2\u6848\u4EF6",
    "\u6839\u636E\u6848\u53F7\u3001\u6848\u7531\u3001\u539F\u544A\u88AB\u544A\u7B49\u4FE1\u606F\u67E5\u8BE2\u6CD5\u5F8B\u6587\u4E66\u5386\u53F2\u6848\u4EF6\uFF0C\u67E5\u8BE2\u6848\u4EF6\u7684\u5224\u51B3\u6240\u4F9D\u636E\u7684\u6CD5\u5F8B\u6761\u6587\uFF0C\u67E5\u8BE2\u5F8B\u5E08\u4E8B\u52A1\u6240\u6CD5\u5F8B\u4EE3\u7406\u7B49\u4FE1\u606F\u7B49"
  ],
  ["\u6CD5\u5F8B\u6761\u6587", "\u67E5\u8BE2\u6CD5\u5F8B\u6982\u5FF5\u6216\u4E86\u89E3\u6CD5\u6761\u5185\u5BB9"],
  ["\u65E5\u5E38\u804A\u5929", "\u7528\u6237\u53EF\u80FD\u53EA\u662F\u60F3\u8DDF\u4F60\u804A\u4E24\u53E5"]
];
async function getQuestions(filename) {
  const raw = (await fs4.readFile(filename)).toString();
  const list = raw.split("\n");
  if (list[list.length - 1].trim() == "") list.pop();
  return list.map((v) => JSON.parse(v));
}
async function generateAnswer(question, messageCallback) {
  messageCallback = messageCallback || (() => {
  });
  let rounds = 0;
  let retryRounds = 0;
  let latestToolCallTemp;
  let latestAnswer = "";
  let classifys;
  let answers = [];
  let totalTokens = 0;
  let afterContent = "";
  let history = [];
  let disableToolNames = [];
  let toolCallLog = "";
  while (true) {
    if (rounds++ >= MAX_ROUNDS) break;
    if (answers.length > 0 && answers.filter((v) => v.content).length == answers.length) {
      const allAnswer = answers.reduce(
        (str, v, i) => `${str}${v.content}

`,
        ""
      );
      messageCallback({ type: 2 /* Consulting */, title: "\u270D\uFE0F \u4F18\u5316\u7B54\u6848" });
      latestAnswer = await llm_default.answerRephrase(
        question,
        allAnswer,
        (tokens) => totalTokens += tokens
      );
      console.log(`\u9636\u6BB5\u6027\u7B54\u6848\uFF1A${latestAnswer}`);
      messageCallback({
        type: 2 /* Consulting */,
        title: "\u270D\uFE0F \u4F18\u5316\u7B54\u6848",
        data: latestAnswer,
        finish: true
      });
      messageCallback({ type: 2 /* Consulting */, title: "\u{1F50D} \u68C0\u67E5\u7B54\u6848" });
      const { completed, explain } = await llm_default.checkTaskCompleted(
        question,
        latestAnswer,
        history,
        retryRounds,
        (tokens) => totalTokens += tokens
      );
      if (!completed) {
        if (++retryRounds >= MAX_RETRY_ROUNDS) break;
        messageCallback({
          type: 2 /* Consulting */,
          title: "\u{1F50D} \u68C0\u67E5\u7B54\u6848",
          data: `\u7B54\u6848\u68C0\u67E5\u4E0D\u901A\u8FC7\uFF1A${explain}`,
          error: true
        });
        latestToolCallTemp = void 0;
        history = [];
        history.push({
          role: "user",
          content: `${latestAnswer}

\u4EE5\u4E0A\u7B54\u6848\u4E0D\u5B8C\u6574\uFF0C\u8BF7\u4F7F\u7528\u5DE5\u5177\u6765\u67E5\u8BE2\u5B8C\u5584\uFF01
\u76EE\u524D\u7F3A\u5931\u4FE1\u606F\uFF1A
${explain}`
        });
        logger_default.warn(`[\u4E0D\u5B8C\u6574\u7684\u7B54\u6848] ${latestAnswer}`);
        logger_default.warn(`[\u65B0\u4E00\u8F6E\u4EFB\u52A1\u63D0\u793A] ${explain}`);
        classifys = void 0;
        answers = [];
        continue;
      }
      messageCallback({
        type: 2 /* Consulting */,
        title: "\u{1F50D} \u68C0\u67E5\u7B54\u6848",
        data: "\u68C0\u67E5\u901A\u8FC7",
        finish: true
      });
      break;
    }
    if (!classifys) {
      messageCallback({ type: 1 /* Classify */, title: "\u{1F500} \u95EE\u9898\u5206\u7C7B" });
      classifys = await llm_default.questionClassify(
        question,
        QUESTION_CATEGORYS,
        (tokens) => totalTokens += tokens
      );
      messageCallback({
        type: 1 /* Classify */,
        title: "\u{1F500} \u95EE\u9898\u5206\u7C7B",
        data: classifys,
        finish: true
      });
    }
    if (classifys.length == 0) {
      classifys = void 0;
      continue;
    }
    answers = [];
    for (let classify of classifys) {
      let answer;
      switch (classify) {
        case "\u6CD5\u5F8B\u6761\u6587":
          if (!history[history.length - 1] || history[history.length - 1].role != "tool")
            messageCallback({
              type: 2 /* Consulting */,
              title: "\u{1F4DA}\uFE0F \u54A8\u8BE2\u6CD5\u5F8B\u6761\u6587"
            });
          answer = await llm_default.consultingLegalConcept(
            question,
            history,
            afterContent,
            (tokens) => totalTokens + tokens
          );
          answer.content && messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F4DA}\uFE0F \u54A8\u8BE2\u6CD5\u5F8B\u6761\u6587",
            data: answer.content,
            finish: true
          });
          break;
        case "\u516C\u53F8\u4FE1\u606F":
          if (!history[history.length - 1] || history[history.length - 1].role != "tool")
            messageCallback({
              type: 2 /* Consulting */,
              title: "\u{1F3E2} \u54A8\u8BE2\u516C\u53F8\u4FE1\u606F"
            });
          answer = await llm_default.consultingCompanyInfo(
            question,
            history,
            afterContent,
            disableToolNames,
            (tokens) => totalTokens += tokens
          );
          answer.content && messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F3E2} \u54A8\u8BE2\u516C\u53F8\u4FE1\u606F",
            data: answer.content,
            finish: true
          });
          break;
        case "\u5386\u53F2\u6848\u4EF6":
          if (!history[history.length - 1] || history[history.length - 1].role != "tool")
            messageCallback({
              type: 2 /* Consulting */,
              title: "\u2696\uFE0F \u54A8\u8BE2\u5386\u53F2\u6848\u4EF6"
            });
          answer = await llm_default.consultingLegalDocument(
            question,
            history,
            afterContent,
            disableToolNames,
            (tokens) => totalTokens + tokens
          );
          answer.content && messageCallback({
            type: 2 /* Consulting */,
            title: "\u2696\uFE0F \u54A8\u8BE2\u5386\u53F2\u6848\u4EF6",
            data: answer.content,
            finish: true
          });
          break;
        case "\u65E5\u5E38\u804A\u5929":
          messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F600} \u56DE\u7B54\u95EE\u9898"
          });
          const result = await llm_default.communication(
            question,
            (tokens) => totalTokens + tokens
          );
          logger_default.success(`\u6D88\u8017Token\u6570\u91CF\u3010${totalTokens}\u3011`);
          messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F600} \u56DE\u7B54\u95EE\u9898",
            data: result,
            finish: true,
            tokens: totalTokens
          });
          return {
            answer: result,
            totalTokens
          };
        default:
          messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F310} \u7F51\u7EDC\u68C0\u7D22"
          });
          logger_default.warn(`[\u610F\u6599\u4E4B\u5916\u7684\u95EE\u9898\u5206\u7C7B\uFF0C\u5C06\u4F7F\u7528\u7F51\u7EDC\u68C0\u7D22] ${classify}`);
          answer = {
            content: await api_default.webSearch(question),
            calls: []
          };
          messageCallback({
            type: 2 /* Consulting */,
            title: "\u{1F310} \u7F51\u7EDC\u68C0\u7D22",
            finish: true
          });
      }
      answers.push(answer);
    }
    disableToolNames = [];
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
          logger_default.warn(
            `[\u672C\u8F6E\u5DF2\u7981\u7528${disableToolNames.join("\u3001")}\u5DE5\u5177\u9632\u6B62\u91CD\u590D\u8C03\u7528]`
          );
          afterContent = `\u5DE5\u5177\u8C03\u7528\u65E5\u5FD7\uFF1A
${toolCallLog}

\u5982\u679C\u9898\u76EE\u8FD8\u9700\u8981\u5176\u5B83\u4FE1\u606F\u8BF7\u4FEE\u6539\u53C2\u6570\u8C03\u7528\u5DE5\u5177\u67E5\u8BE2\u76F8\u5E94\u4FE1\u606F\uFF0C\u5426\u5219\u8BF7\u76F4\u63A5\u56DE\u7B54\u95EE\u9898\u3002`;
        } else {
          latestToolCallTemp = callTemp;
          messageCallback({
            type: 3 /* CallTool */,
            title: "\u{1F527} \u5DE5\u5177\u8C03\u7528",
            data: call
          });
          let toolResult = await tools_default.toolCallDistribution(
            call.name,
            call.args,
            messageCallback
          );
          toolCallLog += `\u5DF2\u8C03\u7528${call.name}\uFF0C\u53C2\u6570\uFF1A${Object.entries(
            call.args
          ).reduce((str, v) => str + v[0] + "=" + v[1] + ";", "")}
`;
          console.log(`\u5DE5\u5177\u8C03\u7528\u7ED3\u679C\uFF1A${toolResult}`);
          history.push({
            role: "tool",
            content: `\u5DE5\u5177\u67E5\u8BE2\u7ED3\u679C\uFF1A
${toolResult}`,
            tool_call_id: call.id
          });
          messageCallback({
            type: 3 /* CallTool */,
            title: "\u{1F527} \u5DE5\u5177\u8C03\u7528",
            data: toolResult,
            finish: true
          });
        }
      }
    }
  }
  if (!latestAnswer) {
    logger_default.warn(`[\u6CD5\u5F8BAPI\u65E0\u6CD5\u89E3\u51B3\u8BE5\u95EE\u9898\uFF0C\u5C06\u4F7F\u7528\u7F51\u7EDC\u68C0\u7D22]`);
    latestAnswer = await api_default.webSearch(question);
  }
  logger_default.success(`\u6D88\u8017Token\u6570\u91CF\u3010${totalTokens}\u3011`);
  return {
    answer: latestAnswer,
    totalTokens
  };
}
async function generateQuestionAnswer(param, messageCallback) {
  try {
    if (!param) throw new Error("Question param must be provided");
    let query;
    if (_12.isNumber(param)) {
      const id = Number(param);
      const questions = await getQuestions("question.jsonl");
      if (!questions[id]) throw new Error(`Question ${id} not found`);
      query = questions[id].question;
    } else query = param;
    console.log(`

\u9898\u76EE\uFF1A${query}`);
    const results = await getQuestions("result.jsonl");
    messageCallback({
      type: 0 /* Question */,
      title: "\u{1F440} \u9605\u8BFB\u95EE\u9898",
      data: query,
      finish: true
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
    await fs4.appendFile("result.jsonl", `${JSON.stringify(result)}
`);
    console.log(`\u7B54\u6848\uFF1A${answer}`);
    messageCallback({
      type: 5 /* Answer */,
      title: "\u{1F916} \u7B54\u6848\u8F93\u51FA",
      data: answer,
      finish: true,
      tokens: totalTokens
    });
    return {
      answer,
      totalTokens
    };
  } catch (err) {
    messageCallback({
      type: 2 /* Consulting */,
      title: "\u274C \u89E3\u7B54\u5931\u8D25",
      data: err.message,
      error: true
    });
  }
}
async function generateQuestionsAnswer() {
  await fs4.ensureFile("result.jsonl");
  const questions = await getQuestions("question.jsonl");
  const results = await getQuestions("result.jsonl");
  if (questions.length == results.length)
    logger_default.info("\u6240\u6709\u9898\u76EE\u5DF2\u7ECF\u5B8C\u6210\u56DE\u7B54\uFF0C\u5982\u679C\u9700\u8981\u91CD\u65B0\u56DE\u7B54\u8BF7\u5220\u9664result.jsonl");
  for (let question of questions.slice(results.length)) {
    await (async () => {
      console.log(
        `

\u9898\u76EE\uFF08${question.id + 1}/${questions.length}\uFF09\uFF1A${question.question}`
      );
      const { answer, totalTokens } = await generateAnswer(question.question);
      const result = {
        id: question.id,
        question: question.question,
        answer
      };
      await fs4.appendFile("result.jsonl", `${JSON.stringify(result)}
`);
      console.log(
        `\u7B54\u6848\uFF08${question.id + 1}/${questions.length}\uFF09\uFF1A${answer}

`
      );
    })().catch((err) => {
      const result = {
        id: question.id,
        question: question.question,
        answer: `\u95EE\u9898\u5904\u7406\u5931\u8D25\uFF1A${err.message}`
      };
      fs4.appendFile("result.jsonl", `${JSON.stringify(result)}
`);
      logger_default.error(err);
    });
  }
}
var question_default = {
  getQuestions,
  generateQuestionsAnswer,
  generateQuestionAnswer
};

// src/api/routes/index.ts
import path3 from "path";
import fs5 from "fs-extra";
import _13 from "lodash";

// src/api/controllers/question.ts
import { PassThrough } from "stream";
async function generateQuestionAnswerStream(query) {
  const transStream = new PassThrough();
  question_default.generateQuestionAnswer(query, (msg) => {
    transStream.write(`${JSON.stringify(msg)}

`);
  }).then(() => {
    transStream.end();
  }).catch((err) => {
    logger_default.error(err);
    transStream.end();
  });
  return transStream;
}
var question_default2 = {
  generateQuestionAnswerStream
};

// src/api/routes/question.ts
var question_default3 = {
  prefix: "/question",
  post: {
    "/generate_answer": async (request2) => {
      request2.validate("body.query");
      const { query } = request2.body;
      const stream = await question_default2.generateQuestionAnswerStream(query);
      return new Response(stream, {
        type: "text/event-stream"
      });
    }
  }
};

// src/api/routes/index.ts
var routes_default = [
  {
    get: {
      "/": async () => {
        return new Response("Redirect to index page", { redirect: "/index.html" });
      },
      "/(.*)": async (request2) => {
        let _path = request2.params[0];
        if (!_13.isString(_path))
          return new Response("not found", {
            type: "html",
            statusCode: 404
          });
        const ext = path3.extname(_path).substring(1);
        const filePath = path3.join("public/", _path);
        if (!await fs5.pathExists(filePath) || !(await fs5.stat(filePath)).isFile()) {
          return new Response("not found", {
            type: "html",
            statusCode: 404
          });
        }
        const { size: fileSize } = await fs5.promises.stat(filePath);
        const readStream = fs5.createReadStream(filePath);
        return new Response(readStream, {
          type: ext || "txt",
          headers: {
            "Cache-Control": "max-age=31536000"
            //对页面资源缓存设置一年有效期
          },
          size: fileSize
        });
      }
    }
  },
  question_default3
];

// src/index.ts
var cmdArgs = minimist(process.argv.slice(2));
var startupTime = performance.now();
(async () => {
  const param = cmdArgs.q;
  if (param) {
    if (param.trim() == "all")
      await question_default.generateQuestionsAnswer();
    else
      await question_default.generateQuestionAnswer(param);
    process.exit(0);
  }
  logger_default.header();
  logger_default.info("<<<< law qa server >>>>");
  logger_default.info("Process id:", process.pid);
  server_default.attachRoutes(routes_default);
  await server_default.listen();
})().then(
  () => logger_default.success(
    `Service startup completed (${Math.floor(performance.now() - startupTime)}ms)`
  )
).catch((err) => logger_default.error(err));
//# sourceMappingURL=index.js.map