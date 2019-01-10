# -*- coding: utf-8 -*-

import json
from IPython.terminal.embed import InteractiveShellEmbed
from IPython.core.interactiveshell import ExecutionResult


class IPythonShell(InteractiveShellEmbed):
    """use an ipython interface to provide shell"""

    ENCODING = 'utf-8'

    def __init__(self, encoding='utf-8'):
        InteractiveShellEmbed.__init__(self)
        self.set_custom_completer(self.remote_completer, pos=0)
        self.encoding = encoding or self.ENCODING

    def ipython_pre_works(self, result, raw_cell, store_history,
                          silent=False, shell_futures=True,
                          ):
        if silent:
            store_history = False

        if store_history:
            result.execution_count = self.execution_count

        def error_before_exec(value):
            result.error_before_exec = value
            return result

        self.events.trigger('pre_execute')
        if not silent:
            self.events.trigger('pre_run_cell')

        preprocessing_exc_tuple = None
        cell = raw_cell

        if store_history:
            self.history_manager.store_inputs(self.execution_count,
                                              cell, raw_cell)
        if not silent:
            self.logger.log(cell, raw_cell)

        if preprocessing_exc_tuple is not None:
            self.showtraceback(preprocessing_exc_tuple)
            if store_history:
                self.execution_count += 1
            return error_before_exec(preprocessing_exc_tuple[2])

        return cell

    def ipython_post_works(self, result, store_history):
        if store_history:
            self.history_manager.store_output(self.execution_count)
            self.execution_count += 1
            result.execution_count = self.execution_count

    def redirect_to_ipython(self, raw_cell):
        """
        to be finished
        """
        if raw_cell == '?\n':
            return True
        if raw_cell.startswith('%'):
            return True

        return False

    def run_cell(self, raw_cell, store_history=True,
                 silent=False, shell_futures=True
                 ):
        """
        run ipython code in ipython run_cell,
        run python console code in remoute console
        """
        if self.redirect_to_ipython(raw_cell):
            return InteractiveShellEmbed.run_cell(
                self, raw_cell, store_history, silent, shell_futures
            )

        result = ExecutionResult()
        self.displayhook.exec_result = result

        if (not raw_cell) or raw_cell.isspace():
            return result

        cell = self.ipython_pre_works(
            result, raw_cell, store_history, silent, shell_futures
        )

        output = self._runsource(cell)
        if output:
            result.result = output
            self._output(output)
            # self.write(output)
        self.ipython_post_works(result, store_history)

        return result

    def _output(self, output):
        """
        try to display evaled object
        if failed, write raw string
        """
        try:
            output = eval(output)
            try:
                output = output.decode(self.encoding)
            except:
                pass
            self.displayhook(output)
            return
        except:
            pass
        if not output.endswith('\n\n'):
            output += '\n'
        self.displayhook.start_displayhook()
        self.displayhook.write_output_prompt()
        self.write('\n' + output)
        self.displayhook.finish_displayhook()

    def runsource(self, source):
        self.write(self._runsource(source))

    def _runsource(self, source, *args, **kwargs):
        self.sock.send(source)
        raw = self.sock.recv()
        if raw == '' or raw is None:
            exit(0)
        flag, op = raw[0], raw[1:]
        # TODO old interface which is not used, going to be deprecated.
        flag is '0'
        return op

    def remote_completer(self, ipcompleter, text, line=None, cursor_pos=None):
        source = 'complete$%s' % text
        op = self._runsource(source)
        try:
            # ignore those cases like obj not exists
            return json.loads(op)
        except:
            return []
