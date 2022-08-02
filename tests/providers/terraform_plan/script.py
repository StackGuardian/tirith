from icecream import ic
import json

import pytest
import csv
import os
from time import time
import atexit
from time import time, strftime, localtime
from datetime import timedelta
import pandas as pd
from decimal import Decimal
from sg_policy.providers.terraform_plan import handler
import json


start = time()
data_file = r"C:\Users\ARCHANA SINGH\Desktop\framework\policy-framework\tests\providers\opa\terraform_plan\data\data_2.json"
input_file = r"C:\Users\ARCHANA SINGH\Desktop\framework\policy-framework\tests\providers\opa\terraform_plan\input\input_2.json"
json_data = handler.evaluate(data_file, input_file)
print(json_data)
end = time()
elapsed_time = end - start
with open(
    f"{data_file}",
    "r",
) as fp:
    for count, line in enumerate(fp):
        pass
        policy_lines = count + 1
with open(
    f"{input_file}",
    "r",
) as fp:
    for count, line in enumerate(fp):
        pass
        tf_lines = count + 1
data = json.dumps(json_data)
json_to_python = json.loads(data)
results = json_to_python

# print(results["result"])
all_of_datas = []
for result in results["result"]:
    if "all_of" in result:
        for all_of_data in results["result"]["all_of"]:
            all_of_datas.append([all_of_data["attribute"], all_of_data["iter_count"]])

none_of_datas = []
for result in results["result"]:
    if "none_of" in result:
        for none_of_data in results["result"]["none_of"]:
            none_of_datas.append(
                [none_of_data["attribute"], none_of_data["iter_count"]]
            )

any_of_datas = []
for result in results["result"]:
    if "any_of" in result:
        for any_of_data in results["result"]["any_of"]:
            any_of_datas.append([any_of_data["attribute"], any_of_data["iter_count"]])


with open("mycsv.csv", "a", newline="") as f:
    thewriter = csv.writer(f)
    thewriter.writerow(
        [
            "no.of lines in tf.json",
            "no.of lines in policy",
            "time taken to execute all policy",
            "all_of_data",
            "none_of_data",
            "any_of_data",
        ]
    )
    thewriter.writerow(
        [
            tf_lines,
            policy_lines,
            elapsed_time,
            all_of_datas,
            none_of_datas,
            any_of_datas,
        ]
    )

    # print(msg)
