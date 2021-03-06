from functools import partial
from functional.util import compose, parallelize


class ExecutionStrategies(object):
    """
    Enum like object listing the types of execution strategies
    """
    PRE_COMPUTE = 0
    PARALLEL = 1


class ExecutionEngine(object):

    def evaluate(self, sequence, transformations):
        # pylint: disable=no-self-use
        result = sequence
        for transform in transformations:
            strategies = transform.execution_strategies
            if (strategies is not None
                    and ExecutionStrategies.PRE_COMPUTE in strategies):
                result = transform.function(list(result))
            else:
                result = transform.function(result)
        return iter(result)


class ParallelExecutionEngine(ExecutionEngine):

    def __init__(self, processes=None, raise_errors=True,
                 *args, **kwargs):
        super(ParallelExecutionEngine, self).__init__(*args, **kwargs)
        self.processes = processes
        self.raise_errors = raise_errors

    def evaluate(self, sequence, transformations):
        result = sequence
        parallel = partial(parallelize, processes=self.processes,
                           raise_errors=self.raise_errors)
        staged = []
        for transform in transformations:
            strategies = transform.execution_strategies or {}
            if ExecutionStrategies.PARALLEL in strategies:
                staged.insert(0, transform.function)
            else:
                if staged:
                    result = parallel(compose(*staged), result)
                    staged = []
                if ExecutionStrategies.PRE_COMPUTE in strategies:
                    result = list(result)
                result = transform.function(result)
        if staged:
            result = parallel(compose(*staged), result)
        return iter(result)
