from .const import TIME_FORMATTER


class Logger:
    def __init__(self):
        self.tags = []

    def pop(self):
        self.tags.pop()

    def push(self, name: str):
        self.tags.append(name)

    def log(self, *values, **kwargs):
        import time
        prefix = "[{}]{}".format(time.strftime(TIME_FORMATTER),
                                 "[{}]".format("][".join(self.tags)) if len(self.tags) > 0 else "")
        print(prefix, end=" ")
        print(*values, **kwargs)
