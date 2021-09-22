#!/usr/bin/env python

import json

with open('out.json') as out:
    evalResults = json.load(out)

all_evaluations = {}

def evaluate_type(value, eval_type, evaluation_condition):
    global passes, failiers
    fail_set = False

    for res in value[eval_type]:
        eval_pass = res['evaluation_result']['pass']
        message = res['evaluation_result']['message']
        evaluation = True if eval_pass else False

        #all_evaluations[eval_type]['evaluations'][evaluation] = \
        #        message if evaluation in all_evaluations[eval_type]['evaluations'] else [message]
        if evaluation not in all_evaluations[eval_type]['evaluations']:
            all_evaluations[eval_type]['evaluations'][evaluation] = []

        all_evaluations[eval_type]['evaluations'][evaluation].append(message)

        outputs[eval_type].append(res)

        if eval_pass != True:
            not_true[eval_type].append(res)
            if eval_pass == False: errors[eval_type].append(res)

        #if res['evaluation_result']['pass'] == evaluation_condition:
        #    all_evaluations[eval_type]['all_pass'] = False
        print(eval_type, res['evaluation_result']['pass'] is not evaluation_condition)
        if res['evaluation_result']['pass'] is not evaluation_condition and not fail_set:
            #all_evaluations[eval_type]['all_pass'] = not evaluation_condition
            all_evaluations[eval_type]['all_pass'] = not all_evaluations[eval_type]['all_pass']
            fail_set = True

errors = {}
outputs = {}
not_true = {}

if not evalResults.get('errors'):
    if evalResults.get('result'):
        for res in evalResults['result']:
            for exp in res['expressions']:
                    allOfBlockPassed = True
                    anyOfBlockPassed = True
                    noneOfBlockPassed = True

                    value = exp['value']

                    for eval_type in value:
                        errors[eval_type] = []
                        outputs[eval_type] = []
                        not_true[eval_type] = []
                        all_evaluations[eval_type] = {
                                'evaluations': {},
                                'all_pass': False if eval_type == "any_of" else True
                            }

                        results = exp['value'][eval_type]

                        #evaluation_condition = True if evalResults == "any_of" else False
                        evaluation_condition = True if evalResults == "all_of" else False
                        evaluate_type(value, eval_type, evaluation_condition)

                    log = {
                            "errors": errors,
                            "outputs": outputs,
                            "all_not_true_evaluations": not_true
                            }

                    print(json.dumps(log, indent=1))
                    print('\nUser readable part:\n\n')

                    all_pass = [ all_evaluations[p]['all_pass'] for p in all_evaluations ]
                    print(f'All evaluations have {"not" if False in all_pass else ""} passed.')

                    for eval_type, report in all_evaluations.items():
                        status = "been successfull" if report['all_pass'] else "failed"
                        print(f'\nEvaluation of {" ".join(eval_type.split("_")).upper()} conditions has {status}:')
                        print('======================================================')

                        successes = report['evaluations'].get(True)
                        fails = report['evaluations'].get(False)

                        if successes:
                            if isinstance(successes, list):
                                for success in successes:
                                    if success: print(f'PASS: {success}')
                            else:
                                print(f'PASS: {successes}')

                        if fails:
                            for fail in fails:
                                print(f'FAIL: {fail}')
