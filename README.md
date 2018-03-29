# pylane

[![PyPI version](https://badge.fury.io/py/pylane.svg)](https://badge.fury.io/py/pylane)

An python vm injector with debug tools, based on gdb and ptrace.

## Features

* Attach a running python process with its pid, directly access and change anything in python vm, or run a user defined python script.
* Provide a python remote shell.
    * Use IPython as an interactive interface, support some IPython features such as ? % magic functions.
    * Provide remote auto completion.
    * Provide debug toolkit, we can get class/instances by name, get object's source code, etc.
    * Defined an executor in program, and use the shell as a command interface.
* Support Linux and BSD

## Usage

install:

```
pip install pylane
```

use:

```
pylane inject <PID> <YOUR_PYTHON_FILE>
```

to run your code in a process

or

```
pylane shell <PID>
```

to get an interactive shell
