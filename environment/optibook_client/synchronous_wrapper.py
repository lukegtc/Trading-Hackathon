import concurrent
import threading
import time
import logging
import asyncio
import datetime

logger = logging.getLogger('client')


class SynchronousWrapper:
    def __init__(self, clients):

        self._clients = clients

        self._thread = None
        self._loop = asyncio.new_event_loop()

    def get_loop(self):
        return self._loop

    def is_connected(self) -> bool:
        return all([cl.is_connected() for cl in self._clients]) and self._loop.is_running()

    def connect(self) -> None:
        assert not self.is_connected(), "Cannot connect while already connected"

        self._thread = threading.Thread(target=self._thread_entry_point, daemon=True)
        self._thread.start()

        slept_for = 0
        sleep_duration = 0.1
        while not self.is_connected() and slept_for < 5:
            time.sleep(sleep_duration)
            slept_for += sleep_duration
        if not self.is_connected():
            raise Exception("Unable to connect to the exchange")

    def disconnect(self) -> None:
        if self._loop.is_running():
            futures = [concurrent.futures.Future() for c in self._clients]

            def callback():
                for fut_to_set, cl in zip(futures, self._clients):
                    task = self._loop.create_task(cl.disconnect())
                    task.add_done_callback(
                        lambda async_fut, fut_to_set=fut_to_set: fut_to_set.set_exception(async_fut.exception()) if async_fut.exception() else fut_to_set.set_result(async_fut.result())
                    )

            self._loop.call_soon_threadsafe(callback)

            for fut in futures:
                fut.result()

            # allow some time for the loop to complete
            slept_for = 0
            sleep_duration = 0.1
            while self._loop.is_running() and slept_for < 5:
                time.sleep(sleep_duration)
                slept_for += sleep_duration
        assert (not self._loop.is_running())

    def run_on_loop(self, awaitable):
        start_time = datetime.datetime.now()
        fut = concurrent.futures.Future()

        def callback():
            task = self._loop.create_task(awaitable)
            task.add_done_callback(lambda async_fut: fut.set_exception(async_fut.exception()) if async_fut.exception() else fut.set_result(async_fut.result()))

        self._loop.call_soon_threadsafe(callback)

        ret = fut.result()
        end_time = datetime.datetime.now()
        diff = end_time - start_time
        if diff.total_seconds() > 1.0:
            logger.warning(f"Call to server took {diff.total_seconds()}s", stack_info=True)
        return ret

    # private functions from here

    def _thread_entry_point(self):
        logger.debug("background thread started")
        try:
            self._loop.run_until_complete(self._run())
        finally:
            cs = [cl.disconnect() for cl in self._clients]
            self._loop.run_until_complete(asyncio.gather(*cs, *asyncio.Task.all_tasks(self._loop), loop=self._loop, return_exceptions=True))

    async def _run(self):
        try:
            await asyncio.gather(*[cl.connect() for cl in self._clients], loop=self._loop)

            async def wait_connected(cl):
                while cl.is_connected():
                    await asyncio.sleep(0.1)

            await asyncio.gather(*[wait_connected(cl) for cl in self._clients], loop=self._loop)
        except Exception as exc:
            logger.warning(exc)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()
