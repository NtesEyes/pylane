# -*- coding: utf-8 -*-


import socket
import struct
import traceback
import random
import time


class Transport(object):
    """
    """

    sock = None
    encoding = 'utf-8'

    def send(self, data):
        """
        send data with length in 4 bytes header
        """
        data = data.encode(self.encoding)
        header = struct.pack('<L', len(data))
        self.sock.sendall(header + data)

    def recv(self):
        """
        recv data
        """
        header = self.recv_bytes(4)
        if header == '':
            return header
        try:
            length = struct.unpack('<L', header)[0]
        except:
            return None
        data = self.recv_bytes(length).decode(self.encoding)
        return data

    def recv_bytes(self, n):
        """
        recv n bytes
        """
        data = b''
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def close(self):
        try:
            self.sock and self.sock.close()
        except:
            traceback.print_exc()


class SockClient(Transport):
    """
    """

    sock = None
    CONNECT_RETRIES = 3
    CONNECT_RETRY_INTERVAL = 1

    def __init__(self, host, port, encoding='utf-8'):
        self.host = host
        self.port = port
        self.encoding = encoding

    def connect(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        e = None
        for i in range(self.CONNECT_RETRIES):
            try:
                sock.connect((self.host, self.port))
                break
            except socket.error as e:
                pass
            time.sleep(self.CONNECT_RETRY_INTERVAL)
        else:
            if e:
                raise e
        self.sock = sock


class SockServer(Transport):
    """
    """

    RANDOM_PORT_RANGE = (65000, 65500)
    BIND_RETRIES = 10
    ACCEPT_CLIENT_NUM = 1

    host = "127.0.0.1"
    port = None
    server = None
    client = None

    def __init__(self, listen_timeout=30, transport_timeout=0, encoding='utf-8'):
        """
        """
        self.listen_timeout = listen_timeout
        self.transport_timeout = transport_timeout
        self.encoding = encoding
        self.server = None
        self.sock = None

    def listen(self):
        """
        bind and listen
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for i in range(self.BIND_RETRIES):
            port = self.get_port()
            try:
                sock.bind((self.host, port))
                self.port = port
                sock.settimeout(self.listen_timeout)
                sock.listen(self.ACCEPT_CLIENT_NUM)
                break
            except socket.error as e:
                # not a address already in use exception
                if e.errno != 98:
                    raise e
        else:
            raise NoPortAvailable(repr(self.RANDOM_PORT_RANGE))

        self.server = sock

    def accept(self):
        """
        accept client
        """
        try:
            (sock, _) = self.server.accept()
        except socket.timeout:
            return
        if self.transport_timeout:
            sock.settimeout(self.transport_timeout)
        self.sock = self.client = sock

    def get_port(self):
        return random.randint(*self.RANDOM_PORT_RANGE)

    def connected(self):
        return self.sock is not None

    def close(self):
        try:
            self.sock and self.sock.close()
            self.server and self.server.close()
        except:
            traceback.print_exc()


class NoPortAvailable(Exception):
    pass


class NoConnectedClient(Exception):
    pass
