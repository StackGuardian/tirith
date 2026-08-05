# Ansible Best Practices Policy with JQ Operations

This directory contains a comprehensive Ansible playbook validation policy that uses JQ operations to enforce security, maintainability, and operational best practices.

## Files

### 1. `input_ansible_best_practices.json`
A realistic Ansible playbook in JSON format that demonstrates:
- **Secure web application deployment**
- **Multi-tier infrastructure setup**
- **Security hardening** (firewall, permissions, user management)
- **Monitoring integration** (Prometheus, Telegraf)
- **Backup automation** (cron jobs, retention policies)
- **Service management** (systemd, nginx, postgresql)
- **Configuration management** (templates, variables, handlers)
- **Validation tasks** (health checks, API verification)

**Key Features:**
- 28+ tasks covering complete application lifecycle
- 3 handlers for service management
- 15+ configuration variables
- Proper use of FQCN (Fully Qualified Collection Names)
- Security best practices (no_log, locked passwords, minimal permissions)
- Idempotency patterns (changed_when, creates, handlers)
- Operational excellence (retries, timeouts, backups)

### 2. `policy_ansible_best_practices_jq.json`
A comprehensive Tirith policy with 42 evaluators using JQ queries to validate:

#### Naming Conventions (4 evaluators)
- All plays have descriptive names
- All tasks have descriptive names
- Task names follow capitalization standards
- All handlers have unique names

#### Security Best Practices (6 evaluators)
- Sensitive data uses `no_log`
- File permissions are not overly permissive
- TLS/SSL is enabled
- Security tasks are present
- Privilege escalation is properly configured
- become_user requires become

#### Idempotency & Change Management (5 evaluators)
- Command/shell tasks define `changed_when` or use `creates/removes`
- Service restarts use handlers
- Shell tasks with pipes use `pipefail`
- Avoid shell when command is sufficient
- ignore_errors used sparingly

#### Module Usage & Parameters (8 evaluators)
- FQCN (Fully Qualified Collection Names) for all modules
- Service tasks explicitly set `enabled`
- Template tasks have src, dest, and validation
- File tasks specify owner and group
- wait_for tasks have timeouts
- URI tasks validate status codes
- Git tasks specify versions
- Package tasks avoid 'latest' state

#### Configuration Management (5 evaluators)
- Critical tasks are properly tagged
- Variables are defined and used
- Playbook has minimum task count (10+)
- Handlers are defined
- gather_facts is explicit

#### Operational Excellence (8 evaluators)
- Monitoring is enabled and configured
- Backup functionality is present
- Validation tasks exist (health checks)
- Retry logic for network operations
- Configuration backups enabled
- Cron tasks specify user
- Registered variables use meaningful names
- Systemd daemon reloads when needed

#### Complex JQ Queries (6 evaluators)
- Extract critical task names
- Count security tasks
- Extract application configuration
- Validate monitoring settings
- Validate TLS settings
- Validate backup configuration

### 3. `test_ansible_best_practices_jq.py`
Comprehensive test suite with multiple test functions:

- `test_ansible_best_practices_policy_comprehensive()` - Full policy evaluation
- `test_ansible_best_practices_naming_conventions()` - Naming standards
- `test_ansible_best_practices_security()` - Security checks
- `test_ansible_best_practices_idempotency()` - Idempotency validation
- `test_ansible_best_practices_module_usage()` - Module parameter checks
- `test_ansible_best_practices_operational()` - Operational practices
- `test_ansible_best_practices_complex_jq_queries()` - Complex JQ capabilities
- `test_ansible_best_practices_variable_extraction()` - Variable validation

## JQ Query Examples

### Example 1: Check for unnamed tasks
```jq
[.[].tasks[] | select(.name == null or .name == "")] | length
```

### Example 2: Find tasks with sensitive data without no_log
```jq
[.[].tasks[] | 
  select((.name | tostring | test("password|secret|token|key|credential"; "i")) or 
         (. | tostring | test("password|secret|token|credential"; "i"))) | 
  select(.no_log != true)] | length
```

### Example 3: Extract critical task names
```jq
[.[].tasks[] | select(.tags != null and (.tags | contains(["critical"]))) | .name]
```

