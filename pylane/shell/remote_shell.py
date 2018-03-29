# -*- coding: utf-8 -*-

import sys
import traceback
import threading
import code

from pylane.shell.sock import SockClient

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from StringIO import StringIO


class OutputHookContext(object):
    """
    Hook sys std with string io
    """

    def __enter__(self):
        self.sys_stdout = sys.stdout
        sys.stdout = self.stdout = StringIO()

        self.sys_stderr = sys.stderr
        sys.stderr = self.stderr = StringIO()

    def __exit__(self, *args, **kwargs):
        sys.stdout = self.sys_stdout
        sys.stderr = self.sys_stderr

    def truncate(self):
        for io in (sys.stdout, sys.stderr):
            if isinstance(io, StringIO):
                io.buf = ''

    def getvalue(self):
        return (self.stdout.getvalue(), self.stderr.getvalue())

    def getvalue_truncate(self):
        value = (self.stdout.getvalue(), self.stderr.getvalue())
        self.truncate()
        return value


class RemoteShellThread(threading.Thread):
    """
    Start a thread in target process, run an interpreter
    """

    host = 'localhost'
    port = 9594
    debug = False

    def __init__(self, host=None, port=None, encoding='utf-8'):
        """
        """
        if host:
            self.host = host
        if port:
            self.port = port

        self.encoding = encoding
        self.lock = threading.RLock()
        self.stdio_hook = OutputHookContext()

        import __main__ as main
        self.user_defined_executor = getattr(
            main, '_user_defined_executor', None)
        self.in_user_defined_executor = False
        self.user_defined_executor_local = {}

        # use code for more compatibility
        #   even if we provide some ipython features
        # TODO may integrate ipython someday
        self._interpreter = code.InteractiveInterpreter(locals=locals())
        self.runsource('import sys')
        self.runsource('import __main__ as main')

        self.sock = SockClient(self.host, self.port, encoding)
        super(RemoteShellThread, self).__init__()

    def handle(self):
        """
        handle io
        """
        while True:
            cmd = self.sock.recv()
            if cmd is None:
                continue
            if cmd is '':
                break
            flag = '0'
            self.sock.send(flag + self.runsource(cmd))

    def runsource(self, source, filename="<input>", symbol="single"):
        """
        run code in interpreter
        """
        with self.lock:
            if source == '$enter_executor\n':
                if self.user_defined_executor:
                    self.in_user_defined_executor = True
                    return 'True'
                else:
                    return 'False, _user_defined_executor not found'
            if source == '$exit_executor\n':
                self.in_user_defined_executor = False
                return 'True'

            op = '\n'
            with self.stdio_hook:
                if self.in_user_defined_executor and self.user_defined_executor:
                    return repr(self.user_defined_executor(
                        source.replace('\n', ''),
                        self.user_defined_executor_local
                    ))
                extend_function = self.get_extend_function(source)
                if extend_function:
                    return extend_function(self, source)

                state, op = self._runsource(source)
            return op

    def get_output(self):
        """
        """
        out, err = self.stdio_hook.getvalue_truncate()
        try:
            out = out.decode(self.encoding)
            err = err.decode(self.encoding)
        except:
            # TODO
            pass
        return out, err

    def _runsource(self, source):
        self._interpreter.runsource(
            source, filename="<input>", symbol="single")
        out, err = self.get_output()
        if err:
            ret = False, err
        else:
            ret = True, out
        if self.debug:
            file('/tmp/pmx-shell-log', 'w').write("%s\n%s" % (
                source, ret))
        return ret

    def run_help_doc(self, source):
        """
        support object?
        TODO more info when object??
        """
        item = source.replace('??\n', '').replace('?\n', '')
        state, doc = self._runsource('%s.__doc__' % item)
        if not state:
            return doc
        # pre eval and decode to support unicode doc
        doc = eval(doc).decode(self.encoding)
        state, type_ = self._runsource('type(%s).__name__' % item)
        type_ = eval(type_)

        op = "Type: %s\nDocstring: %s\n" % (type_, doc)
        return op

    def complete(self, source):
        """
        """
        text = source.split('$', 2)[1]
        suggs = []
        # for obj.\t
        if text.endswith('.'):
            item = text[:-1]
            state, op = self._runsource('dir(%s)' % item)
            if not state:
                return op
            suggs = eval(op)
        # for obj.prefix\t
        elif '.' in text:
            item, sub_text = text.rsplit('.', 1)
            state, op = self._runsource('dir(%s)' % item)
            if not state:
                return op
            dir_list = eval(op)
            for t in dir_list:
                if t.startswith(sub_text):
                    suggs.append(item + '.' + t)
        # for prefix\t
        else:
            state, op = self._runsource('dir()')
            if not state:
                return op
            dir_list = eval(op)
            for t in dir_list:
                if t.startswith(text):
                    suggs.append(t)

        return repr(suggs)

    def user_defined_function(self, source):
        import __main__ as main
        handler = getattr(main, '_user_defined_handler', None)\
            or getattr(main, '_telnet_handler', None)
        if not handler:
            return 'User defined handler not found'
        source = "main.%s('%s')" % (handler.__name__, source.replace('\n', ''))
        state, op = self._runsource(source)
        if not isinstance(op, basestring):
            op = repr(op)
        return op

    def get_extend_function(self, source):
        """
        """
        if source.endswith('?\n'):
            return self.extend_functions['help']
        if source.startswith('$'):
            return self.extend_functions['udf']
        return self.extend_functions.get(
            source.split('$')[0]
        )

    extend_functions = {
        'help': run_help_doc,
        'udf': user_defined_function,
        'complete': complete
    }

    def run(self):
        """
        main run entrance
        """
        try:
            self.sock.connect()
            self.handle()
        except SystemExit:
            pass
        except:
            traceback.print_exc(file=sys.__stderr__)
        finally:
            if self.sock:
                self.sock.close()
