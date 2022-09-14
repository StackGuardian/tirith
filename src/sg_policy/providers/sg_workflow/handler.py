import logging

# TODO: Add at least __name__ as the name of the logger
logger = logging.getLogger()


def __getValue(key, data):
    logger.debug(f"Searching {key} in input data")
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
            result = data["VCSConfig"]["iacInputData"]["data"][key]
        else:
            raise KeyError(f"{key} not found in input_data")

    elif key in ["iacTemplateId", "useMarketplaceTemplate"]:
        if "VCSConfig" in data and "iacVCSConfig" in data["VCSConfig"] and key in data["VCSConfig"]["iacVCSConfig"]:
            result = data["VCSConfig"]["iacVCSConfig"][key]
        else:
            raise KeyError(f"{key} not found in input_data")

    logger.debug(f"Result obtained through __getValue method : {result}")
    return result


def provide(provider_args, input_data):
    logger.debug("sg_workflow provider")
    logger.debug(f"sg_workflow provider inputs : {provider_args}")
    try:
        if "workflow_attribute" in provider_args:
            workflow_attribute = provider_args["workflow_attribute"]
            if workflow_attribute:
                result = __getValue(workflow_attribute, input_data)
                output = [{"value": result, "meta": None, "err": None}]
                return output
        else:
            logger.debug("workflow_attribute not found in provider_args")
            return [
                {
                    "value": None,
                    "meta": None,
                    "err": f"workflow_attribute not found in provider_args",
                }
            ]
    except Exception as e:
        logger.exception(e)
        return [{"value": None, "meta": None, "err": str(e)}]
