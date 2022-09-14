import logging

logger = logging.getLogger()


def sort_collections(input):
    try:
        if isinstance(input, str) or isinstance(input, float) or isinstance(input, int) or isinstance(input, bool):
            return input
        elif isinstance(input, list):
            if (
                isinstance(input[0], str)
                or isinstance(input[0], float)
                or isinstance(input[0], int)
                or isinstance(input[0], bool)
            ):
                input = sorted(input)
                return input
            else:
                sorted_list = []
                for index, val in enumerate(input):
                    sorted_list.append(sort_collections(val))
                return sorted_list
        elif isinstance(input, dict):
            sorted_dict = {}
            for key in input:
                sorted_val = sort_collections(input[key])
                sorted_dict[key] = sorted_val
            return sorted_dict
        else:
            return input
    except Exception as e:
        # TODO: LOG
        logger.exception(e)
        return input
