def __get_all_costs(costType, input_data):
    totalSum = 0
    if "projects" not in input_data:
        raise KeyError("projects not found in input_data")

    for project in input_data["projects"]:
        if "breakdown" not in project or "resources" not in project["breakdown"]:
            raise KeyError("breakdown/resources not found in one of the project")
       
        for resource in project["breakdown"]["resources"]:
                if costType in resource and resource[costType] != "null":
                    totalSum += float(resource[costType])
        return totalSum
   


def __get_resources_costs(resource_type, costType, input_data):
    totalSum = 0
    if "projects" not in input_data:
        raise KeyError("projects not found in input_data")

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
        


def provide(provider_inputs, input_data):
    try:
        if "resource_type" not in provider_inputs or "costType" not in provider_inputs:
            raise KeyError("resource_type/costType not found in provider_inputs")

        resource_type = provider_inputs["resource_type"]
        costType = provider_inputs["costType"]
        if not resource_type or resource_type == "*" or resource_type == ["*"]:
            value = __get_all_costs(costType, input_data)
        else:
            value = __get_resources_costs(resource_type, costType, input_data)
        return [{"value": value, "meta": None, "err": None}]
        
    except KeyError as e:
        return [{"value": None, "meta": None, "err": str(e)}]
