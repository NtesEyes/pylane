# pylane

[![PyPI version](https://badge.fury.io/py/pylane.svg)](https://badge.fury.io/py/pylane)

[English](README.md)

Pylane 是一个基于gdb的python进程注入和调试工具,
通过gdb trace python进程，然后在该进程的python vm中动态地注入一段python代码，
从而对一个运行中的python进程执行一段任意的逻辑。

## 用法

![pylane_show](misc/pylane_show.gif)

使用inject命令把一个python脚本注入到目标进程：

```
pylane inject <PID> <YOUR_PYTHON_FILE>
```

使用shell命令对目标进程注入一个交互式的shell：

```
pylane shell <PID>
```

Pylane shell特性：

* 使用IPython作为交互接口，支持 ? % 等魔术方法
* 支持完整的远程自动补全
* 提供常用工具函数，例如:
  * 按名字搜索类或实例
  * 获取对象源代码
  * 打印所有线程栈和局部变量

## 安装

```
pip install pylane
```

如果使用virtualenv，需要pylane安装在被attach进程所用的env或系统库.

## 兼容性

兼容 Linux 和 BSD
