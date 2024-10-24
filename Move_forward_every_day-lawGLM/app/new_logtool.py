# -*- coding:utf-8 -*-

import threading


class VlogClass:
    _instance_lock = threading.Lock()

    # 单例模式
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            with cls._instance_lock:
                if not hasattr(cls, "_instance"):
                    cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self, vlog_level=0):
        self.prefix = ""
        self.vlog_level = vlog_level
        return

    def __getitem__(self, level=1):
        if level == 1:
            self.prefix = "VLOG_INFO:"
        elif level == 2:
            self.prefix = "VLOG_WARNNING:"
        elif level == 3:
            self.prefix = "VLOG_ERROR:"
        elif level > 3:
            self.prefix = "VLOG_BAD:"
        else:
            self.prefix = "VLOG0:"
        self.level = level
        return self

    def __call__(self, text, *args):
        if self.level >= self.vlog_level:
            print(self.prefix, text, args)
        return


VLOG_LEVEL = 2
VLOG = VlogClass(VLOG_LEVEL)
