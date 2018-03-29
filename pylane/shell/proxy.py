# -*- coding: utf-8 -*-


import time
from threading import Thread
from .sock import SockServer
from .inject import inject
from .ipython_embed import IPythonShell


class AsyncServer(object):
    """
    """
    LISTEN_TIMEOUT = 30

    def start_server(self, encoding, timeout):
        """start sock server and wait for client"""
        self.sock_server = SockServer(
            listen_timeout=self.LISTEN_TIMEOUT,
            transport_timeout=timeout or 0,
            encoding=encoding)
        self.sock_server.listen()
        self.async_accept()
        return (self.sock_server.host, self.sock_server.port)

    def async_accept(self):
        """start a thread to wait for sock server accept"""
        thread = Thread(
            target=self.sock_server.accept, name="sock_server_async_accept")
        thread.daemon = True
        self.async_accept_thread = thread
        thread.start()

    def wait(self):
        """wait for remote client to connet"""
        while self.async_accept_thread and self.async_accept_thread.is_alive():
            time.sleep(0.1)
        if not self.sock_server.connected():
            raise NoConnectedClient(
                "No client connected in %s seconds" % self.LISTEN_TIMEOUT
            )
        self.sock = self.sock_server


class NoConnectedClient(Exception):
    pass


class SimpleRemoteProxy(object):
    MODULE = 'remote_shell'
    ENTRANCE = 'RemoteShellThread'


class BaseProxy(AsyncServer, SimpleRemoteProxy):
    """"""

    def __init__(self, inject_args):
        """"""
        self.inject_args = inject_args

    def run(self):
        """"""
        host, port = self.start_server(
            encoding=self.inject_args.get('encoding'),
            timeout=self.inject_args.get('timeout')
        )
        inject(
            module=self.MODULE,
            entrance=self.ENTRANCE,
            host=host,
            port=port,
            inject_args=self.inject_args)
        self.wait()


class IPythonShellProxy(BaseProxy, IPythonShell):
    """"""

    def __init__(self, inject_args):
        BaseProxy.__init__(self, inject_args)
        IPythonShell.__init__(self, inject_args.get('encode'))
