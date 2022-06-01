import re
from time import time
import os
import json

#TODO: use CAMELCASE for all function name
def finditem(obj, key):

	if key in obj:
		return obj[key]
	for v in obj.values():
		if isinstance(v, dict):
			item = finditem(v, key)
			if item is not None:
				return item
	return None


def find_input_resource_changes_value(chunks, input_resource_change_attrs):

	Iter_Count = 0
	if (
		len(chunks) > 1
		and len(input_resource_change_attrs[chunks[0]]) > 1
		and (type(input_resource_change_attrs[chunks[0]]) == dict)
	):

		res = finditem(input_resource_change_attrs[chunks[0]], chunks[-1])

	elif (
		len(chunks) > 1
		and len(input_resource_change_attrs[chunks[0]]) == 1
		and type(input_resource_change_attrs[chunks[0]]) == list
	):

		res = finditem(input_resource_change_attrs[chunks[0]][0], chunks[-1])

	elif (
		len(chunks) > 1
		and len(input_resource_change_attrs[chunks[0]]) > 1
		and type(input_resource_change_attrs[chunks[0]]) == list
	):

		res = []

		for i in range(len(input_resource_change_attrs[chunks[0]])):
			each_re = finditem(input_resource_change_attrs[chunks[0]][i], chunks[-1])
			res.append(each_res)

	else:
		res = input_resource_change_attrs[chunks[0]]

	return res


# def find_item(chunks,input_resource_change_attrs):
# 	print(chunks[-1])
# 	print(input_resource_change_attrs[chunks[0]][0])
# 	s=finditem(input_resource_change_attrs[chunks[0]][0],chunks[-1])
# 	print(s)


def initialize(policy, input_data):

	policies = policy["terraform_plan"]["policies"]
	policy_resource = []
	policy_attribute_name = []
	policy_attribute = []
	input_resource_changes_attr_value = []
	input_datatype = []
	policy_attribute_name = []
	input_resource_change_attrs = {}
	new_policy_attribute = []
	new_policy_attribute_name = []
	count = 0
	iter_count = 0
	Iter_count = []
	if len(policies) > 0:
		for policy in policies:
			policy_resource.append(policy["resource_type"])
			attributes = policy["attributes"]
		resource_changes = input_data["resource_changes"]
		for resource_change in resource_changes:
			if resource_change["type"] in policy_resource:
				input_resource_change_attrs = resource_change["change"]["after"]
		# print(input_resource_change_attrs)
		for attribute in attributes:
			count = 1
			chunks = attribute["name"].split(".")
			s = chunks[0]
			if chunks[0] in input_resource_change_attrs:
				count += 1
				policy_attribute.append(attribute)
				policy_attribute_name.append(s)
				if "*" in chunks:
					res = find_input_resource_changes_value(
						chunks, input_resource_change_attrs
					)

				else:
					res = find_input_resource_changes_value(
						chunks, input_resource_change_attrs
					)

				try:
					input_changes = int(res)

				except:
					input_changes = res
				input_resource_changes_attr_value.append(input_changes)
				each_iter_count = count + iter_count
				Iter_count.append(each_iter_count)
				if type(input_changes) == str:
					input_datatype.append("string")
				elif type(input_changes) == bool:
					input_datatype.append("boolean")
				elif type(input_changes) == list:
					input_datatype.append("array")
				elif type(input_changes) == dict:
					input_datatype.append("map")
				elif type(input_changes) == int:
					input_datatype.append("integer")
				else:
					input_datatype.append(type(input_changes))
	# print(iter_count)

	msg = {
		"policy_resource": policy_resource,
		"policy_attribute": policy_attribute,
		"policy_attribute_name": policy_attribute_name,
		"input_resource_changes_attr_value": input_resource_changes_attr_value,
		"input_datatype": input_datatype,
		"iter_count": Iter_count,
	}
	# print(input_resource_changes_attr_value)
	return msg


