# Ansible-Lint Policy Examples

This directory contains Tirith policies that replicate common ansible-lint checks using JMESPath queries.

## Files

- **`policy_ansible_lint.json`** - Comprehensive policy checking 40+ ansible-lint rules
- **`playbook_ansible_lint.yml`** - Good example following best practices
- **`playbook_ansible_lint_violations.yml`** - Bad example showing common violations

## Ansible-Lint Rules Covered

### Critical Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `name[play]` | All plays should be named | `playbook_has_name` |
| `name[task]` | All tasks should be named | `all_tasks_named` |
| `name[casing]` | Task names should be capitalized | `task_name_format` |
| `no-log-password` | Tasks with passwords need no_log | `no_log_password` |
| `risky-file-permissions` | File permissions should not be 0777 | `risky_file_permissions` |
| `deprecated-command-syntax` | Use 'become' not 'sudo' | `sudo_deprecated` |
| `deprecated-module` | Avoid deprecated modules | `deprecated_module` |

### Important Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `command-instead-of-module` | Use specific modules not command/shell | `no_command_instead_of_module` |
| `command-instead-of-shell` | Use 'command' when shell features not needed | `no_command_instead_of_shell` |
| `package-latest` | Don't use state: latest | `package_latest_forbidden` |
| `risky-shell-pipe` | Shells with pipes need pipefail | `risky_shell_pipe` |
| `no-changed-when` | Commands need changed_when | `no_changed_when` |
| `become-user-without-become` | become_user requires become | `become_user_without_become` |
| `deprecated-bare-vars` | Variables need Jinja2 syntax | `deprecated_bare_vars` |

### Best Practice Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `literal-compare` | Don't compare to True/False | `literal_compare` |
| `no-jinja-when` | when should not use {{ }} | `no_jinja_when` |
| `empty-string-compare` | Don't compare to empty string | `no_empty_strings` |
| `no-relative-paths` | Use absolute paths | `no_relative_paths` |
| `deprecated-local-action` | Use delegate_to instead | `deprecated_local_action` |
| `ignore-errors` | Use sparingly | `ignore_errors_minimal` |
| `inline-env-var` | Use environment keyword | `inline_env_var` |
| `args` | Use module parameters directly | `args_module_usage` |
| `meta-no-tags` | Meta tasks shouldn't have tags | `meta_no_tags` |

### Performance Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `performance` | Disable gather_facts for localhost | `gather_facts_smart` |
| `complexity` | Avoid deeply nested blocks | `max_block_depth` |
| `handler-usage` | Use handlers for service restarts | `handler_usage` |

### Quality Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `fqcn` | Use FQCN for modules | `no_free_form_with_fqcn` |
| `yaml` | YAML should be valid | `yaml_formatting` |
| `key-order[task]` | Task keys should be ordered | `key_order_check` |
| `run-once` | run_once needs delegate_to | `run_once_delegation` |
| `unnamed-task` | Handlers need unique names | `handler_names_unique` |

### Security Rules

| Rule ID | Description | Policy Check |
|---------|-------------|--------------|
| `var-naming[no-role-prefix]` | Sensitive vars should use vault | `no_plain_text_passwords` |
| `no-log-password` | Password tasks need no_log | `no_log_password` |
| `risky-file-permissions` | Avoid overly permissive modes | `risky_file_permissions` |

## Example Violations

### Missing Task Names
```yaml
# BAD
- command: echo "hello"

# GOOD
- name: Print greeting message
  ansible.builtin.command: echo "hello"
```

### Package with Latest
```yaml
# BAD
- name: Install nginx
  yum:
    name: nginx
    state: latest

# GOOD
- name: Install nginx
  ansible.builtin.yum:
    name: nginx
    state: present
```

### Plain Text Passwords
```yaml
# BAD
vars:
  db_password: "MyPassword123"
  
tasks:
  - name: Set MySQL password
    shell: mysql -e "SET PASSWORD='{{ db_password }}'"

# GOOD
vars:
  db_password: "{{ vault_db_password }}"
  
tasks:
  - name: Set MySQL password
    ansible.builtin.shell: mysql -e "SET PASSWORD='{{ db_password }}'"
    no_log: true
```