### Example 4: Validate FQCN usage
```jq
[.[].tasks[] | keys[] | 
  select(test("^ansible\\.builtin\\.|^community\\.|^ansible\\.") | not) | 
  select(test("^(name|tags|when|become|...)$") | not)] | length
```

### Example 5: Check file permissions
```jq
[.[].tasks[] | 
  select(has("ansible.builtin.file") or has("ansible.builtin.copy") or has("ansible.builtin.template")) | 
  select((.[\"ansible.builtin.file\"].mode? == "0777") or 
         (.[\"ansible.builtin.copy\"].mode? == "0777") or 
         (.[\"ansible.builtin.template\"].mode? == "0777"))] | length
```

## Running the Tests

### Run all tests:
```bash
pytest tests/providers/json/test_ansible_best_practices_jq.py -v
```

### Run specific test:
```bash
pytest tests/providers/json/test_ansible_best_practices_jq.py::test_ansible_best_practices_security -v
```

### Run with detailed output:
```bash
pytest tests/providers/json/test_ansible_best_practices_jq.py -v -s
```

## Policy Evaluation Expression

The policy uses a complex boolean expression to ensure comprehensive validation:

```python
(playbook_has_name && all_tasks_named && task_name_capitalization) && 
(become_usage_check && become_user_without_become) && 
(package_state_not_latest && file_permissions_not_too_open && sensitive_tasks_use_no_log) && 
(command_tasks_have_changed_when || shell_with_pipe_uses_pipefail) && 
(use_fqcn_for_modules && tasks_have_appropriate_tags) && 
(service_tasks_have_enabled && template_tasks_complete && file_tasks_have_owner_group) && 
(wait_for_tasks_have_timeout && uri_tasks_validate_status && git_tasks_specify_version) && 
(no_when_with_jinja_delimiters && ignore_errors_minimal) && 
(minimum_task_count && handlers_exist && vars_defined) && 
(security_tasks_exist && validation_tasks_exist) && 
(verify_monitoring_enabled && verify_tls_enabled && verify_backup_configured)
```

## Best Practices Enforced

### 1. Security
- ✅ Sensitive data protection with `no_log`
- ✅ Minimal file permissions (never 0777)
- ✅ TLS/SSL enabled for secure communications
- ✅ User accounts with locked passwords
- ✅ Firewall configuration
- ✅ Security-tagged tasks

### 2. Maintainability
- ✅ All plays, tasks, and handlers named
- ✅ Descriptive variable names
- ✅ Proper task organization with tags
- ✅ Comments and documentation
- ✅ Version control (git with explicit versions)

### 3. Idempotency
- ✅ Command/shell tasks with `changed_when`
- ✅ Use of `creates` and `removes`
- ✅ Handlers for service restarts
- ✅ Configuration validation

### 4. Operational Excellence
- ✅ Monitoring integration
- ✅ Automated backups with retention
- ✅ Health checks and validation
- ✅ Retry logic for flaky operations
- ✅ Proper timeout values
- ✅ Log rotation

### 5. Module Best Practices
- ✅ FQCN for all modules
- ✅ Explicit module parameters
- ✅ Template validation
- ✅ Service `enabled` parameter
- ✅ File ownership specification

## Error Tolerance Levels

The policy uses three error tolerance levels:

- **High** - Critical security/functionality issues (e.g., no_log, permissions)
- **Medium** - Important best practices (e.g., handlers, backups)
- **Low** - Style and optimization recommendations (e.g., FQCN, tags)

## Customization

You can customize the policy by:

1. **Adjusting error_tolerance** values in evaluators
2. **Modifying threshold values** (e.g., minimum task count)
3. **Adding new evaluators** for organization-specific rules
4. **Updating the eval_expression** to change validation logic
5. **Creating specialized policies** for different environments (dev/staging/prod)

## References

- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [ansible-lint Rules](https://ansible-lint.readthedocs.io/rules/)
- [JQ Manual](https://stedolan.github.io/jq/manual/)
- [Tirith Policy Documentation](../../../docs/)

## Contributing

When adding new checks:
1. Add the evaluator to the policy JSON
2. Update the test suite with specific test cases
3. Document the JQ query logic
4. Update this README with the new check
5. Test with both passing and failing scenarios