def all_of(msg):
	total_evaluation = []
	if msg["policy_attribute"] != []:
		evaluator_ref_all_of = []
		evaluator_data_all_of = []
		evaluator_datatype_all_of = []
		count = 0
		for key, value in msg.items():
			count = 1
			if key == "policy_attribute":
				# print(value)
				for attribute in value:
					count += 1
					# print(attribute)
					evaluator_all_of = attribute["evaluators"]["all_of"][0]
					# print(evaluator_all_of)
					evaluator_ref_all_of.append(evaluator_all_of["evaluator_ref"])
					try:
						res = int(evaluator_all_of["evaluator_data"])
					except:
						res = evaluator_all_of["evaluator_data"]
					evaluator_data_all_of.append(res)
					if type(res) == str:
						evaluator_datatype_all_of.append("string")
					elif type(res) == bool:
						evaluator_datatype_all_of.append("boolean")
					elif type(res) == list:
						evaluator_datatype_all_of.append("array")
					elif type(res) == dict:
						evaluator_datatype_all_of.append("map")
					elif type(res) == int:
						evaluator_datatype_all_of.append("integer")
					else:
						evaluator_datatype_all_of.append(
							type(evaluator_all_of["evaluator_data"])
						)
		# print(msg["input_resource_changes_attr_value"][0])
		each_evaluation = {}
		evaluator_result_all_of = ""
		iter_count = 0
		# print(msg["input_resource_changes_attr_value"])
		for i in range(len(evaluator_ref_all_of)):
			if (
				type(msg["input_resource_changes_attr_value"][i]) == list
				and type(msg["input_resource_changes_attr_value"][i][0]) != dict
			):
				for j in range(len(msg["input_resource_changes_attr_value"][i])):
					evaluator_result_all_of = evaluator_handler(
						msg["input_resource_changes_attr_value"][i][j],
						evaluator_data_all_of[i],
						evaluator_ref_all_of[i],
					)[0]
					iter_count = evaluator_handler(
						msg["input_resource_changes_attr_value"][i][j],
						evaluator_data_all_of[i],
						evaluator_ref_all_of[i],
					)[1]
			each_evaluation = {}
			each_evaluation = {
				"attribute": msg["policy_attribute_name"][i],
				"evaluator_ref": evaluator_ref_all_of[i],
				"evaluator_data": evaluator_data_all_of[i],
				"input_data": msg["input_resource_changes_attr_value"][i],
				"input_datatype": msg["input_datatype"][i],
				"evaluator_datatype": evaluator_datatype_all_of[i],
				"evaluator_result_all_of": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_all_of[i],
					evaluator_ref_all_of[i],
				)[0],
				"iter_count": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_all_of[i],
					evaluator_ref_all_of[i],
				)[1]
				+ count
				+ msg["iter_count"][i],
			}
			total_evaluation.append(each_evaluation)
	return total_evaluation


def any_of(msg):
	# iterate over any_of map
	total_evaluation = []
	if msg["policy_attribute"] != []:
		evaluator_ref_any_of = []
		evaluator_data_any_of = []
		evaluator_datatype_any_of = []
		count = 0
		for key, value in msg.items():
			if key == "policy_attribute":
				# print(value)
				for attribute in value:
					# print(attribute)
					count += 1
					try:
						evaluator_any_of = attribute["evaluators"]["any_of"][0]
					except:
						break
					# print(evaluator_all_of)
					evaluator_ref_any_of.append(evaluator_any_of["evaluator_ref"])
					try:
						res = int(evaluator_any_of["evaluator_data"])
					except:
						res = evaluator_any_of["evaluator_data"]
					evaluator_data_any_of.append(res)

					if type(evaluator_any_of["evaluator_data"]) == str:
						evaluator_datatype_any_of.append("string")
					elif type(evaluator_any_of["evaluator_data"]) == bool:
						evaluator_datatype_any_of.append("boolean")
					elif type(evaluator_any_of["evaluator_data"]) == list:
						evaluator_datatype_any_of.append("array")
					elif type(res) == dict:
						evaluator_datatype_any_of.append("map")
					elif type(res) == int:
						evaluator_datatype_any_of.append("integer")
					else:
						evaluator_datatype_any_of.append(
							type(evaluator_any_of["evaluator_data"])
						)
		each_evaluation = {}
		for i in range(len(evaluator_ref_any_of)):
			each_evaluation = {}
			each_evaluation = {
				"attribute": msg["policy_attribute_name"][i],
				"evaluator_ref": evaluator_ref_any_of[i],
				"evaluator_data": evaluator_data_any_of[i],
				"input_data": msg["input_resource_changes_attr_value"][i],
				"input_datatype": msg["input_datatype"][i],
				"evaluator_datatype": evaluator_datatype_any_of[i],
				"evaluator_result_any_of": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_any_of[i],
					evaluator_ref_any_of[i],
				)[0],
				"iter_count": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_any_of[i],
					evaluator_ref_any_of[i],
				)[1]
				+ count
				+ msg["iter_count"][i],
			}
			total_evaluation.append(each_evaluation)
	return total_evaluation


