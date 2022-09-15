import json
import os
import pytest

from sg_policy.providers.sg_workflow import handler


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_terraform_plan_json("input.json")
import json
import os
import pytest

from sg_policy.providers.sg_workflow import handler


def load_sg_workflow_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_sg_workflow_plan_json("input.json")

#----------------------------------------------------------------------------- 

provider_args_1 = {
    "workflow_attribute": "ResourceType",
}

def test_resource_type_pass():
    res = handler.provide(provider_args_1,input_data)
    assert bool(res[0]["value"] == "WORKFLOW") == True


def test_resource_type_fail():
    res = handler.provide(provider_args_1,input_data)
    assert bool(res[0]["value"] != "WORKFLOW") == False

#----------------------------------------------------------------------------- 

provider_args_2 = {
    "workflow_attribute": "WfType",
}

def test_wftype_pass():
    res = handler.provide(provider_args_2,input_data)
    assert bool(res[0]["value"] == "TERRAFORM") == True


def test_wftype_fail():
    res = handler.provide(provider_args_2,input_data)
    assert bool(res[0]["value"] != "TERRAFORM") == False

#----------------------------------------------------------------------------- 

provider_args_3 = {
    "workflow_attribute": "approvalPreApply",
}

def test_approval_pre_apply_pass():
    res = handler.provide(provider_args_3,input_data)
    assert bool(res[0]["value"] == True) == True


def test_approval_pre_apply_fail():
    res = handler.provide(provider_args_3,input_data)
    assert bool(res[0]["value"] != True) == False

#condition coming false means value is true therefore test pass, not so test fail

#----------------------------------------------------------------------------- 
provider_args_4 = {
    "workflow_attribute": "driftCheck",
}
def test_drift_check_pass():
    res = handler.provide(provider_args_4,input_data)
    assert bool(res[0]["value"] == False) == True


def test_drift_check_fail():
    res = handler.provide(provider_args_4,input_data)
    assert bool(res[0]["value"] == True) == False
#----------------------------------------------------------------------------- 
provider_args_5 = {
    "workflow_attribute": "managedTerraformState",
}
def test_managed_terraform_state_pass():
    res = handler.provide(provider_args_5,input_data)
    assert bool(res[0]["value"] == True) == True

def test_managed_terraform_state_fail():
    res = handler.provide(provider_args_5,input_data)
    assert bool(res[0]["value"] != True) == False

#----------------------------------------------------------------------------- 

provider_args_8 = {
    "workflow_attribute": "s3_bucket_acl",
}

def test_s3_bucket_acl_pass():
    res = handler.provide(provider_args_8,input_data)
    assert bool(res[0]["value"] == "public-read") == True


def test_s3_bucket_acl_fail():
    res = handler.provide(provider_args_8,input_data)
    assert bool(res[0]["value"] != "public-read") == False

#----------------------------------------------------------------------------- 

provider_args_9 = {
    "workflow_attribute": "s3_bucket_block_public_acls",
}

def test_s3_bucket_block_public_acl_pass():
    res = handler.provide(provider_args_9,input_data)
    assert bool(res[0]["value"] == False) == True


def test_s3_bucket_block_public_acl_fail():
    res = handler.provide(provider_args_9,input_data)
    assert bool(res[0]["value"] == True) == False
#----------------------------------------------------------------------------- 

provider_args_10 = {
    "workflow_attribute": "s3_bucket_block_public_policy",
}

def test_s3_bucket_block_public_policy_pass():
    res = handler.provide(provider_args_10,input_data)
    assert bool(res[0]["value"] == False) == True


def test_s3_bucket_block_public_policy_fail():
    res = handler.provide(provider_args_10,input_data)
    assert bool(res[0]["value"] == True) == False
#----------------------------------------------------------------------------- 

provider_args_11 = {
    "workflow_attribute": "s3_bucket_force_destroy",
}

def test_s3_bucket_force_destroy_pass():
    res = handler.provide(provider_args_11,input_data)
    assert bool(res[0]["value"] == True) == True

def test_s3_bucket_force_destroy_fail():
    res = handler.provide(provider_args_11,input_data)
    assert bool(res[0]["value"] != True) == False

#----------------------------------------------------------------------------- 

provider_args_12 = {
    "workflow_attribute": "s3_bucket_ignore_public_acls",
}

def test_s3_bucket_ignore_pass():
    res = handler.provide(provider_args_12,input_data)
    assert bool(res[0]["value"] == False) == True

def test_s3_bucket_ignore_fail():
    res = handler.provide(provider_args_12,input_data)
    assert bool(res[0]["value"] == True) == False

#-----------------------------------------------------------------------------
#  
provider_args_13 = {
    "workflow_attribute": "s3_bucket_restrict_public_buckets",
}

def test_s3_bucket_restrict_passing():
    res = handler.provide(provider_args_13,input_data)
    assert bool(res[0]["value"] == False) == True


def test_s3_bucket_restrict_failing():
    res = handler.provide(provider_args_13,input_data)
    assert bool(res[0]["value"] == True) == False

#----------------------------------------------------------------------------- 
provider_args_14 = {
    "workflow_attribute": "useMarketplaceTemplate",
}

def test_use_marketplace_template_passing():
    res = handler.provide(provider_args_14,input_data)
    assert bool(res[0]["value"] == True) == True


def test_use_marketplace_template_failing():
    res = handler.provide(provider_args_14,input_data)
    assert bool(res[0]["value"] != True) == False

