import re
import os
import json

def compareString(policydata, inputDataToBeScanned):
    result = re.fullmatch(policydata, inputDataToBeScanned)
    return result


def evaluate(wfPolicyPath, wfPayloadPath):
    if os.path.isfile(wfPolicyPath) and os.path.isfile(wfPayloadPath):

        wfPolicyFile = open(wfPolicyPath)
        wfPayloadFile = open(wfPayloadPath)

        wfPolicy = json.load(wfPolicyFile)
        wfPayload = json.load(wfPayloadFile)

        res = False
        errs = []
        for polKey, val in wfPolicy.items():
            polKey = polKey.split("__")[0]
            policyVal = val
            targetVal = wfPayload.get(polKey)

            if targetVal is None:
                continue

            if polKey == "WfType":
                for item in policyVal:
                    result = compareString(item, targetVal)

                    if result is None:
                        # err_ = f"Value error for key {key} : {targetVal}"
                        err_ = {
                            "Workflow Type": f"allowed value(s) are {policyVal}"
                        }
                        errs.append(err_)
                        break

            if polKey == "TerraformConfig":
                for key_config, val_config in policyVal.items():
                    keyForConfig = key_config.split("__")[0]
                    policyValForConfig = val_config
                    from copy import deepcopy

                    allowedValues = deepcopy(val_config)
                    targetValForConfig = wfPayload.get(polKey)[keyForConfig]
                    keyValMap = {
                        "approvalPreApply": "Plan Approval",
                        "managedTerraformState": "Managed Terraform State",
                        "driftCheck": "Automated Drift Check",
                    }

                    if targetValForConfig is None:
                        continue
                    else:
                        if keyForConfig == "terraformVersion":
                            # check terraformVersion string

                            while policyValForConfig:
                                item = policyValForConfig.pop()
                                result = compareString(item, targetValForConfig)
                                if result is None and not policyValForConfig:
                                    err_ = {
                                        "Terraform Version": f"allowed value(s) are {allowedValues}"
                                    }
                                    errs.append(err_)
                                    break
                                if result:
                                    break
                        else:
                            # check all the boolean values for approvalPreApply
                            if targetValForConfig not in policyValForConfig:
                                err_ = {
                                    keyValMap.get(
                                        keyForConfig, keyForConfig
                                    ): f"allowed value(s) are {policyValForConfig}"
                                }
                                errs.append(err_)
                                break

            if polKey == "ResourceName":
                for item in policyVal:
                    result = compareString(item, targetVal)
                    if result is None:
                        err_ = {
                            "Workflow Name": f"allowed value(s) are {policyVal}"
                        }
                        errs.append(err_)
                        break

            # TODO: Logic fix required
            # if polKey == "Tags":
            #     for item in policyVal:
            #         for check in targetVal:
            #             result = compareString(item, check)
            #             if result is None:
            #                 err_ = {"Tags": f"allowed value(s) are {policyVal}"}
            #                 errs.append(err_)
            #                 break
            if polKey == "VCSConfig":
                policyVal = wfPolicy[polKey]["iacVCSConfig"]
                targetValForConfig = wfPayload.get(polKey)["iacVCSConfig"]
                if targetValForConfig is None:
                    continue
                else:
                    for key_config, val_config in policyVal.items():
                        keyForConfig = key_config.split("__")[0]
                        policyValForConfig = val_config
                        targetValForConfig = wfPayload.get(polKey)[
                            "iacVCSConfig"
                        ].get(keyForConfig)
                        if targetValForConfig is None:
                            continue
                        else:
                            if keyForConfig == "iacTemplateId":
                                for item in policyValForConfig:
                                    result = compareString(item, targetValForConfig)
                                    if result is None:
                                        err = {
                                            "IaC Template": f"allowed value(s) are {policyValForConfig}"
                                        }
                                        errs.append(err)
                                        break

                            if keyForConfig == "useMarketplaceTemplate":
                                if targetValForConfig not in policyValForConfig:
                                    err = {
                                        "Use Marketplace IAC Template": f"allowed value(s) are {policyValForConfig}"
                                    }
                                    errs.append(err)
                                    break

        if not errs:
            res = True

        return {'Passed' : res , 'errs' : errs}

    else:
        return 'Paths provides are not correct'
