class UnsupportedConditionTypeInPolicy(Exception):
    def __init__(self, message="Condition Type is not supported"):
        self.message = message
        super().__init__(self.message)


class UnsupportedKeyInPolicy(Exception):
    def __init__(self, message="Unsupported Key in policy"):
        self.message = message
        super().__init__(self.message)


class UnsupportedProviderInPolicy(Exception):
    def __init__(self, message="Unsupported Provider in policy"):
        self.message = message
        super().__init__(self.message)
