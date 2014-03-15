class Future:
    """Wraps a future; calbacks on the wrapper are scheduled on a given Clock

    To be instantiated using Clock.wait_for()
    """
    def __init__(self, clock, wrapped_future):
        self.clock = clock
        self._wrapped = wrapped_future
        self._callbacks = {}
        self.cancel = wrapped_future.cancel
        self.cancelled = wrapped_future.cancelled
        self.done = wrapped_future.done
        self.result = wrapped_future.result
        self.exception = wrapped_future.exception
        self.set_result = wrapped_future.set_result
        self.set_exception = wrapped_future.set_exception

    def __iter__(self):
        return iter(self._wrapped)

    def add_done_callback(self, fn):
        def wrapped_callback(future):
            self.clock.schedule(0, fn, self)
        self._callbacks.setdefault(fn, []).append(wrapped_callback)
        self._wrapped.add_done_callback(wrapped_callback)

    def remove_done_callback(self, fn):
        unwrapped_callbacks = self._callbacks[fn]
        return sum(self._wrapped.remove_done_callback(cb)
                   for cb in unwrapped_callbacks)
