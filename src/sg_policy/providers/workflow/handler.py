def getValue(key, data):
    result = ''
    if key == 'integrationId':
        temp = []
        if 'DeploymentPlatformConfig' in data:
            for obj in data['DeploymentPlatformConfig']:
                if 'config' in obj and 'integrationId' in obj['config']:
                    temp.append(obj['config']['integrationId'])
            result = tmp
        else:
            raise KeyError('DeploymentPlatformConfig not found in input_data')

    elif key == 'Description' or key == 'DocVersion' or key == 'ResourceName' or key == 'ResourceType' or key == 'Tags' or key == 'WfType':
        if key in data:
            result = data[key]
        else:
            raise KeyError(f'{key} not found in input_data')

    elif key == 'approvalPreApply' or key == 'driftCheck' or key == 'managedTerraformState' or key == 'terraformVersion':
        if 'TerraformConfig' in data and key in data['TerraformConfig']:
            result = data['TerraformConfig'][key]
        else:
            raise KeyError(f'{key} not found in input_data')

    elif key == 'bucket_region' or key == 's3_bucket_acl' or key == 's3_bucket_block_public_acls' or key == 's3_bucket_block_public_policy' or key == 's3_bucket_force_destroy' or key == 's3_bucket_ignore_public_acls' or key == 's3_bucket_restrict_public_buckets':
        if 'VCSConfig' in data and 'iacInputData' in data['VCSConfig'] and 'data' in data['VCSConfig']['iacInputData'] and key in data['VCSConfig']['iacInputData']['data']:
            result = data['VCSConfig']['iacInputData'][data][key]
        else:
            raise KeyError(f'{key} not found in input_data')

    elif key == 'iacTemplateId' or key == 'useMarketplaceTemplate':
        if 'iacVCSConfig' in data and key in data['iacVCSConfig']:
            result = data['iacVCSConfig'][key]
        else:
            raise KeyError(f'{key} not found in input_data')

    return result


def provide(provider_inputs, input_data):
    try:
        if 'resource_type' in provider_inputs and len(provider_inputs['resource_type']) > 0:
            resource_type = provider_inputs['resource_type']
            result = getValue(resource_type, input_data)
            return [{'value': result, 'meta': None, 'err': None}]
        else:
            raise KeyError('resource_type not found in provider_inputs')
    except KeyError as e:
        return [{'value': None, 'meta': None, 'err': str(e)}]
