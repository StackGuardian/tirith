import json
import os


def load_terraform_plan_json(json_path):
    with open(f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/{json_path}", "r") as fp:
        return json.load(fp)
