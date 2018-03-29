# -*- coding: utf-8 -*-

import os
from pylane.core.injector import inject as _inject


def inject(module, entrance, host, port, inject_args):
    """
    inject process with module.entrance
    """
    encoding = inject_args.get('encoding', 'utf-8')
    code = create_payload(module, entrance, host, port, encoding)
    inject_args['code'] = code
    success = _inject(**inject_args)
    if not success:
        exit(1)


def create_payload(module, entrance, host, port, encoding):
    """
    generate inject payload code for an exist file
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = base_path + '/%s.py' % module

    payload = "def start_remote_shell():\n"
    with open(file_path) as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            payload += '    ' + line
    payload += "\n    {entrance}(host='{host}', port={port}, encoding='{encoding}').start()\n".format(
        entrance=entrance,
        host=host,
        port=port,
        encoding=encoding
    )
    payload += '\nstart_remote_shell()'
    return payload
