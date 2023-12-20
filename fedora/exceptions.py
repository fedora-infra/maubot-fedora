class InfoGatherError(Exception):
    def __init__(self, message):
        self.message = message


class InvalidInput(ValueError):
    def __init__(self, message):
        self.message = message
