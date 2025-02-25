from tirith.providers.terraform_plan import handler


def test_count_with_indexed_resources():
    plan = {
        "resource_changes": [
            {"type": "aws_s3_bucket", "index": 0},
            {"type": "aws_s3_bucket", "index": 1},
            {"type": "aws_s3_bucket", "index": 2},
        ]
    }
    provider_args = {"operation_type": "count", "terraform_resource_type": "aws_s3_bucket"}
    result = handler.provide(provider_args, plan)

    assert len(result) == 1
    assert result[0]["value"] == 3


def test_count_with_non_indexed_resources():
    plan = {
        "resource_changes": [
            {"type": "aws_s3_bucket"},
            {"type": "aws_s3_bucket"},
        ]
    }
    provider_args = {"operation_type": "count", "terraform_resource_type": "aws_s3_bucket"}
    result = handler.provide(provider_args, plan)

    assert len(result) == 1
    assert result[0]["value"] == 2


def test_count_with_mixed_resources():
    plan = {
        "resource_changes": [
            {"type": "aws_s3_bucket", "index": 0},
            {"type": "aws_s3_bucket"},
            {"type": "aws_s3_bucket", "index": 1},
        ]
    }
    provider_args = {"operation_type": "count", "terraform_resource_type": "aws_s3_bucket"}
    result = handler.provide(provider_args, plan)

    assert len(result) == 1
    assert result[0]["value"] == 3


def test_count_with_star_resource_type():
    plan = {
        "resource_changes": [
            {"type": "aws_s3_bucket", "index": 0},
            {"type": "aws_instance"},
            {"type": "aws_vpc", "index": 1},
        ]
    }
    provider_args = {"operation_type": "count", "terraform_resource_type": "*"}
    result = handler.provide(provider_args, plan)

    assert len(result) == 1
    assert result[0]["value"] == 3


def test_count_with_non_existent_resource():
    plan = {
        "resource_changes": [
            {"type": "aws_s3_bucket", "index": 0},
            {"type": "aws_instance"},
        ]
    }
    provider_args = {"operation_type": "count", "terraform_resource_type": "aws_vpc"}
    result = handler.provide(provider_args, plan)

    assert len(result) == 1
    assert result[0]["value"] == 0
