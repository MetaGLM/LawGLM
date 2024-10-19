# -*- coding: utf-8 -*-
import json
import traceback
import queue
import re
from subprocess import PIPE
import time
import jupyter_client
from dataclasses import dataclass
from typing import Any
from uuid import uuid1


@dataclass
class ToolObservation:
    content_type: str
    text: str
    image_url: str | None = None
    role_metadata: str | None = None
    metadata: Any = None


IPYKERNEL = "my_kernel"  # Ensure this matches the name of your installed kernel

ANSI_ESCAPE = re.compile(r"(\x9B|\x1B\[|\u001b\[)[0-?]*[ -/]*[@-~]")
CODE = re.compile(r"```([^\n]*)\n(.*?)```")


def clean_traceback(traceback_list):
    cleaned_traceback = []
    for line in traceback_list:
        clean_line = re.sub(r"\x1b\[.*?m", "", line)
        cleaned_traceback.append(clean_line)
    return "\n".join(cleaned_traceback)


def clean_output(output_list):
    output_list = [str(i).strip() for i in output_list]
    final_output = []

    i = 0
    while i < len(output_list):
        line = output_list[i]
        if "查询结果为:" in line:
            result_part = line.split("查询结果为:")[1]
            next_lines = output_list[i + 1 : i + 3]
            contains_result = any(result_part.strip("[]") in next_line for next_line in next_lines)
            if contains_result:
                final_output.append(line)
                i += len(next_lines)
            else:
                final_output.append(line)
        else:
            final_output.append(line)
        i += 1

    return final_output


class CodeKernel:
    def __init__(
        self,
        kernel_name="kernel",
        kernel_id=None,
        kernel_config_path="",
        python_path=None,
        ipython_path=None,
        init_file_path="./startup.py",
        verbose=1,
    ):
        self.kernel_name = kernel_name
        self.kernel_id = kernel_id
        self.kernel_config_path = kernel_config_path
        self.python_path = python_path
        self.ipython_path = ipython_path
        self.init_file_path = init_file_path
        self.verbose = verbose
        self.cache_code = ""
        self.task_id = str(uuid1()).split("-", 3)[-1]
        self.cache_code_list = []

        if python_path is None and ipython_path is None:
            env = None
        else:
            env = {"PATH": self.python_path + ":$PATH", "PYTHONPATH": self.python_path}

        self.kernel_manager = jupyter_client.KernelManager(
            kernel_name=IPYKERNEL, connection_file=self.kernel_config_path, exec_files=[self.init_file_path], env=env
        )
        if self.kernel_config_path:
            self.kernel_manager.load_connection_file()
            self.kernel_manager.start_kernel(stdout=PIPE, stderr=PIPE)
        else:
            self.kernel_manager.start_kernel(stdout=PIPE, stderr=PIPE)

        self.kernel = self.kernel_manager.blocking_client()
        self.kernel.start_channels()
        print("Code kernel started.")

    def execute(self, code, add=True):
        if code.startswith("def") and code in self.cache_code:
            return "已经定义的函数，无需重复执行"
        all_msg_out = []
        self.kernel.execute(code)
        try:
            io_msg_content = self.kernel.get_iopub_msg(timeout=20)["content"]
            while True:
                msg_out = io_msg_content
                if "text" in msg_out:
                    all_msg_out.extend(msg_out["text"].split("\n"))

                elif "traceback" in msg_out:
                    # all_msg_out = clean_output(all_msg_out)
                    raw = "\n".join(all_msg_out)
                    if len(raw) > 1000:
                        msg = raw[:200] + "\n\n中间内容省略，如需查看，请缩减输出内容后重新打印\n\n" + raw[-300:]
                    else:
                        msg = raw
                    msg += clean_traceback(msg_out["traceback"])
                    msg += "请处理报错信息"

                    return msg

                try:
                    io_msg_content = self.kernel.get_iopub_msg(timeout=20)["content"]
                    if "execution_state" in io_msg_content and io_msg_content["execution_state"] == "idle":
                        break
                except queue.Empty:
                    traceback.print_exc()
                    break
            if add:
                self.cache_code += "IN:\n"
                self.cache_code += code
                self.cache_code += "\n"
                info = {"in": code, "out": all_msg_out, "task_id": self.task_id, "run_time": int(time.time())}
                with open("data/function_exe.jsonl", "a", encoding="utf8") as f:
                    f.write(json.dumps(info))
                    f.write("\n")
                self.cache_code_list.append(info)
            all_msg_out = clean_output(all_msg_out)
            raw = "\n".join(all_msg_out)
            if len(raw) > 1000:
                msg = raw[:500] + "\n\n中间内容省略，如需查看，请缩减输出内容后重新打印\n\n" + raw[-500:]
            else:
                msg = raw
            return msg
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.restart()
            self.run_code_history()
            return "代码执行超时，请重新编码"

    def run_code_history(self):
        try:
            for i in self.cache_code_list:
                self.kernel.execute(i["in"])
        except:
            pass

    def execute_interactive(self, code, verbose=False):
        shell_msg = self.kernel.execute_interactive(code)
        if shell_msg is queue.Empty:
            if verbose:
                print("Timeout waiting for shell message.")
        self.check_msg(shell_msg, verbose=verbose)

        return shell_msg

    def inspect(self, code, verbose=False):
        shell_msg = self.kernel.get_shell_msg(timeout=30)
        if shell_msg is queue.Empty:
            if verbose:
                print("Timeout waiting for shell message.")
        self.check_msg(shell_msg, verbose=verbose)

        return shell_msg

    def get_error_msg(self, msg, verbose=False) -> str | None:
        if msg["content"]["status"] == "error":
            try:
                error_msg = msg["content"]["traceback"]
            except:
                try:
                    error_msg = msg["content"]["traceback"][-1].strip()
                except:
                    error_msg = "Traceback Error"
            if verbose:
                print("Error: ", error_msg)
            return error_msg
        return None

    def check_msg(self, msg, verbose=False):
        status = msg["content"]["status"]
        if status == "ok":
            if verbose:
                print("Execution succeeded.")
        elif status == "error":
            for line in msg["content"]["traceback"]:
                if verbose:
                    print(line)

    def shutdown(self):
        self.kernel_manager.shutdown_kernel()
        print("Backend kernel shutdown.")
        self.kernel.shutdown()
        print("Code kernel shutdown.")

    def restart(self):
        self.kernel_manager.restart_kernel()

    def interrupt(self):
        self.kernel_manager.interrupt_kernel()

    def is_alive(self):
        return self.kernel.is_alive()


def run_code(python_str, code_kernel, iscode=False):
    if iscode:
        val = code_kernel.execute(python_str)
        return val

    match = re.search(r"```python(.*?)```", python_str, re.DOTALL)

    if match:
        python_str_run = match.group(1)
        python_str_run = re.sub(r"-> (str|list|dict|int|float)\s*\n", "\n", python_str_run)

        if (
            "<safe>" not in python_str
            and "假设" in python_str_run
            or "..." in python_str
            or re.search(r"\[.*# .* \.\.\..*]", python_str, re.DOTALL)
        ):
            return f"Traceback:拒绝运行代码，因怀疑其中含有假设数据,之前的代码为：```python\n{code_kernel.cache_code}\n```\n怀疑有假设变量的代码为：{python_str_run},请重新编码，不要使用假设数据"

        val = code_kernel.execute(python_str_run)
        return val
    else:
        match = re.search(r"```json(.*?)```", python_str, re.DOTALL)
        if match:
            print("json结果并未保存到代码：", match.group(1))
        return "没有使用正则表达式搜索到python代码，请使用```python ```代码输出"
