# -*- coding: utf-8 -*-

import sys
import traceback
import threading
import code
import json

from pylane.shell.sock import SockClient

if sys.version_info[0] == 3:
    from io import StringIO
else:
    from io import BytesIO as StringIO


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
            io.seek(0)
            io.truncate()

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
            # recv of sock closed returns '' in py2 and None in py3
            if cmd == '' or cmd is None:
                break
            flag = '0'
            self.sock.send(flag + self.runsource(cmd))

    def runsource(self, source, filename="<input>", symbol="single"):
        """
        run code in interpreter
        """
        with self.lock:
            source_strip = source.strip()
            if source_strip == '$enter_executor':
                if self.user_defined_executor:
                    self.in_user_defined_executor = True
                    return 'True'
                else:
                    return 'False, _user_defined_executor not found'
            if source_strip == '$exit_executor':
                self.in_user_defined_executor = False
                return 'True'

            if self.in_user_defined_executor and self.user_defined_executor:
                with self.stdio_hook:
                    return repr(self.user_defined_executor(
                        source_strip,
                        self.user_defined_executor_local
                    ))

            extend_function = self.get_extend_function(source_strip)
            if extend_function:
                with self.stdio_hook:
                    try:
                        return extend_function(self, source_strip)
                    except Exception as e:
                        print("Failed to run source", source, "err:", e)

            with self.stdio_hook:
                state, op = self._runsource(source)
                if not state:
                    print("Failed to run source", source)
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
        # add \n in case of incomplete section code.
        ret = self._interpreter.runsource(
            source + "\n", filename="<input>", symbol="single")
        out, err = self.get_output()
        if ret is True:
            err += "error: cmd not completed."
        if err:
            ret = False, err
        else:
            ret = True, out
        if self.debug:
            open('/tmp/pmx-shell-log', 'w').write("%s\n%s" % (
                source, ret))
        return ret

    def run_help_doc(self, source):
        """
        support object?
        TODO more info when object??
        """
        item = source.replace('??', '').replace('?', '')
        state, doc = self._runsource('%s.__doc__' % item)
        if not state:
            return doc
        state, type_ = self._runsource('type(%s).__name__' % item)
        state, type_ = self._runsource('type(%s).__name__' % item)
        if not state:
            return type_
        op = "Type: %sDocstring: %s" % (type_, doc)
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
            dir_list = eval(op)
            suggs = [item + '.' + t for t in dir_list]
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

        return json.dumps(suggs)

    def user_defined_function(self, source):
        import __main__ as main
        handler = getattr(main, '_user_defined_handler', None)\
            or getattr(main, '_telnet_handler', None)
        if not handler:
            return 'User defined handler not found'
        source = "main.%s('%s')" % (handler.__name__, source.replace('\n', ''))
        state, op = self._runsource(source)
        if not isinstance(op, str):
            op = repr(op)
        return op

    def get_extend_function(self, source):
        """
        """
        if source.endswith('?'):
            return self.extend_functions['help_doc']
        if source.startswith('$'):
            return self.extend_functions['udf']
        return self.extend_functions.get(
            source.split('$')[0]
        )

    extend_functions = {
        'help_doc': run_help_doc,
        'udf': user_defined_function,
        'complete': complete
    }

    def run(self):
        """
        main run entrance
        """
        self.name = "pylane-shell-thread"
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
