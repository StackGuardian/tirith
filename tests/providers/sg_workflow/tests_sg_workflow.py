import json
import os
import pytest

from sg_policy.providers.sg_workflow import handler


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/{json_path}", "r") as fp:
        return json.load(fp)


input_data = load_terraform_plan_json("input.json")
