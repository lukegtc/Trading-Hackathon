import asyncio
import logging
import typing
import traceback
import socket
import capnp
from .idl import common_capnp

VERBOSE = 5
logging.addLevelName(VERBOSE, 'VERBOSE')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(name)-10s] [%(threadName)-12s] %(message)s')
logger = logging.getLogger('client')

TIMEOUT_VAL = 2

def _get_default_settings():
    from pathlib import Path
    import json
    optibook_path = Path.home() / Path('.optibook')
    if optibook_path.is_file():
        with optibook_path.open('r') as f:
            return json.load(f)
    return {}


def logger_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            logger.exception('Exception occurred in callback')
            raise
    return wrapper


_default_settings = _get_default_settings()


class Client:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self.reset_data()

    def reset_data(self):
        self._task = None
        self._socket = None
        self._client = None
        self._connected = False
        self._dcp = None

    async def connect(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()
        if self.is_connected():
            raise Exception("already connected")
        self.reset_data()

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._host, self._port))
        self._client = capnp.TwoPartyClient(self._socket)
        self._connected = True

        def on_dc(*args, **kwargs):
            self._connected = False

        self._dcp = self._client.on_disconnect().then(on_dc)

        await self._on_connected()

        self._task = loop.create_task(self._run())
        self._loop = loop

    async def _on_connected(self):
        pass

    async def _run(self):
        while self.is_connected():
            capnp.poll_once()
            await asyncio.sleep(0.1)

    def is_connected(self):
        if self._socket is None:
            return False
        try:
            self._socket.getpeername()
        except OSError:
            return False
        return self._connected

    async def disconnect(self):
        if self.is_connected():
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()

        capnp.poll_once()

        if self._task is not None:
            await self._task

    def _call_handler(self, h, *args, **kwargs):
        f = h(*args, **kwargs)
        if asyncio.iscoroutine(f):
            asyncio.ensure_future(f, loop=self._loop)


class RawClient:
    def __init__(self, host, port):
        self._host = host
        self._port = port
        self._extra_callbacks_id = 0
        self._extra_callbacks = {}
        self.reset_data()

    def reset_data(self):
        self._task = None
        self._reader = None
        self._writer = None
        self._waiters: typing.Dict[int, asyncio.Future] = {}
        self._request_id = 0

    def add_message_callback(self, f):
        c_id = self._extra_callbacks_id
        self._extra_callbacks[c_id] = f
        self._extra_callbacks_id += 1
        return id

    def remove_message_callback(self, c_id):
        del self._extra_callbacks[c_id]

    async def _read(self):
        logger.info(f'start read {self._reader}')
        try:
            while not self._writer.transport.is_closing():
                nr_segments_b = await self._reader.readexactly(4)
                nr_segments = int.from_bytes(nr_segments_b, byteorder='little') + 1
                bytes_to_read = nr_segments * 4
                if nr_segments % 2 == 0:
                    bytes_to_read += 4
                segment_sizes_b = await self._reader.readexactly(bytes_to_read)
                total_size = 0
                for i in range(nr_segments):
                    segment_size = int.from_bytes(segment_sizes_b[i*4:(i+1)*4], byteorder='little')
                    total_size += segment_size * 8
                all_data = await self._reader.readexactly(total_size)
                total_msg_buf = nr_segments_b + segment_sizes_b + all_data
                msg = common_capnp.RawMessage.from_bytes(total_msg_buf)

                if msg.type == common_capnp.GenericReply.schema.node.id:
                    await self._handle_message_reply(msg.msg.as_struct(common_capnp.GenericReply.schema))
                else:
                    await self._on_message(msg)

                for f in self._extra_callbacks.values():
                    f(msg)
        except asyncio.exceptions.IncompleteReadError:
            logger.info('info disconnected due to incomplete read - most likely connection was closed')
            raise
        except:
            traceback.print_exc()
            raise
        finally:
            self._reader = None
            self._writer = None
            logger.info('end of reader loop')

    async def _on_message(self, msg):
        pass

    async def send_request(self, request_id, request):
        await self.write(request)

        f = asyncio.Future()
        self._waiters[request_id] = f
        return await f

    async def _handle_message_reply(self, msg):
        request_id = msg.requestId

        if request_id in self._waiters:
            fut = self._waiters.pop(request_id)
            fut.set_result(msg)
        else:
            raise Exception(
                f"Got reply for unknown request id {request_id}. Message: '{str(msg)}'")

    async def connect(self, loop=None):
        if not loop:
            loop = asyncio.get_event_loop()

        if self.is_connected():
            raise Exception("already connected")
        self.reset_data()

        self._reader, self._writer = await asyncio.open_connection(self._host, self._port, loop=loop)
        logger.info(f'opened connection')

        async def try_run():
            try:
               await self._read()
            except Exception as e:
                self._cleanup_on_exception(e)

        self._task = asyncio.ensure_future(try_run())

        await self._on_connected()

    async def write(self, msg):
        self._writer.write(msg.to_bytes())
        await self._writer.drain()

    async def _on_connected(self):
        pass

    def is_connected(self):
        return self._writer and not self._writer.transport.is_closing()

    async def disconnect(self):
        if self.is_connected():
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except:
                # python 3.6 does not allow wait_closed()
                # hack to just sleep for 100ms
                await asyncio.sleep(0.1)

        if self._task is not None:
            await self._task

    def _cleanup_on_exception(self, exc):
        for f in self._waiters.values():
            f.set_exception(exc)
