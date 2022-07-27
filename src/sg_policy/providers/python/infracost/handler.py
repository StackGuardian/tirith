
def getValuesFromAll(costType,input_data):
    totalSum = 0
    projects = input_data["projects"]
    for project in projects:
        resources = project['breakdown']['resources']
        for resource in resources:
            if resource[costType] != "null":
                totalSum += float(resource[costType])
    return totalSum



def getValuesFromSet(resource_type,costType,input_data):
    totalSum = 0
    projects = input_data["projects"]
    for project in projects:
        resources = project['breakdown']['resources']
        for resource in resources:
            if resource[costType] != "null" and resource[name] in resource_type:
                totalSum += float(resource[costType])
    return totalSum


def initialize(provider_inputs, input_data):
    resource_type = provider_inputs['resource_type']
    costType = provider_inputs['costType']
    if len(resource_type)==0 or resource_type=='*' or resource_type == ["*"]:
        value = getValuesFromAll(costType,input_data)
        return value
    else:
        value = getValuesFromSet(resource_type,costType,input_data)
        return value




