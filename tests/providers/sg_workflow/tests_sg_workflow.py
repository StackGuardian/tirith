import json
import os
import pytest

from sg_policy.providers.sg_workflow import handler


def load_sg_workflow_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_sg_workflow_plan_json("input.json")



provider_args_1 = {
    "resource_type": "ResourceType",
}

def test_case_passing_1():
    res = handler.provide(provider_args_1,input_data)
    assert bool(res[0]["value"] == "WORKFLOW") == True


def test_case_failing_1():
    res = handler.provide(provider_args_1,input_data)
    assert bool(res[0]["value"] != "WORKFLOW") == False

#----------------------------------------------------------------------------- 

provider_args_2 = {
    "resource_type": "WfType",
}

def test_case_passing_2():
    res = handler.provide(provider_args_2,input_data)
    assert bool(res[0]["value"] == "TERRAFORM") == True


def test_case_failing_2():
    res = handler.provide(provider_args_2,input_data)
    assert bool(res[0]["value"] != "TERRAFORM") == False

#----------------------------------------------------------------------------- 

provider_args_3 = {
    "resource_type": "approvalPreApply",
}

def test_case_passing_3():
    res = handler.provide(provider_args_3,input_data)
    assert bool(res[0]["value"] == True) == True


def test_case_failing_3():
    res = handler.provide(provider_args_3,input_data)
    assert bool(res[0]["value"] != True) == True


#----------------------------------------------------------------------------- 
provider_args_4 = {
    "resource_type": "driftCheck",
}
def test_case_passing_4():
    res = handler.provide(provider_args_4,input_data)
    assert bool(res[0]["value"] == False) == True


def test_case_failing_4():
    res = handler.provide(provider_args_4,input_data)
    assert bool(res[0]["value"] != False) == False
#----------------------------------------------------------------------------- 
provider_args_5 = {
    "resource_type": "managedTerraformState",
}
def test_case_passing_5():
    res = handler.provide(provider_args_5,input_data)
    assert bool(res[0]["value"] == True) == True

def test_case_failing_5():
    res = handler.provide(provider_args_5,input_data)
    assert bool(res[0]["value"] != True) == False

#----------------------------------------------------------------------------- 
# Problem in handler
provider_args_8 = {
    "resource_type": "s3_bucket_acl",
}

def test_case_passing_8():
    res = handler.provide(provider_args_8,input_data)
    assert bool(res[0]["value"] == "public-read") == True


def test_case_failing_8():
    res = handler.provide(provider_args_8,input_data)
    assert bool(res[0]["value"] != "public-read") == False

#----------------------------------------------------------------------------- 
# Problem in handler
provider_args_9 = {
    "resource_type": "s3_bucket_block_public_acls",
}

def test_case_passing_9():
    res = handler.provide(provider_args_9,input_data)
    assert bool(res[0]["value"] == False) == True


def test_case_failing_9():
    res = handler.provide(provider_args_9,input_data)
    assert bool(res[0]["value"] != False) == True
#----------------------------------------------------------------------------- 
# Problem in handler
provider_args_10 = {
    "resource_type": "s3_bucket_block_public_policy",
}

def test_case_passing_10():
    res = handler.provide(provider_args_10,input_data)
    assert bool(res[0]["value"] == False) == True


def test_case_failing_10():
    res = handler.provide(provider_args_10,input_data)
    assert bool(res[0]["value"] != False) == True
#----------------------------------------------------------------------------- 
# Problem in handler
provider_args_11 = {
    "resource_type": "s3_bucket_force_destroy",
}

def test_case_passing_11():
    res = handler.provide(provider_args_11,input_data)
    assert bool(res[0]["value"] == True) == True

def test_case_failing_11():
    res = handler.provide(provider_args_11,input_data)
    assert bool(res[0]["value"] != True) == True

#----------------------------------------------------------------------------- 
# Problem in handler
provider_args_12 = {
    "resource_type": "s3_bucket_ignore_public_acls",
}

def test_case_passing_12():
    res = handler.provide(provider_args_12,input_data)
    assert bool(res[0]["value"] == False) == True

def test_case_failing_12():
    res = handler.provide(provider_args_12,input_data)
    assert bool(res[0]["value"] != False) == True

#-----------------------------------------------------------------------------
# # Problem in handler 
provider_args_13 = {
    "resource_type": "s3_bucket_restrict_public_buckets",
}

def test_case_passing_13():
    res = handler.provide(provider_args_13,input_data)
    assert bool(res[0]["value"] == False) == True


def test_case_failing_13():
    res = handler.provide(provider_args_13,input_data)
    assert bool(res[0]["value"] != False) == True
#----------------------------------------------------------------------------- 
provider_args_14 = {
    "resource_type": "useMarketplaceTemplate",
}

def test_case_passing_14():
    res = handler.provide(provider_args_14,input_data)
    assert bool(res[0]["value"] == True) == True


def test_case_failing_14():
    res = handler.provide(provider_args_14,input_data)
    assert bool(res[0]["value"] != True) == False

#----------------------------------------------------------------------------- 
# provider_args_15 = {
#     "resource_type": "iacTemplateId",
# }

#----------------------------------------------------------------------------- 
# provider_args_6 = {
#     "resource_type": "terraformVersion",
# }

# provider_args_7 = {
#     "resource_type": "bucket_region",
# }
