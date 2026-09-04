"""Discovery of policy files for `tirith lint` and `tirith fmt`."""

import json
import os

from tirith.policyfiles import collect, looks_like_policy

POLICY = {
    "meta": {"version": "v1", "required_provider": "stackguardian/terraform_plan"},
    "evaluators": [
        {
            "id": "a",
            "provider_args": {
                "operation_type": "attribute",
                "terraform_resource_type": "*",
                "terraform_resource_attribute": "tags",
            },
            "condition": {"type": "IsNotEmpty"},
        }
    ],
    "eval_expression": "a",
}
PLAN = {"format_version": "1.2", "resource_changes": []}


def _write(path, document):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(document, f)
    return path


def test_looks_like_policy_needs_one_of_the_engine_keys():
    assert looks_like_policy(POLICY)
    assert looks_like_policy({"meta": {}})
    assert not looks_like_policy(PLAN)
    assert not looks_like_policy([POLICY])
    assert not looks_like_policy("meta")


def test_a_directory_walk_finds_policies_and_ignores_the_plans_beside_them(tmp_path):
    root = str(tmp_path)
    _write(os.path.join(root, "a", "policy.json"), POLICY)
    _write(os.path.join(root, "a", "input.json"), PLAN)
    _write(os.path.join(root, "b", "policy.json"), POLICY)
    _write(os.path.join(root, "notes.txt"), {})  # not .json, never opened

    collected = collect([root])

    assert [os.path.relpath(p.path, root) for p in collected.policies] == ["a/policy.json", "b/policy.json"]
    assert collected.ignored == 1
    assert collected.skipped == []
    assert collected.missing == []


def test_an_explicitly_named_non_policy_is_reported_not_ignored(tmp_path):
    plan = _write(os.path.join(str(tmp_path), "plan.json"), PLAN)

    collected = collect([plan])

    assert collected.policies == []
    assert collected.skipped == [plan]
    assert collected.ignored == 0


def test_invalid_json_inside_a_policy_directory_is_a_policy_with_an_error(tmp_path):
    root = str(tmp_path)
    bad = os.path.join(root, "broken.json")
    with open(bad, "w") as f:
        f.write('{"meta": ')

    (policy_file,) = collect([root]).policies

    assert policy_file.path == bad
    assert policy_file.document is None
    assert "not valid JSON" in policy_file.error


def test_missing_paths_are_listed_and_the_rest_still_collected(tmp_path):
    good = _write(os.path.join(str(tmp_path), "policy.json"), POLICY)

    collected = collect([good, os.path.join(str(tmp_path), "nope")])

    assert [p.path for p in collected.policies] == [good]
    assert collected.missing == [os.path.join(str(tmp_path), "nope")]


def test_skipped_directories_are_not_descended(tmp_path):
    root = str(tmp_path)
    _write(os.path.join(root, "node_modules", "x", "policy.json"), POLICY)
    _write(os.path.join(root, ".git", "policy.json"), POLICY)
    _write(os.path.join(root, ".tirith", "policies", "policy.json"), POLICY)

    collected = collect([root])

    assert [os.path.relpath(p.path, root) for p in collected.policies] == [".tirith/policies/policy.json"]


def test_no_paths_means_the_conventional_directory_when_present(tmp_path, monkeypatch):
    root = str(tmp_path)
    _write(os.path.join(root, ".tirith", "policies", "p.json"), POLICY)
    _write(os.path.join(root, "elsewhere.json"), POLICY)
    monkeypatch.chdir(root)

    collected = collect([])

    assert [os.path.relpath(p.path, root) for p in collected.policies] == [".tirith/policies/p.json"]


def test_no_paths_falls_back_to_the_current_directory(tmp_path, monkeypatch):
    root = str(tmp_path)
    _write(os.path.join(root, "elsewhere.json"), POLICY)
    monkeypatch.chdir(root)

    collected = collect([])

    assert [os.path.basename(p.path) for p in collected.policies] == ["elsewhere.json"]


def test_the_same_file_reached_twice_is_collected_once(tmp_path):
    root = str(tmp_path)
    policy = _write(os.path.join(root, "policy.json"), POLICY)

    collected = collect([root, policy])

    assert len(collected.policies) == 1
