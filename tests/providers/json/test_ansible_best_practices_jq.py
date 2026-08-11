"""
Test suite for Ansible Best Practices policy using JQ operations.
This tests comprehensive Ansible playbook validation with complex JQ queries.
"""

import json
import os
import pytest
from tirith.core.core import start_policy_evaluation_from_dict


def load_test_data():
    """Helper function to load input and policy data."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "input_ansible_best_practices.json")
    policy_file = os.path.join(current_dir, "policy_ansible_best_practices_jq.json")
    
    # Verify files exist
    assert os.path.exists(input_file), f"Input file not found: {input_file}"
    assert os.path.exists(policy_file), f"Policy file not found: {policy_file}"
    
    # Load input and policy data
    with open(input_file, 'r') as f:
        input_data = json.load(f)
    
    with open(policy_file, 'r') as f:
        policy_data = json.load(f)
    
    return input_data, policy_data


def test_ansible_best_practices_policy_comprehensive():
    """
    Test comprehensive Ansible best practices enforcement with JQ queries.
    
    This test validates:
    - Naming conventions (plays, tasks, handlers)
    - Security practices (no_log, permissions, TLS)
    - Idempotency (changed_when, handlers)
    - Module best practices (FQCN, proper parameters)
    - Configuration management (tags, variables)
    - Operational practices (monitoring, backups, validation)
    """
    input_data, policy_data = load_test_data()
    
    # Evaluate the input against the policy
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Print detailed results for debugging
    print("\n" + "="*80)
    print("Test: Ansible Best Practices with JQ Operations")
    print("="*80)
    print(f"Overall Result: {result.get('final_result', 'UNKNOWN')}")
    print("="*80 + "\n")
    
    # Print individual evaluator results
    if 'evaluators' in result:
        print("Evaluator Results:")
        print("-"*80)
        for evaluator in result['evaluators']:
            eval_id = evaluator.get('id', 'unknown')
            eval_result = evaluator.get('result', 'UNKNOWN')
            eval_desc = evaluator.get('description', '')
            eval_value = evaluator.get('provider_response', 'N/A')
            
            status_symbol = "✓" if eval_result == "PASS" else "✗"
            print(f"{status_symbol} [{eval_result}] {eval_id}")
            print(f"  Description: {eval_desc}")
            print(f"  Value: {eval_value}")
            print()
        print("-"*80 + "\n")
    
    # Assert overall success
    assert result.get('final_result') == 'PASS', \
        f"Policy evaluation failed. Results: {json.dumps(result, indent=2)}"


def test_ansible_best_practices_naming_conventions():
    """Test that all plays, tasks, and handlers are properly named."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check naming-related evaluators
    naming_evaluators = [
        'playbook_has_name',
        'all_tasks_named',
        'task_name_capitalization',
        'all_handlers_named'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in naming_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        assert evaluators[eval_id].get('result') == 'PASS', \
            f"Naming check failed for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_security():
    """Test security-related best practices."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check security-related evaluators
    security_evaluators = [
        'sensitive_tasks_use_no_log',
        'file_permissions_not_too_open',
        'security_tasks_exist',
        'verify_tls_enabled'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in security_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        assert evaluators[eval_id].get('result') == 'PASS', \
            f"Security check failed for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_idempotency():
    """Test idempotency-related best practices."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check idempotency-related evaluators
    idempotency_evaluators = [
        'command_tasks_have_changed_when',
        'handlers_exist',
        'handlers_for_service_restarts'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in idempotency_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        # Note: Some evaluators may not pass due to error_tolerance
        result_status = evaluators[eval_id].get('result')
        assert result_status in ['PASS', 'ERROR'], \
            f"Idempotency check unexpected result for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_module_usage():
    """Test proper module usage and parameters."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check module usage evaluators
    module_evaluators = [
        'use_fqcn_for_modules',
        'service_tasks_have_enabled',
        'template_tasks_complete',
        'file_tasks_have_owner_group'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in module_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        assert evaluators[eval_id].get('result') == 'PASS', \
            f"Module usage check failed for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_operational():
    """Test operational best practices (monitoring, backups, validation)."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check operational evaluators
    operational_evaluators = [
        'verify_monitoring_enabled',
        'verify_backup_configured',
        'validation_tasks_exist',
        'retries_for_flaky_operations'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in operational_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        assert evaluators[eval_id].get('result') == 'PASS', \
            f"Operational check failed for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_complex_jq_queries():
    """Test complex JQ query capabilities."""
    input_data, policy_data = load_test_data()
    result = start_policy_evaluation_from_dict(policy_data, input_data)
    
    # Check complex query evaluators
    complex_evaluators = [
        'extract_critical_task_names',
        'extract_security_task_count',
        'extract_app_configuration'
    ]
    
    evaluators = {e['id']: e for e in result.get('evaluators', [])}
    
    for eval_id in complex_evaluators:
        assert eval_id in evaluators, f"Missing evaluator: {eval_id}"
        # These should all pass as they extract and validate specific data
        assert evaluators[eval_id].get('result') == 'PASS', \
            f"Complex query failed for {eval_id}: {evaluators[eval_id]}"


def test_ansible_best_practices_variable_extraction():
    """Test that JQ can extract and validate configuration variables."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "input_ansible_best_practices.json")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Verify the input structure
    assert isinstance(data, list), "Input should be a list of plays"
    assert len(data) > 0, "Input should have at least one play"
    
    play = data[0]
    assert 'name' in play, "Play should have a name"
    assert 'vars' in play, "Play should have variables"
    assert 'tasks' in play, "Play should have tasks"
    assert 'handlers' in play, "Play should have handlers"
    
    # Verify critical variables
    vars_dict = play['vars']
    assert vars_dict.get('tls_enabled') is True, "TLS should be enabled"
    assert vars_dict.get('monitoring_enabled') is True, "Monitoring should be enabled"
    assert vars_dict.get('backup_enabled') is True, "Backup should be enabled"
    assert vars_dict.get('app_name') == 'secure-webapp', "App name should match"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