def none_of(msg):
	total_evaluation = []
	if msg["policy_attribute"] != []:
		evaluator_ref_none_of = []
		evaluator_data_none_of = []
		evaluator_datatype_none_of = []
		count = 0
		for key, value in msg.items():
			count = 1
			if key == "policy_attribute":
				# print(value)
				for attribute in value:
					count += 1
					# print(attribute)
					try:
						evaluator_none_of = attribute["evaluators"]["none_of"][0]
					except:
						break
					# print(evaluator_all_of)
					evaluator_ref_none_of.append(evaluator_none_of["evaluator_ref"])
					try:
						res = int(evaluator_none_of["evaluator_data"])
					except:
						res = evaluator_none_of["evaluator_data"]
					evaluator_data_none_of.append(res)
					if type(evaluator_none_of["evaluator_data"]) == str:
						evaluator_datatype_none_of.append("string")
					elif type(evaluator_none_of["evaluator_data"]) == bool:
						evaluator_datatype_none_of.append("boolean")
					elif type(evaluator_none_of["evaluator_data"]) == list:
						evaluator_datatype_none_of.append("array")
					elif type(res) == dict:
						evaluator_datatype_none_of.append("map")
					elif type(res) == int:
						evaluator_datatype_none_of.append("integer")
					else:
						evaluator_datatype_none_of.append(
							type(evaluator_none_of["evaluator_data"])
						)
		# print(msg["input_resource_changes_attr_value"][0])
		each_evaluation = {}
		for i in range(len(evaluator_ref_none_of)):
			each_evaluation = {}
			each_evaluation = {
				"attribute": msg["policy_attribute_name"][i],
				"evaluator_ref": evaluator_ref_none_of[i],
				"evaluator_data": evaluator_data_none_of[i],
				"input_data": msg["input_resource_changes_attr_value"][i],
				"input_datatype": msg["input_datatype"][i],
				"evaluator_datatype": evaluator_datatype_none_of[i],
				"evaluator_result_any_of": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_none_of[i],
					evaluator_ref_none_of[i],
				)[0],
				"iter_count": evaluator_handler(
					msg["input_resource_changes_attr_value"][i],
					evaluator_data_none_of[i],
					evaluator_ref_none_of[i],
				)[1]
				+ count
				+ msg["iter_count"][i],
			}
			total_evaluation.append(each_evaluation)
	return total_evaluation


def evaluator_handler(input_data, evaluator_data, evaluator_ref):
	# print(evaluator_ref)
	if evaluator_ref == "str_equals_str":
		evaluation_result, iter_count = str_equals_str(input_data, evaluator_data)
	elif evaluator_ref == "str_contains_str":
		evaluation_result, iter_count = str_contains_str(
			input_data[i], evaluator_data[i]
		)
	elif evaluator_ref == "str_in_list":
		evaluation_result, iter_count = str_in_list(input_data, evaluator_data)
	elif evaluator_ref == "equals_null":
		evaluation_result, iter_count = equals_null(input_data[i])
	elif evaluator_ref == "str_matches_regex":
		evaluation_result, iter_count = str_matches_regex(input_data, evaluator_data)
	elif evaluator_ref == "bool_equals_bool":
		evaluation_result, iter_count = bool_equals_bool(True, True)
	elif evaluator_ref == "cidr_contains_cidr_or_ip":
		evaluation_result, iter_count = cidr_contains_cidr_or_ip(
			input_data, evaluator_data
		)
	elif evaluator_ref == "int_equals_int":
		evaluation_result, iter_count = int_equals_int(input_data, evaluator_data)
	elif evaluator_ref == "map_in_list":
		evaluation_result, iter_count = map_in_list(input_data, evaluator_data)
	elif evaluator_ref == "map_in_list_full_match":
		evaluation_result, iter_count = map_in_list_full_match(
			input_data, evaluator_data
		)
	# print(result)
	return evaluation_result, iter_count


