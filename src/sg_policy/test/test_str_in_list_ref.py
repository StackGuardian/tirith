import json

import pytest
import os
from time import time
import atexit
from time import time, strftime, localtime
from datetime import timedelta
import pandas as pd
from decimal import Decimal


def test_evaluationresult_handler():
    para = []
    para_input = [
        {
            "evaluator_data": [{"name": "fail"}],
            "input_data": [
                {
                    "rule_no": {"key": {"value": {"hello": 11}}},
                    "action": "allow",
                    "from_port": "0",
                    "to_port": 0,
                    "protocol": "-1",
                    "cidr_block": "0.0.0.0/0",
                }
            ],
            "expectedresult": False,
        },
        {
            "evaluator_data": [{"name": "fail"}],
            "input_data": [
                {
                    "rule_no": {"key": {"value": {"hello": 11}}},
                    "action": "allow",
                    "from_port": "0",
                    "to_port": 0,
                    "protocol": "-1",
                    "cidr_block": "0.0.0.0/0",
                },
                {"name": "fail"},
            ],
            "expectedresult": False,
        },
        {
            "evaluator_data": [{"name": "fail"}],
            "input_data": [
                {
                    "rule_no": {"key": {"value": {"hello": 11}}},
                    "action": "allow",
                    "from_port": "0",
                    "to_port": 0,
                    "protocol": "-1",
                    "cidr_block": "0.0.0.0/0",
                },
                {"name": "fail"},
            ],
            "expectedresult": False,
        },
    ]
    for i in range(len(para_input)):
        input_data = para_input[i]["input_data"]
        evaluator_data = para_input[i]["evaluator_data"]
        expectedresult = para_input[i]["expectedresult"]
        each_tuple = (input_data, evaluator_data, expectedresult)
        para.append(each_tuple)

    return para


List_of_tuples = test_evaluationresult_handler()


@pytest.mark.parametrize(
    ("input_data", "evaluator_data", "expectedresult"), List_of_tuples
)
def test_eval(input_data, evaluator_data, expectedresult):
    from sg_policy.providers.python.terraform_plan import handler

    result, iter_count = handler.str_in_list(input_data, evaluator_data)
    print(result)
    assert result["pass"] == expectedresult
