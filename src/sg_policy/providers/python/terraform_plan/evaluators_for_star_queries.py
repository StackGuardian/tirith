def star_int_equals_int(input_data, evaluator_data):
	#print(type(input_data))
	#print(evaluator_data)
	iter_count = 0
	if (
		type(input_data) == list
		and type(evaluator_data) == int
	):  
		msg=""
		allowed_list_of_index=[]
		for i in range(len(input_data)):
			if type(input_data[i])==int:
					if input_data[i]==evaluator_data:
					   iter_count=iter_count+1
					   allowed_list_of_index.append(i)
			if type(input_data[i])!=int:
				msg="input data should be integer"
				return {"pass":"undef","message":msg},iter_count
		if allowed_list_of_index!=[] and msg!="":
			msg=f"input_data at the index '{allowed_list_of_index}'' are present"
			return {"pass":True,"message":msg},iter_count
		else:
			msg= f"input data'{input_data}' is not present in allowed list '{evaluator_data}'"
			return {"pass":False,"message":msg},iter_count
  



		