import os
import random
import socket
import threading


def hostname():
    return socket.gethostname()

_threads = []


def _execute_async(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    _threads.append(thread)
    return thread


class Server:
    """A quick way to create a socket server"""

    def __init__(self, on_disconnect, host, port, on_connect=None, on_recv=None):
        """
        :param on_disconnect: A function to call when a client disconnects, will receive the client and address as
            parameters
        :param host: The host to bind to
        :param port: The port to bind to
        :param on_connect: A function to call when a client connects, will receive the client and address as parameters
        :param on_recv: A function to call when a client sends data, will receive the client, address and data as
            parameters
        """
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_recv = on_recv
        self.host = host
        self.port = port

        # Assertions..

        assert on_recv is not None or on_connect is not None, "You must provide at least one of on_recv or on_connect"
        assert on_recv is None or callable(on_recv), "on_recv must be a function"
        assert on_connect is None or callable(on_connect), "on_connect must be a function"
        assert callable(on_disconnect), "on_disconnect must be a function"

        if on_connect is None:
            assert on_recv is not None, "You must provide at least one of on_recv or on_connect"

        if on_recv is None:
            assert on_connect is not None, "You must provide at least one of on_recv or on_connect"



        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self._alive = False

    def start(self):
        """Start the socket server"""
        self._alive = True
        self.socket.listen()
        while self._alive:
            client, address = self.socket.accept()
            if self.on_connect is not None:
                _execute_async(
                    self.on_connect,
                    client,
                    address
                )
            else:
                _execute_async(
                    self._builtin_on_connect,
                    client,
                    address
                )

    def _builtin_on_connect(self, client: socket.socket, address):
        while self._alive:
            try:
                data = client.recv(1024)
                if data:
                    if self.on_recv is not None:
                        _execute_async(
                            self.on_recv,
                            client,
                            address,
                            data
                        )
                else:
                    client.close()
                    raise ConnectionResetError
            except (ConnectionResetError, ConnectionAbortedError, OSError):
                self.on_disconnect(client, address)
                break


    def stop(self):
        """Stop the socket server"""
        self._alive = False
        self.socket.close()
        for t in _threads:
            assert isinstance(t, threading.Thread)
            assert not t.is_alive(), "Thread {} is still alive".format(t)




class UDSServer(Server):
    """A quick way to create a socket server using Unix Domain Sockets"""

    def __init__(self, on_disconnect, path, on_connect=None, on_recv=None):
        """
        :param on_disconnect: A function to call when a client disconnects, will receive the client and address as
            parameters
        :param path: The path to bind to
        :param on_connect: A function to call when a client connects, will receive the client and address as parameters
        :param on_recv: A function to call when a client sends data, will receive the client, address and data as
            parameters
        """
        super().__init__(on_disconnect, 'localhost', random.randint(6000, 9999), on_connect, on_recv)
        self.socket.close()
        if os.path.exists(path):
            os.unlink(path)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(path)