def cidr_contains_cidr_or_ip(input_data, evaluator_data):
	# TODO: improvement
	iter_count = 0
	if type(input_data) == str and type(evaluator_data) == str:
		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif type(input_data) != str:
		msg = "For 'cidr_contains_cidr_or_ip' evaluator_ref, both input_data and evaluator_data should be cidr or ip as 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	elif type(evaluator_data) == str:
		msg = "For 'cidr_contains_cidr_or_ip' evaluator_ref, both input_data and evaluator_data should be cidr or ip as 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def bool_equals_bool(input_data, evaluator_data):
	iter_count = 0
	if (
		type(input_data) == bool
		and type(evaluator_data) == bool
		and input_data == evaluator_data
	):

		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif type(input_data) != bool:
		msg = "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'."
		return {"pass": "undef", "message": msg}, iter_count
	elif type(evaluator_data) != bool:
		msg = "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input should be '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def is_valid(evaluation_data):
	try:
		re.compile(evaluator_data)
		regex_valid = True
	except:
		regex_valid = False


def str_matches_regex(input_data, evaluator_data):
	iter_count = 0
	if (
		type(input_data) == str
		and is_valid(evaluator_data)
		and re.fullmatch(evaluator_data, input_data)
	):
		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif is_valid(evaluator_data):
		msg = f"Provided regex '{evaluator_data}' is not valid"
		return {"pass": "undef", "message": msg}, iter_count
	elif type(input_data) != str:
		msg = "For 'str_matches_regex' evaluator_ref, input_data should be a 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def str_contains_str(input_data, evaluator_data):
	iter_count = 0
	if type(input_data) == str and type(evaluator_data) == str:
		# contains(evaluator_data, input_data)
		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif type(input_data) != str:
		msg = "For 'str_contains_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	elif type(evaluator_data) != str:
		msg = "For 'str_contains_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


# functions str_equals + type_check put together
def str_equals_str(input_data, evaluator_data):
	iter_count = 0
	if (
		type(input_data) == str
		and type(evaluator_data) == str
		and input_data == evaluator_data
	):
		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif type(input_data) != str:
		msg = "For 'str_equals_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	elif type(evaluator_data) != str:
		msg = "For 'str_equals_str' evaluator_ref, both input_data and evaluator_data should be 'string'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def str_in_list(input_data, evaluator_data):
	iter_count = 0
	if type(input_data) == str and type(evaluator_data) == list:
		for i in range(len(evaluator_data)):
			iter_count = 1
			if input_data == evaluator_data[i]:
				msg = ""
				return {"pass": True, "message": msg}, iter_count
	if type(input_data) != str:
		msg = "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'."
		return {"pass": "undef", "message": msg}, iter_count
	if type(evaluator_data) != list:
		msg = "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		# print("yes")
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count
		# print(msg)


def equals_null(input_data):
	iter_count = 0
	if type(input_data) == None:
		msg = ""
		return {"pass": True, "message": msg}, iter_count

	else:
		msg = f"input data is of type '{type(input_data)}' which is not 'None'"
		return {"pass": False, "message": msg}, iter_count


def int_equals_int(input_data, evaluator_data):
	iter_count = 0
	if (
		type(input_data) == int
		and type(evaluator_data) == int
		and input_data == evaluator_data
	):
		msg = ""
		return {"pass": True, "message": msg}, iter_count
	elif type(input_data) != int:
		msg = "For 'int_equals_int' evaluator_ref, both input_data and evaluator_data should be 'integer'."
		return {"pass": "undef", "message": msg}, iter_count
	elif type(evaluator_data) != int:
		msg = "For 'int_equals_int' evaluator_ref, both input_data and evaluator_data should be 'integer'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


