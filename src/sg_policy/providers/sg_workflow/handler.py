def __getValue(key, data):
    result = ""
    if key == "integrationId":
        temp = []
        if "DeploymentPlatformConfig" in data:
            for obj in data["DeploymentPlatformConfig"]:
                if "config" in obj and "integrationId" in obj["config"]:
                    temp.append(obj["config"]["integrationId"].replace("/integrations/", ""))
            result = temp
        else:
            raise KeyError("DeploymentPlatformConfig not found in input_data")

    elif key in [
        "Description",
        "DocVersion",
        "ResourceName",
        "ResourceType",
        "Tags",
        "WfType",
    ]:
        if key in data:
            result = data.get(key)
        else:
            raise KeyError(f"{key} not found in input_data")

    elif key in [
        "approvalPreApply",
        "driftCheck",
        "managedTerraformState",
        "terraformVersion",
    ]:
        if "TerraformConfig" in data and key in data["TerraformConfig"]:
            result = data["TerraformConfig"][key]
        else:
            raise KeyError(f"{key} not found in input_data")

    elif key in [
        "bucket_region",
        "s3_bucket_acl",
        "s3_bucket_block_public_acls",
        "s3_bucket_block_public_policy",
        "s3_bucket_force_destroy",
        "s3_bucket_ignore_public_acls",
        "s3_bucket_restrict_public_buckets",
    ]:
        if (
            "VCSConfig" in data
            and "iacInputData" in data["VCSConfig"]
            and "data" in data["VCSConfig"]["iacInputData"]
            and key in data["VCSConfig"]["iacInputData"]["data"]
        ):
            result = data["VCSConfig"]["iacInputData"][data][key]
        else:
            raise KeyError(f"{key} not found in input_data")

    elif key in ["iacTemplateId", "useMarketplaceTemplate"]:
        if "iacVCSConfig" in data and key in data["iacVCSConfig"]:
            result = data["iacVCSConfig"][key]
        else:
            raise KeyError(f"{key} not found in input_data")

    return result


def provide(provider_inputs, input_data):
    try:
        if "resource_type" in provider_inputs:
            resource_type = provider_inputs["resource_type"]
            if resource_type:
                result = __getValue(resource_type, input_data)
                return [{"value": result, "meta": None, "err": None}]
        else:
            return [
                {
                    "value": None,
                    "meta": None,
                    "err": f"resource_type not found in provider_inputs",
                }
            ]
    except Exception as e:
        # TODO: Log exception as debug log
        return [{"value": None, "meta": None, "err": str(e)}]
