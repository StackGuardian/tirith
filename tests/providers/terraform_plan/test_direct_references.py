import json
import os
import pytest
import shutil

from subprocess import Popen
from tirith.core.core import start_policy_evaluation_from_dict


# TODO: Move these helper functions to a utils file
def is_on_github_actions():
    """
    Check if the tests are running on Github Actions or not
    """
    if "CI" not in os.environ or not os.environ["CI"] or "GITHUB_RUN_ID" not in os.environ:
        return False
    return True


def load_json_from_fixtures(json_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_path, "fixtures", json_path)) as f:
        return json.load(f)


def parse_json_file(file_path):
    with open(file_path) as f:
        return json.load(f)


def process_terraform_file_into_plan_dict(tf_filepath) -> dict:
    """
    Process .tf file into a plan dict

    :param tf_filepath: path to .tf file
    :return:            plan dict
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    test_tmp_dirpath = os.path.join(current_path, ".test_tmp")
    if not os.path.exists(test_tmp_dirpath):
        os.mkdir(test_tmp_dirpath)
    copied_tf_filepath = shutil.copy(tf_filepath, test_tmp_dirpath)
    Popen(
        f"terraform init && terraform plan -out=tfplan && terraform show -json tfplan > plan.json",
        cwd=test_tmp_dirpath,
        shell=True,
    ).wait()
    plan_dict = parse_json_file(os.path.join(test_tmp_dirpath, "plan.json"))
    os.remove(copied_tf_filepath)
    return plan_dict


def load_tf_plan_dict_from_fixtures(tf_plan_fixture_path):
    current_path = os.path.dirname(os.path.abspath(__file__))
    tf_path = os.path.join(current_path, "fixtures", tf_plan_fixture_path)
    return process_terraform_file_into_plan_dict(tf_path)


def tearDown():
    # TODO: Use this tearDown()
    current_path = os.path.dirname(os.path.abspath(__file__))
    test_tmp_dirpath = os.path.join(current_path, "test_tmp")
    shutil.rmtree(test_tmp_dirpath)


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_references_to_and_by_should_raise_error():
    """
    Test that a policy with both `references_to` and `referenced_by` raises an error
    """
    policy = load_json_from_fixtures("fail_s3_referenced_by_to.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("extra_elb_no_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["result"][0]["message"] == (
        "Only one of `referenced_by` or "
        "`references_to` must be provided in "
        "the provider input (severity_value: "
        "99))"
    )


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_references_to_should_fail():
    """
    Test that a policy with `references_to` fails when not all of the
    `terraform_resource_type` references to `references_to`
    """
    policy = load_json_from_fixtures("elb_references_to_secroup.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("extra_elb_no_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["passed"] == False


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_references_to_should_pass():
    """
    Test that a policy with `references_to` should pass when all of the
    `terraform_resource_type` references to `references_to`
    """
    policy = load_json_from_fixtures("elb_references_to_secroup.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("elb_with_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == True
    assert result["evaluators"][0]["passed"] == True


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_references_to_should_fail_when_no_resources_found():
    """
    Test that a policy with `references_to` should fail when
    `terraform_resource_type` isn't found
    """
    policy = load_json_from_fixtures("elb_references_to_secroup.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("s3_bucket_with_intelligent_tiering_config.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["passed"] == False


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_referenced_by_should_fail_when_the_resource_isnt_found():
    """
    Test that a policy with `references_by` should fail when
    `terraform_resource_type` is not found
    """
    policy = load_json_from_fixtures("s3_referenced_by_intelligent_tiering_config.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("elb_with_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["passed"] == False


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_referenced_by_should_skip_when_the_resource_isnt_found_err_tolerance():
    """
    Test that a policy with `references_by` should fail when
    `terraform_resource_type` is not found with `error_tolerance` set to 1
    """
    policy = load_json_from_fixtures("s3_referenced_by_intelligent_tiering_config_err_tolerance_1.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("elb_with_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == None
    assert result["evaluators"][0]["passed"] == None


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_referenced_by_should_fail():
    """
    Test that a policy with `references_by` should fail when one of the
    `terraform_resource_type` is not referenced by `referenced_by` res type
    """
    policy = load_json_from_fixtures("s3_referenced_by_intelligent_tiering_config.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("s3_bucket_not_all_has_intelligent_tiering.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["passed"] == False


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_direct_referenced_by_should_pass():
    """
    Test that a policy with `references_by` should pass when all of the
    `terraform_resource_type` are referenced by `referenced_by` res type
    """
    policy = load_json_from_fixtures("s3_referenced_by_intelligent_tiering_config.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("s3_bucket_with_intelligent_tiering_config.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == True
    assert result["evaluators"][0]["passed"] == True


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_old_direct_references_should_pass():
    """
    Test that the old way of specifying direct references still works
    (without any `references_to` and `referenced_by`)
    """
    policy = load_json_from_fixtures("at_least_one_aws_s3_bucket_int_config_refers_to_s3_bucket.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("s3_bucket_not_all_has_intelligent_tiering.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == True
    assert result["evaluators"][0]["passed"] == True


@pytest.mark.skipif(is_on_github_actions(), reason="Can't test using tf file on Github Actions")
def test_old_direct_references_should_fail_when_no_resource_type_is_found():
    """
    Test that the old way of specifying direct references still works
    (without any `references_to` and `referenced_by`)
    """
    policy = load_json_from_fixtures("at_least_one_aws_s3_bucket_int_config_refers_to_s3_bucket.tirith.json")
    tf_plan_dict = load_tf_plan_dict_from_fixtures("elb_with_secgroup.tf")

    result = start_policy_evaluation_from_dict(policy, tf_plan_dict)
    assert result["final_result"] == False
    assert result["evaluators"][0]["passed"] == False
    assert (
        result["evaluators"][0]["result"][0]["message"]
        == "resource_type: 'aws_s3_bucket_intelligent_tiering_configuration' is not found (severity_value: 1)"
    )