# def list_contains_map(input_data,evaluator_data):
def map_in_list(
	input_data, evaluator_data
):  # atleast one map i input_data should be present in  evulator_data
	iter_count = 0
	if type(input_data) == list and type(evaluator_data) == list:
		msg = ""
		if msg == "":
			for i in range(len(evaluator_data)):
				iter_count += 1
				if type(evaluator_data[i]) != dict:
					msg = "For 'map_in_list' evaluator_ref, evaluator_data should also be  'lists of map/maps'."
					return {"pass": "undef", "message": msg}, iter_count
					break

		if msg == "":
			for i in range(len(input_data)):
				iter_count += 1
				if type(input_data[i]) != dict:
					msg = "For 'map_in_list' evaluator_ref, input_data should be a 'list of map/maps'."
					return {"pass": "undef", "message": msg}, iter_count
					break
		if msg == "":
			for data in input_data:
				iter_count += 1
				if data in evaluator_data:
					return {"pass": True, "message": msg}, iter_count
					break

	if type(input_data) != dict:
		msg = "For 'map_in_list' evaluator_ref, input_data should be a 'map' and evaluator_data should be a 'map'."
		return {"pass": "undef", "message": msg}, iter_count
	if type(evaluator_data) != dict:
		msg = "For 'map_in_list' evaluator_ref, input_data should be a 'map' and evaluator_data should be a 'map'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		# print("yes")
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def map_in_list_full_match(
	input_data, evaluator_data
):  # the evaluator_data should contain only the dict items present in input_data
	iter_count = 0
	if type(input_data) == list and type(evaluator_data) == list:
		msg = ""
		if msg == "":
			for i in range(len(evaluator_data)):
				if type(evaluator_data[i]) != dict:
					iter_count += 1
					msg = "For 'map_in_list_full_match' evaluator_ref, evaluator_data should also be  'lists of map/maps'."
					return {"pass": "undef", "message": msg}, iter_count
					break

		if msg == "":
			for i in range(len(input_data)):
				if type(input_data[i]) != dict:
					iter_count + 1
					msg = "For 'map_in_list_full_match' evaluator_ref, input_data should be a 'list of map/maps'."
					return {"pass": "undef", "message": msg}, iter_count
					break
		if msg == "":

			flag = 0
			if all(x in input_data for x in evaluator_data):
				flag = 1
				inter_count = len(evaluator_data)
			if flag:
				return {"pass": True, "message": msg}, iter_count
			else:
				msg = "For 'map_in_list_full_match' evaluator_ref,  evaluator_data should be contains items provided by input_data only."
				return {"pass": "undef", "message": msg}, iter_count

	if type(input_data) != dict:
		msg = "For 'map_in_list_full_match' evaluator_ref, input_data should be a 'map' and evaluator_data should be a 'map'."
		return {"pass": "undef", "message": msg}, iter_count
	if type(evaluator_data) != dict:
		msg = "For 'map_in_list_full_match' evaluator_ref, input_data should be a 'map' and evaluator_data should be a 'map'."
		return {"pass": "undef", "message": msg}, iter_count
	else:
		# print("yes")
		msg = f"input string '{input_data}' is not present in allowed list '{evaluator_data}'"
		return {"pass": False, "message": msg}, iter_count


def evaluate(data_file, input_file):
	# print(data)
	if os.path.isfile(data_file) and os.path.isfile(input_file):

		# Opening JSON file
		# TODO:check the schema of the input files
		# TODO:Check the files are json
		# TODO:
		with open(f"{data_file}") as f:

			json_to_python = json.load(f)
			policy = json_to_python
		with open(f"{input_file}") as f:

			json_to_python = json.load(f)
			input_data = json_to_python
		msg = initialize(policy, input_data)
		final_output = {
			"result": {
				"all_of": all_of(msg),
				"any_of": any_of(msg),
				"none_of": none_of(msg),
			}
		}
		print(final_output)
		return final_output


