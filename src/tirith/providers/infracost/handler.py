import logging

# TODO: Add at least __name__ as the name of the logger
logger = logging.getLogger()


def __get_all_costs(operation_type, input_data):
    logger.debug(f"costType :  {operation_type}")
    pointer = {"total_monthly_cost": "totalMonthlyCost", "total_hourly_cost": "totalHourlyCost"}
    totalSum = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if pointer[operation_type] in resource and resource[pointer[operation_type]] != "null":
                        totalSum += float(resource[pointer[operation_type]])
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                logger.debug(f"Total sum of {operation_type} of all resources :  {totalSum}")
                return totalSum
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def __get_resources_costs(resource_type, operation_type, input_data):
    logger.debug(f"costType :  {operation_type}")
    pointer = {"total_monthly_cost": "totalMonthlyCost", "total_hourly_cost": "totalHourlyCost"}
    totalSum = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if (
                        pointer[operation_type] in resource
                        and "name" in resource
                        and resource[pointer[operation_type]] != "null"
                        and resource["name"] in resource_type
                    ):
                        totalSum += float(resource[pointer[operation_type]])
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                logger.debug(f"Total sum of {operation_type} of specific resources :  {totalSum}")
                return totalSum
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def provide(provider_args, input_data):
    logger.debug("infracost provider")
    logger.debug(f"infracost provider inputs : {provider_args}")
    try:
        if "resource_type" in provider_args and "operation_type" in provider_args:
            resource_type = provider_args["resource_type"]
            operation_type = provider_args["operation_type"]
            if not resource_type or resource_type == "*" or resource_type == ["*"]:
                value = __get_all_costs(operation_type, input_data)
                output = [{"value": value, "meta": None, "err": None}]
                return output
            else:
                value = __get_resources_costs(resource_type, operation_type, input_data)
                return [{"value": value, "meta": None, "err": None}]
        else:
            raise KeyError("resource_type/operation_type not found in provider_args")
    except KeyError as e:
        return [{"value": None, "meta": None, "err": str(e)}]
