def __get_all_costs(costType, input_data):
    totalSum = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if costType in resource and resource[costType] != "null":
                        totalSum += float(resource[costType])
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                return totalSum
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def __get_resources_costs(resource_type, costType, input_data):
    totalSum = 0
    if "projects" in input_data:
        for project in input_data["projects"]:
            if "breakdown" in project and "resources" in project["breakdown"]:
                for resource in project["breakdown"]["resources"]:
                    if (
                        costType in resource
                        and "name" in resource
                        and resource[costType] != "null"
                        and resource["name"] in resource_type
                    ):
                        totalSum += float(resource[costType])
                    else:
                        pass
                        # raise KeyError(f'{costType} not found in one of the resource')
                return totalSum
            else:
                raise KeyError("breakdown/resources not found in one of the project")
    else:
        raise KeyError("projects not found in input_data")


def provide(provider_inputs, input_data):
    try:
        if "resource_type" in provider_inputs and "costType" in provider_inputs:
            resource_type = provider_inputs["resource_type"]
            costType = provider_inputs["costType"]
            if not resource_type or resource_type == "*" or resource_type == ["*"]:
                value = __get_all_costs(costType, input_data)
                return [{"value": value, "meta": None, "err": None}]
            else:
                value = __get_resources_costs(resource_type, costType, input_data)
                return [{"value": value, "meta": None, "err": None}]
        else:
            raise KeyError("resource_type/costType not found in provider_inputs")
    except KeyError as e:
        return [{"value": None, "meta": None, "err": str(e)}]
