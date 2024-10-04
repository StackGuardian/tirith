import logging

logger = logging.getLogger(__name__)


def sort_collections(inputs):
    try:
        if isinstance(inputs, (str, float, int, bool)):
            return inputs
        elif isinstance(inputs, list):
            if len(inputs) == 0:
                return inputs
            if (
                isinstance(inputs[0], str)
                or isinstance(inputs[0], float)
                or isinstance(inputs[0], int)
                or isinstance(inputs[0], bool)
            ):
                inputs = sorted(inputs)
                return inputs
            else:
                sorted_list = []
                for index, val in enumerate(inputs):
                    sorted_list.append(sort_collections(val))
                return sorted_list
        elif isinstance(inputs, dict):
            sorted_dict = {}
            for key in inputs:
                sorted_val = sort_collections(inputs[key])
                sorted_dict[key] = sorted_val
            return sorted_dict
        else:
            return inputs
    except Exception as e:
        # TODO: LOG
        logger.exception(e)
        return inputs
