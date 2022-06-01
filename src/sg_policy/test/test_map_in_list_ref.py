import json

import pytest
import os
from time import time
import atexit
from time import time, strftime, localtime
from datetime import timedelta
import pandas as pd
from decimal import Decimal


@pytest.fixture()
def apigw_event():
    """Generates API GW Event"""

    return {
        "evaluator_data":
               {
                  "name":"fail"
               }
            ,
            "input_data":[
               {
                  "rule_no":{
                     "key":{
                        "value":{
                           "hello":11
                        }
                     }
                  },
                  "action":"allow",
                  "from_port":"0",
                  "to_port":0,
                  "protocol":"-1",
                  "cidr_block":"0.0.0.0/0"
               }
            ]
            }

def test_evaluationresult_handler(apigw_event):
    
    from sg_policy.providers.python.terraform_plan import handler  
    input_data=apigw_event["input_data"]
    evaluator_data=apigw_event["evaluator_data"] 
    result,iter_count = handler.map_in_list(input_data,evaluator_data)
    

    assert   result["pass"] in ["true"]