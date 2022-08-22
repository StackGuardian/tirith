def getValue(key,data):
    result = []
    if key == 'integrationId':
        if 'DeploymentPlatformConfig' in data:
            for obj in data['DeploymentPlatformConfig']:
                if 'config' in obj and 'integrationId' in obj['config']:
                    result.append(obj['config']['integrationId'])
        else:
            raise KeyError('DeploymentPlatformConfig not found in input_data')

    elif key == 'Description':
        pass
    elif key == 'DocVersion':
        pass
    elif key == 'ResourceName':
        pass
    elif key == 'ResourceType':
        pass
    elif key == 'Tags':
        pass
    elif key == 'InputData':
        pass
    elif key == 'iacTemplateId':
        pass
    elif key == 'useMarketplaceTemplate':
        pass
    elif key == 'WfType':
        pass


def provide(provider_inputs, input_data):
    try:
        if 'resource_type' in provider_inputs and len(resource_type) > 0:
            resource_type = provider_inputs['resource_type']
            result = getValue(resource_type,input_data)
            return [{'value': result, 'meta': None, 'err': None}]
        else:
            raise KeyError('resource_type not found in provider_inputs')
    except KeyError as e:
        return [{'value': None, 'meta': None, 'err': str(e)}]
