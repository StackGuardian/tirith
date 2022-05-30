import re
import os
import json

def compareString(policydata, inputDataToBeScanned):
    result = re.fullmatch(policydata, inputDataToBeScanned)
    return result


def evaluate(ICPolicyPath, ICPayloadPath):
    if os.path.isfile(ICPolicyPath) and os.path.isfile(ICPayloadPath):

        ICPolicyFile = open(ICPolicyPath)
        ICPayloadFile = open(ICPayloadPath)

        ICPolicy = json.load(ICPolicyFile)
        ICPayload = json.load(ICPayloadFile)

        res = False
        errs = []

        targetTotalMonthlyCost = ICPayload.get("totalMonthlyCost")
        targetTotalHourlyCost = ICPayload.get("totalHourlyCost")

        checkMaximumTotalMonthlyCost = ICPolicy.get('maximumTotalMonthlyCost')
        checkMaximumTotalHourlyCost = ICPolicy.get('maximumTotalHourlyCost')

        if checkMaximumTotalMonthlyCost and targetTotalMonthlyCost:
            if float(targetTotalMonthlyCost) > float(checkMaximumTotalMonthlyCost):
                err_ = f"Total monthly cost is higher than than maximum configured in the policy"
                errs.append(err_)

        if checkMaximumTotalHourlyCost and targetTotalHourlyCost:
            if float(targetTotalHourlyCost) > float(checkMaximumTotalHourlyCost):
                err_ = f"Total hourly cost is higher than maximum configured in the policy"
                errs.append(err_)

        if not errs:
            res = True

        return {'Passed' : res , 'errs' : errs}

    else:
        return 'Paths provided are not correct'