def test_evaluate_handler(event):
	policy = event["data"]
	input_data = event["input_data"]
	msg = initialize(policy, input_data)
	final_output = {
		"result": {
			"all_of": all_of(msg),
			"any_of": any_of(msg),
			"none_of": none_of(msg),
		}
	}
	return final_output

	# final_output = {
	#     "errors": {},
	#     "result": {
	#     "all_of": [
	#       {
	#         "attribute": "ami",
	#         "evaluation_result": {
	#           "message": "input string 'ami-09b4b74c' is not present in allowed list '[\"provide list of string items to match\"]'",
	#           "pass": False
	#         },
	#         "evaluator_data": [
	#           "provide list of string items to match"
	#         ],
	#         "evaluator_datatype": "array",
	#         "evaluator_ref": "str_in_list",
	#         "input_data": "ami-09b4b74c",
	#         "input_datatype": "string",
	#         "resource_type": "aws_instance"
	#       },
	#       {
	#         "attribute": "instance_type",
	#         "evaluation_result": {
	#           "message": "input string 't2.micro' is not present in allowed list '[\"provide list of string items to match\"]'",
	#           "pass": False
	#         },
	#         "evaluator_data": [
	#           "provide list of string items to match"
	#         ],
	#         "evaluator_datatype": "array",
	#         "evaluator_ref": "str_in_list",
	#         "input_data": "t2.micro",
	#         "input_datatype": "string",
	#         "resource_type": "aws_instance"
	#       },
	#       {
	#         "attribute": "ebs_optimized",
	#         "evaluation_result": {
	#           "message": "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'.",
	#           "pass": "undef"
	#         },
	#         "evaluator_data": [
	#           "provide a boolean value of true or False"
	#         ],
	#         "evaluator_datatype": "array",
	#         "evaluator_ref": "bool_equals_bool",
	#         "input_data": None,
	#         "input_datatype": "None",
	#         "resource_type": "aws_instance"
	#       },
	#       {
	#         "attribute": "disable_api_termination",
	#         "evaluation_result": {
	#           "message": "For 'bool_equals_bool' evaluator_ref, both input_data and evaluator_data should be 'boolean'.",
	#           "pass": "undef"
	#         },
	#         "evaluator_data": [
	#           "provide a boolean value of true or False"
	#         ],
	#         "evaluator_datatype": "array",
	#         "evaluator_ref": "bool_equals_bool",
	#         "input_data": None,
	#         "input_datatype": "None",
	#         "resource_type": "aws_instance"
	#       },
	#       {
	#         "attribute": "instance_initiated_shutdown_behavior",
	#         "evaluation_result": {
	#           "message": "For 'str_in_list' evaluator_ref, input_data should be a 'string' and evaluator_data should be a 'list'.",
	#           "pass": "undef"
	#         },
	#         "evaluator_data": [
	#           "provide list of string items to match"
	#         ],
	#         "evaluator_datatype": "array",
	#         "evaluator_ref": "str_in_list",
	#         "input_data": None,
	#         "input_datatype": "None",
	#         "resource_type": "aws_instance"
	#       }
	#     ],
	#     "any_of": [],
	#     "none_of": []
	#   }
	# }

	# print(msg)
	# any_of_value=False
	# all_of_value=False
	# none_of_value=False
	# for key,value in msg.items():
	# 	if key=="policy_attribute":
	# 		#print(value)
	# 		for attribute in value:
	# 			#print(attribute)
	# 			if "all_of" in attribute["evaluators"]:
	# 				all_of_value=True
	# 			if "any_of" in attribute["evaluators"]:
	# 				any_of_value=True
	# 			if "none_of" in attribute["evaluators"]:
	# 				none_of_value=False
	# result={}
	# if all_of_value:
	# 	result.append("all_of":all_of(msg))
	# else:
	# 	result.append("all_of":[])
	# if any_of_value:
	# 	result.append("any_of":any_of(msg))
	# else:
	# 	result.append("all_of":[])
