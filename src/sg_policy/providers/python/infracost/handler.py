def __get_all_costs(costType, input_data):
    totalSum = 0
    if 'projects' in input_data:
        for project in input_data.get("projects"):
            if 'breakdown' in project and 'resources' in project.get('breakdown'):
                for resource in project.get('breakdown').get('resources'):
                    if resource[costType] != "null":
                        totalSum += float(resource[costType])
                return totalSum
            else:
                raise KeyError('key not found in one of the project')
    else:
        raise KeyError('projects key not found in input_data')


def __get_resources_costs(resource_type, costType, input_data):
    totalSum = 0
    if 'projects' in input_data:
        for project in input_data.get("projects"):
            if 'breakdown' in project and 'resources' in project.get('breakdown'):
                for resource in project.get('breakdown').get('resources'):
                    if resource[costType] != "null" and resource['name'] in resource_type:
                        totalSum += float(resource[costType])
                return totalSum
            else:
                raise KeyError('key not found in one of the project')
    else:
        raise KeyError('projects key not found in input_data')


def provide(provider_inputs, input_data):
    try:
        if 'resource_type' in provider_inputs and 'costType' in provider_inputs:
            resource_type = provider_inputs.get('resource_type')
            costType = provider_inputs.get('costType')
            if not resource_type or resource_type == '*' or resource_type == ["*"]:
                value = __get_all_costs(costType, input_data)
                return [{'value': value}]
            else:
                value = __get_resources_costs(resource_type, costType, input_data)
                return [{'value': value}]
        else:
            raise KeyError('key not found in provider_inputs')
    except KeyError as e:
        print(e)
        return None

