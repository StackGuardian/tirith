#!/usr/bin/env python3

#from cli.cli import evaluate
from cli.cli import *

current_dir = os.getcwd()
data_json = os.path.join(current_dir, '../../../data.json')
input_json = os.path.join(current_dir, './input.json')
#input_json = os.path.join(current_dir, '../../../../input.json')
evaluate(data_json, input_json)
