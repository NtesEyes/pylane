# -*- coding: utf-8 -*-

"""
Entry of Pylane
"""

import click
from pylane.core.injector import inject as _inject
from pylane.shell.shell import shell as _shell


@click.command()
@click.argument('pid', type=int)
@click.argument('file_path', type=click.Path(exists=True, readable=True))
@click.pass_context
def inject(ctx, pid, file_path):
    """Inject a python process, run some code inside the vm."""
    _inject(pid=pid, file_path=file_path, **ctx.obj)


@click.command()
@click.argument('pid', type=int)
@click.pass_context
def shell(ctx, pid):
    """Create a remote python shell on a process."""
    _shell(pid=pid, **ctx.obj)


@click.group()
@click.option('-g', '--gdb_path', type=click.Path(exists=True), default='/usr/bin/gdb')
@click.option('-v', '--verbose', count=True)
@click.option('-t', '--timeout', type=int, default=10)
@click.option('-e', '--encoding', type=str, default='utf-8')
@click.pass_context
def main_entry(ctx, **kwargs):
    ctx.obj = kwargs


main_entry.add_command(inject)
main_entry.add_command(shell)


def main():
    main_entry()


if __name__ == '__main__':
    main()
