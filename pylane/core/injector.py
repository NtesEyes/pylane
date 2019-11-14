# -*- coding: utf-8 -*-

import os
import sys
import signal
import time
import tempfile
import platform
import subprocess
import stat
import atexit
from threading import Timer
from .exception import (
    RequirementsInvalid,
    PylaneExceptionHandler
)

try:
    # py3
    from subprocess import getoutput
except ImportError:
    # py2
    from commands import getoutput


class Injector(object):
    """Inject a python process, run some code inside the vm."""

    def __init__(self,
                 pid=None,
                 code=None,
                 file_path=None,
                 gdb_path='gdb',
                 timeout=10,
                 verbose=0,
                 **ignore):
        """Init injector by args.
        Args:
            pid (int): target python process's pid.
            code (str): raw code.
            file_path (str): file path of the python code file.
            gdb_path (str): executable gdb path.
            timeout (int): timeout seconds.
            verbose (int): verbose level.

        Returns:
        """

        self.gdb = gdb_path
        self.timeout = timeout
        self.verbose = verbose

        self.env_detect()
        self.ensure_pid(pid)
        self.temp_file = None
        self.code_file = None
        self.ensure_code_file(code, file_path)

        atexit.register(self.cleanup)

    def env_detect(self):
        """"""
        # check platform
        self.env = env = {}
        if 'BSD' in platform.platform():
            env['bsd'] = True
            self.run = self._bsd_run
        if platform.dist()[0] == 'Ubuntu':
            env['ubuntu'] = True

        # check gdb
        if not os.access(self.gdb, os.X_OK):
            raise RequirementsInvalid(
                'gdb is not exist or not executable.'
            )
        # check ptrace
        ptrace_scope = '/proc/sys/kernel/yama/ptrace_scope'
        ptrace_req_msg = ('ptrace is disabled, enable it by:'
                          'echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope . '
                          'arg --privileged may be also needed for docker '
                          'exec/run command to override ptrace_scope.')
        if os.path.exists(ptrace_scope):
            with open(ptrace_scope, 'r') as f:
                value = int(f.read().strip())
            if value == 1:
                raise RequirementsInvalid(ptrace_req_msg)
        else:
            getsebool = '/usr/sbin/getsebool'
            if os.path.exists(getsebool):
                p = subprocess.Popen(
                    [getsebool, 'deny_ptrace'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                if 'deny_ptrace --> on' in out:
                    raise RequirementsInvalid(ptrace_req_msg)

    def cleanup(self):
        """"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
            except:
                pass

    def ensure_code_file(self, code, file_path):
        """"""
        if file_path:
            file_path = os.path.abspath(file_path)
            if not os.path.isfile(file_path):
                raise RequirementsInvalid(
                    'Arg file_path is not a valid file.'
                )
            self.code_file = file_path
        else:
            if code:
                (fd, temp_file_path) = tempfile.mkstemp()
                with os.fdopen(fd, 'w') as f:
                    f.write(code)
                self.code_file = self.temp_file = temp_file_path
            else:
                raise RequirementsInvalid(
                    'Neither code nor code file_path specified.'
                )
        st = os.stat(self.code_file)
        os.chmod(self.code_file,
                 st.st_mode | stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)

    def ensure_pid(self, pid):
        """"""
        ps_cmd = "ps ax | awk '{print $1}' | grep -w %s" % pid
        if not pid or not getoutput(ps_cmd):
            raise RequirementsInvalid('Process %s not exist.' % pid)
        self.pid = pid

    def generate_gdb_codes(self):
        """Generate gdb command codes
        Args:
        Returns:
            list: gdb command code lines
        """

        lib_path = os.path.abspath(
            os.path.join(os.path.abspath(__file__), '../..')
        )
        inject_paths = [
            # TODO to support injected code file's path
            # cannot support docker container
            # os.path.dirname(self.code_file),
            # current path, not used
            os.getcwd(),
            lib_path
        ]
        temp_sys_name = '_pylane_sys'
        prepare_code = ' '.join([
            'import sys as %s;' % temp_sys_name,
            '%s.path.extend([%s]);' % (
                temp_sys_name,
                ','.join(['\\\"%s\\\"' % p for p in inject_paths])
            )
        ])
        # deprecated, cause its hard to pass python code in shell args
        # exec code is passed by shell command line, so add \\\" and \\\\n
        # run_code = 'exec(\\\"%s\\\")' % (self.code.replace('\n', '\\\\n'))
        if sys.version_info.major == 2:
            run_code = ' '.join([
                '__code_file = open(\\\"%s\\\");' % self.code_file,
                '__raw_code = __code_file.read();',
                '__code_file.close();',
                # python 2 donot support exec as Thread's target param
                'exec(__raw_code);',
                'del __code_file;',
                'del __raw_code;'
            ])
        else:
            run_code = ' '.join([
                '__code_file = open(\\\"%s\\\");' % self.code_file,
                '__raw_code = __code_file.read();',
                '__code_file.close();',
                # run code async and stop injection early to keep target process safe
                'from threading import Thread as __Thread;'
                '__thread = __Thread(target=exec, args=(__raw_code,));'
                '__thread.daemon = True;'
                '__thread.start();'
                'del __code_file;'
                'del __raw_code;'
                'del __Thread;'
                'del __thread;'
            ])
        # TODO injected code may change path as well
        cleanup_code = ' '.join([
            '%s.path = %s.path[:-%s];' % (
                temp_sys_name,
                temp_sys_name,
                len(inject_paths)
            )
        ])
        return [
            # use char in case of symbol PyGilState_STATE not found
            'call $gil_state = (char) PyGILState_Ensure()',
            'call (void) PyRun_SimpleString("%s")' % prepare_code,
            'call (void) PyRun_SimpleString("%s")' % run_code,
            'call (void) PyRun_SimpleString("%s")' % cleanup_code,
            # make sure previous codes are safe.
            # gdb exit without GIL release is a disaster for target process.
            'call (void) PyGILState_Release($gil_state)',
        ]

    def timeout_exit(self, process):
        print("timeout in %s secs, exit." % self.timeout)
        os.kill(process.pid, signal.SIGTERM)

    def inject(self):
        """Run inject"""
        codes = self.generate_gdb_codes()
        process = self.run(codes)
        timer = Timer(self.timeout, self.timeout_exit, (process,))
        out = b''
        err = b''
        try:
            timer.start()
            out, err = process.communicate()
        finally:
            timer.cancel()
            self.cleanup()
            if self.verbose:
                print('stdout:', out)
                print('stderr:', err)
                print(err)
            if b'Operation not permitted' in err:
                print('Cannot attach a process without perm.')
                if self.env.get('ubuntu'):
                    print('You may need root perm to use ptrace in Ubuntu.')
                exit(1)
        return True

    def _bsd_run(self, codes):
        """gdb under bsd can only run command in a file"""

        (fd, gdb_file_name) = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write('\n'.join(codes) + '\nquit')

        command = "%s --command=%s --pid=%s --exec=python" % (
            self.gdb, gdb_file_name, self.pid)

        p = self._popen(command)
        # sleep 0.5 seconds to avoid removing gdb_file too fast
        time.sleep(0.5)
        os.remove(gdb_file_name)
        return p

    def _run(self, codes):
        """gdb under linux"""

        batch_commands = ' '.join(
            ["-eval-command='%s'" % code for code in codes]
        )
        command = '%s -p %d -batch %s' % (self.gdb, self.pid, batch_commands)

        return self._popen(command)

    run = _run

    def _popen(self, command):
        """shell popen with pipe std"""
        return subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


@PylaneExceptionHandler
def inject(*args, **kwargs):
    return Injector(*args, **kwargs).inject()
