# -*- coding: utf-8 -*-

"""
"""

from .proxy import IPythonShellProxy as ShellProxy


class Shell(object):
    """Shell server"""

    # pre_codes defined to run before shell is available
    pre_codes = [
        """
            print('Command: %s %s %s' % (
                sys.executable,
                getattr(main, '__file__', '__main__'),
                ' '.join([
                    '"%s"' % (
                        arg.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"'),
                    )
                    for arg in sys.argv[1:]
                ]),
            ))
        """,
        "import pylane.shell.help_functions as tools",
        # "from imp import reload",
        # "tools = reload(tools)",
    ]

    # extend help infos followed by ipython help info
    extend_help = """Welcome to pylane shell. Features below are avaliable:
    Use TAB to get remote auto completion.
    Use 'main' to access remote process's __main__ object.
    Use 'tools' to get pylane toolkit functions.
        Example: tools.get_insts(YOUR_CLASS_NAME).
    Use 'a_object?' for more usage info.
    """
    udf_help = """
    User Defined Executor:
        Put a _user_defined_executor(input, local) function in __main__ global,
            then use $enter_executor to enter, $exit_executor to exit.
        When in executor, all input will be handled by executor.
        Arg local is an empty dict.
    User Defined Functions:
        Put a _user_defined_handler($cmd) function in __main__ global,
            then use $cmd to call them.
    """

    def __init__(self,
                 **inject_args):
        """Init injector by args.
        Args:
            encoding (str): encoding used when shell transporting

        Returns:
        """
        self.inject_args = inject_args
        self.encoding = inject_args.get('encoding')

    def run(self):
        """run shell server and connect"""
        shell_proxy = ShellProxy(self.inject_args)
        shell_proxy.run()
        shell_proxy.runsource("print('''%s''')" % self.extend_help)
        for pre_code in self.pre_codes:
            code = self.raw_code(pre_code)
            shell_proxy.runsource(code)
        shell_proxy.interact()

    def raw_code(self, code):
        """parse code in docstring"""
        lines = code.split('\n')
        for start_line in lines:
            if start_line:
                break
        blanks = len(start_line) - len(start_line.lstrip())
        code = '\n'.join([
            line[blanks:]
            for line in lines
        ])
        if not code.endswith('\n'):
            code += '\n'
        return code


def shell(*args, **kwargs):
    return Shell(*args, **kwargs).run()
