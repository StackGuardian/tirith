# JMESPath Examples for Tirith Policy

This directory contains comprehensive examples of using JMESPath queries with Tirith policies for Ansible playbook validation.

## Files

- **`policy_playbook_jmespath.json`** - Production-ready policy with 20 evaluators showcasing practical JMESPath patterns
- **`policy_advanced_jmespath.json`** - Advanced examples with 25 evaluators demonstrating complex JMESPath features
- **`playbook_jmespath.yml`** - Sample Ansible playbook designed to work with the policies

## JMESPath Features Demonstrated

### 1. **Basic Filtering**
```json
{
    "query": "[0].tasks[?'amazon.aws.ec2_instance'].name"
}
```
Filters tasks that contain the `amazon.aws.ec2_instance` module.

### 2. **Comparison Operators in Filters**
```json
{
    "query": "[0].tasks[?wait_for && wait_for.timeout > `100`].name"
}
```
Filters tasks with timeout greater than 100.

### 3. **Boolean Logic (AND/OR)**
```json
{
    "query": "[0].tasks[?(become == `true` || no_log == `true`) && contains(to_string(@), 'mysql')].name"
}
```
Complex filtering with multiple conditions.

### 4. **Projections**
```json
{
    "query": "[0].tasks[*].name"
}
```
Projects all task names into an array.

### 5. **Multi-Select Hash**
```json
{
    "query": "[0].tasks[?register].{task_name: name, variable: register}"
}
```
Creates custom objects with selected fields.

### 6. **Multi-Select List**
```json
{
    "query": "[0].tasks[*].[name, register]"
}
```
Creates arrays of specific fields.

### 7. **Pipe Expressions**
```json
{
    "query": "[0].tasks[?become == `true`] | [*].name | length(@)"
}
```
Chains operations: filter, project, then count.

### 8. **Functions**

#### String Functions
- `contains(string, substring)` - Check if string contains substring
- `starts_with(string, prefix)` - Check if string starts with prefix
- `ends_with(string, suffix)` - Check if string ends with suffix
- `join(separator, array)` - Join array elements into string

#### Array Functions
- `length(array)` - Get array length
- `sort(array)` - Sort array
- `sort_by(array, &expr)` - Sort by expression
- `reverse(array)` - Reverse array order
- `max(array)` - Get maximum value
- `min(array)` - Get minimum value
- `sum(array)` - Sum numeric values
- `avg(array)` - Calculate average

#### Type Functions
- `type(value)` - Get type of value
- `to_string(value)` - Convert to string
- `to_number(value)` - Convert to number

### 9. **Array Slicing**
```json
{
    "query": "[0].tasks[:3].name"
}
```
Gets first 3 tasks.

```json
{
    "query": "[0].tasks[-1].name"
}
```
Gets last task.

### 10. **Flattening**
```json
{
    "query": "[0].tasks[*].modules[] | @"
}
```
Flattens nested arrays.

### 11. **Object Functions**
- `keys(object)` - Get object keys
- `values(object)` - Get object values
- `to_entries(object)` - Convert to key-value pairs
- `merge(obj1, obj2)` - Merge objects

### 12. **Nested Filtering**
```json
{
    "query": "[0].tasks[?'amazon.aws.ec2_instance' && `amazon.aws.ec2_instance`.instance_tags.Environment == 'production'].name"
}
```
Filters based on deeply nested values.

### 13. **Current Node Reference**
- `@` - Current node in expression
- `` ` `` - Literal values (backticks)

### 14. **Complex Expressions**
```json
{
    "query": "[0].tasks[?contains(keys(@), 'ansible.builtin.package')].`ansible.builtin.package`.{name: name, state: state}"
}
```
Combines multiple features for sophisticated queries.

## Example Use Cases

### Security Validation
```json
{
    "id": "check_sensitive_tasks_no_log",
    "provider_args": {
        "operation_type": "jmespath",
        "query": "[0].tasks[?contains(to_string(@), 'password')].no_log"
    },
    "condition": {
        "type": "Equals",
        "value": true
    }
}
```

### Resource Compliance
```json
{
    "id": "check_production_instance_types",
    "provider_args": {
        "operation_type": "jmespath",
        "query": "[0].tasks[?'amazon.aws.ec2_instance' && `amazon.aws.ec2_instance`.instance_tags.Environment == 'production'].`amazon.aws.ec2_instance`.instance_type"
    },
    "condition": {
        "type": "Contains",
        "value": ["t2.micro", "t3.micro"]
    }
}
```

### Code Quality
```json
{
    "id": "check_all_tasks_have_names",
    "provider_args": {
        "operation_type": "jmespath",
        "query": "[0].tasks[?!name] | length(@)"
    },
    "condition": {
        "type": "Equals",
        "value": 0
    }
}
```

### Metadata Extraction
```json
{
    "id": "extract_registered_variables",
    "provider_args": {
        "operation_type": "jmespath",
        "query": "[0].tasks[?register].{name: name, var: register}"
    }
}
```

## Running the Examples

To test these policies with Tirith (once `jmespath` is implemented):

```bash
# Convert YAML to JSON first
python -c "import yaml, json, sys; print(json.dumps(yaml.safe_load(sys.stdin)))" < playbook_jmespath.yml > playbook_jmespath.json

# Run with policy
tirith -policy-path policy_playbook_jmespath.json -input-path playbook_jmespath.json
```

## JMESPath Resources

- [JMESPath Official Specification](https://jmespath.org/specification.html)
- [JMESPath Tutorial](https://jmespath.org/tutorial.html)
- [JMESPath Playground](https://jmespath.org/) - Test queries interactively

## Implementation Notes

When implementing `jmespath` in Tirith:

1. Use the `jmespath` Python library
2. Handle errors gracefully (invalid queries, missing paths)
3. Consider query performance for large playbooks
4. Support both single values and arrays as results
5. Provide clear error messages for syntax issues

```python
import jmespath

def jmespath(provider_args: Dict, input_data: Dict) -> List[dict]:
    query = provider_args["query"]
    try:
        result = jmespath.search(query, input_data)
        if result is None:
            return [create_result_dict(
                value=ProviderError(severity_value=2),
                err=f"query: `{query}` returned no results"
            )]
        # Ensure result is always a list for consistency
        if not isinstance(result, list):
            result = [result]
        return [create_result_dict(value=value) for value in result]
    except jmespath.exceptions.JMESPathError as e:
        return [create_result_dict(
            value=ProviderError(severity_value=99),
            err=f"Invalid JMESPath query: {str(e)}"
        )]
```