### Risky File Permissions
```yaml
# BAD
- name: Create file
  file:
    path: /tmp/file
    mode: 0777

# GOOD
- name: Create file
  ansible.builtin.file:
    path: /tmp/file
    mode: '0644'
```

### Using Shell Instead of Module
```yaml
# BAD
- name: Clone repository
  shell: git clone https://github.com/example/repo.git

# GOOD
- name: Clone repository
  ansible.builtin.git:
    repo: https://github.com/example/repo.git
    dest: /opt/repo
```

### Shell Pipe Without Pipefail
```yaml
# BAD
- name: Search logs
  shell: cat /var/log/app.log | grep ERROR

# GOOD
- name: Search logs
  ansible.builtin.shell: |
    set -o pipefail
    cat /var/log/app.log | grep ERROR
  args:
    executable: /bin/bash
```

### When with Jinja2 Delimiters
```yaml
# BAD
- name: Check variable
  debug:
    msg: "Defined"
  when: "{{ my_var is defined }}"

# GOOD
- name: Check variable
  ansible.builtin.debug:
    msg: "Defined"
  when: my_var is defined
```

### Deprecated Sudo
```yaml
# BAD
- hosts: all
  sudo: yes
  tasks: []

# GOOD
- name: Configure servers
  hosts: all
  become: true
  tasks: []
```

## Running the Policy

### Convert YAML to JSON
```bash
# Convert good example
python3 -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(open('playbook_ansible_lint.yml'))))" > playbook_ansible_lint.json

# Convert bad example
python3 -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(open('playbook_ansible_lint_violations.yml'))))" > playbook_ansible_lint_violations.json
```

### Run Tirith Policy
```bash
# Check good playbook (should pass most checks)
tirith -policy-path policy_ansible_lint.json -input-path playbook_ansible_lint.json

# Check bad playbook (should fail many checks)
tirith -policy-path policy_ansible_lint.json -input-path playbook_ansible_lint_violations.json
```

## Comparison with ansible-lint

### Advantages of Tirith Policy Approach

1. **Customizable** - Adjust severity and error tolerance per rule
2. **Integrated** - Works with existing Tirith workflows
3. **Extensible** - Add custom rules with JMESPath
4. **CI/CD Ready** - JSON output for automation
5. **Policy as Code** - Version control your lint rules

### When to Use ansible-lint Instead

1. **Development** - Real-time linting in IDE
2. **Formatting** - Auto-fix capabilities
3. **Complete Coverage** - All official ansible-lint rules
4. **Community Rules** - Pre-built rule sets

## Best Practices

1. **Start with Critical Rules** - Focus on security and breaking changes
2. **Use Error Tolerance** - Allow some warnings initially
3. **Gradual Adoption** - Enable more rules over time
4. **Team Agreement** - Document which rules to enforce
5. **CI Integration** - Run in pull request checks

## Error Tolerance

Many checks include `error_tolerance` to allow gradual adoption:

```json
{
    "id": "package_latest_forbidden",
    "condition": {
        "type": "Equals",
        "value": 0,
        "error_tolerance": 2  // Allow up to 2 violations
    }
}
```

## Custom Rules

Add your own organization-specific rules:

```json
{
    "id": "company_naming_convention",
    "description": "Task names must include ticket number",
    "provider_args": {
        "operation_type": "jmespath",
        "query": "[*].tasks[*].name"
    },
    "condition": {
        "type": "RegexMatch",
        "value": ".*\\[TICKET-[0-9]+\\].*"
    }
}
```

## References

- [Ansible Lint Documentation](https://ansible-lint.readthedocs.io/)
- [Ansible Lint Rules](https://ansible-lint.readthedocs.io/rules/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [JMESPath Tutorial](https://jmespath.org/tutorial.html)
