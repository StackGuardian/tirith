def __get_all_costs(costType, input_data):
    totalSum = 0
    projects = input_data.get("projects")
    if projects is not None:
        for project in projects:
            breakdown = project.get('breakdown')
            if breakdown is not None:
                resources = breakdown.get('resources')
                if resources is not None:
                    for resource in resources:
                        if resource[costType] != "null":
                            totalSum += float(resource[costType])
                    return totalSum


def __get_resources_costs(resource_type, costType, input_data):
    totalSum = 0
    projects = input_data.get("projects")
    if projects is not None:
        for project in projects:
            breakdown = project.get('breakdown')
            if breakdown is not None:
                resources = breakdown.get('resources')
                if resources is not None:
                    for resource in resources:
                        if resource[costType] != "null" and resource[name] in resource_type:
                            totalSum += float(resource[costType])
                    return totalSum


def provide(provider_inputs, input_data):
    try:
        resource_type = provider_inputs.get('resource_type')
        costType = provider_inputs.get('costType')
        if resource_type is not None and costType is not None:
            if not resource_type or resource_type == '*' or resource_type == ["*"]:
                value = getValuesFromAll(costType, input_data)
                return [{'value': value}]
            else:
                value = getValuesFromSet(resource_type, costType, input_data)
                return [{'value': value}]
    except Exception as e:
        print(e)
        return None

