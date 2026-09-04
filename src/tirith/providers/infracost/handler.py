import logging

logger = logging.getLogger(__name__)


def __get_all_costs(operation_type, input_data):
    logger.debug(f"costType :  {operation_type}")
    pointer = {
        "total_monthly_cost": ["totalMonthlyCost", "monthlyCost"],
        "total_hourly_cost": ["totalHourlyCost", "hourlyCost"],
    }
    total_sum = 0
    matched_count = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if (
                        pointer[operation_type][0] in resource
                        and resource[pointer[operation_type][0]]
                        and resource[pointer[operation_type][0]] != "null"
                    ):
                        total_sum += float(resource[pointer[operation_type][0]])
                        matched_count += 1
                    elif (
                        pointer[operation_type][1] in resource
                        and resource[pointer[operation_type][1]]
                        and resource[pointer[operation_type][1]] != "null"
                    ):
                        # Support new schema for Infracost
                        total_sum += float(resource[pointer[operation_type][1]])
                        matched_count += 1
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                logger.debug(f"Total sum of {operation_type} of all resources :  {total_sum}")
                return total_sum, matched_count
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def __get_resources_costs(resource_type, operation_type, input_data):
    logger.debug(f"costType :  {operation_type}")
    pointer = {"total_monthly_cost": "totalMonthlyCost", "total_hourly_cost": "totalHourlyCost"}
    pointer = {
        "total_monthly_cost": ["totalMonthlyCost", "monthlyCost"],
        "total_hourly_cost": ["totalHourlyCost", "hourlyCost"],
    }
    total_sum = 0
    matched_count = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if (
                        pointer[operation_type][0] in resource
                        and "name" in resource
                        and resource["name"].split(".")[0] in resource_type
                        and resource[pointer[operation_type][0]]
                        and resource[pointer[operation_type][0]] != "null"
                    ):
                        total_sum += float(resource[pointer[operation_type][0]])
                        matched_count += 1
                    elif (
                        pointer[operation_type][1] in resource
                        and "name" in resource
                        and resource["name"].split(".")[0] in resource_type
                        and resource[pointer[operation_type][1]]
                        and resource[pointer[operation_type][1]] != "null"
                    ):
                        total_sum += float(resource[pointer[operation_type][1]])
                        matched_count += 1
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                logger.debug(f"Total sum of {operation_type} of specific resources :  {total_sum}")
                return total_sum, matched_count
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def _is_every_resource(resource_type):
    """
    Whether the `resource_type` provider arg means "every resource".

    The same three spellings `provide` accepts, kept in one place so the message agrees with
    what was actually measured.

    :param resource_type: The `resource_type` provider arg
    :return:              True when the arg covers every resource
    """
    return not resource_type or resource_type == "*" or resource_type == ["*"]


def _describe_resource_type(resource_type):
    """
    Render the `resource_type` provider arg as the subject of a message.

    :param resource_type: The `resource_type` provider arg, a string or a list of strings
    :return:              A human-readable subject
    """
    if _is_every_resource(resource_type):
        return "all resources"
    if isinstance(resource_type, (list, tuple)):
        return ", ".join(str(item) for item in resource_type)
    return str(resource_type)


def _cost_context(operation_type, input_data, resource_type=None, matched_count=None):
    """
    Build the result context for a cost figure.

    A cost message used to be nothing but the comparison -- ```0` is less than `20``` -- which
    says neither which cost was measured nor what it covered. Two figures of the same size mean
    very different things depending on whether they are monthly or hourly, and a `resource_type`
    that matches nothing yields a genuine-looking 0 that quietly passes a `LessThan`. Both are
    named here.

    :param operation_type: The cost being measured, e.g. `total_monthly_cost`
    :param input_data:     The infracost breakdown, read for its currency
    :param resource_type:  The `resource_type` provider arg, or None for every resource
    :param matched_count:  How many resources contributed a cost, if known
    :return:               The context dictionary
    """
    context = {
        "operation_type": operation_type,
        "label": _describe_resource_type(resource_type),
        "attribute": operation_type,
    }
    if not _is_every_resource(resource_type):
        context["resource_type"] = resource_type
    if matched_count is not None:
        context["matched_resources"] = matched_count
        context["qualifier"] = f"{matched_count} resource{'' if matched_count == 1 else 's'}"
    currency = input_data.get("currency") if isinstance(input_data, dict) else None
    if currency:
        context["currency"] = currency
    return context


def provide(provider_args, input_data):
    logger.debug("infracost provider")
    logger.debug(f"infracost provider inputs : {provider_args}")
    operation_type = provider_args.get("operation_type")
    resource_type = provider_args.get("resource_type")
    try:
        if "resource_type" in provider_args and "operation_type" in provider_args:
            if _is_every_resource(resource_type):
                value, matched_count = __get_all_costs(operation_type, input_data)
                context = _cost_context(operation_type, input_data, matched_count=matched_count)
                return [{"value": value, "meta": None, "err": None, "context": context}]
            else:
                value, matched_count = __get_resources_costs(resource_type, operation_type, input_data)
                context = _cost_context(operation_type, input_data, resource_type, matched_count)
                return [{"value": value, "meta": None, "err": None, "context": context}]
        else:
            raise KeyError("resource_type/operation_type not found in provider_args")
    except KeyError as e:
        # Name what was being measured, so a missing `projects` key is not reported against a
        # policy the reader has to go and look up
        context = _cost_context(operation_type, input_data, resource_type) if operation_type else None
        return [{"value": None, "meta": None, "err": str(e), "context": context}]
