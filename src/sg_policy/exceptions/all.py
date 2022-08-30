class UnsupportedEvaluatorRef(Exception):
    def __init__(self, message="Evaluator Ref does not exist"):
        self.message = message
        super().__init__(self.message)


class UnsupportedKeyInPolicySchema(Exception):
    def __init__(self, message="Unknown Schema validation failed"):
        self.message = message
        super().__init__(self.message)


class UnsupportedProvider(Exception):
    def __init__(self, message="Provider does not exist"):
        self.message = message
        super().__init__(self.message)
