# jq_query Query Tests for Tirith JSON Provider

This directory contains comprehensive tests for the `jq_query` operation type in the Tirith JSON provider.

## Test Coverage

The test suite (`test_jq_query.py`) includes 14 comprehensive test cases:

### 1. Basic Operations
- **test_jq_query_basic_query**: Extract single value from nested structure
- **test_jq_query_array_projection**: Get all elements from array (e.g., all task names)
- **test_jq_query_length_function**: Count array elements

### 2. Filtering & Selection
- **test_jq_query_select_filter**: Filter array elements based on conditions
- **test_jq_query_pipe_expression**: Combine multiple operations with pipes

### 3. Transformations
- **test_jq_query_object_construction**: Extract specific fields into new object
- **test_jq_query_map_function**: Transform array elements

### 4. Conditionals
- **test_jq_query_conditional**: Use if-then-else expressions

### 5. Type Operations
- **test_jq_query_type_checking**: Check data types
- **test_jq_query_has_key_check**: Verify object key existence

### 6. Error Handling
- **test_jq_query_invalid_query**: Handle syntax errors gracefully
- **test_jq_query_missing_query**: Handle missing query parameter
- **test_jq_query_no_results**: Handle queries that return no results

### 7. Real-World Use Cases
- **test_jq_query_complex_ansible_playbook**: Validate realistic Ansible playbook structure

## Running the Tests

### Run all jq_query tests:
```bash
pytest tests/providers/json/test_jq_query.py -v
```

### Run specific test:
```bash
pytest tests/providers/json/test_jq_query.py::test_jq_query_basic_query -v
```

### Run with coverage:
```bash
pytest tests/providers/json/test_jq_query.py --cov=tirith.providers.json --cov-report=html
```

## Test Data Examples

### Example 1: Simple Field Access
```python
input_data = [{"name": "web", "vars": {"region": "us-east-1"}}]
query = ".[0].vars.region"
# Returns: "us-east-1"
```

### Example 2: Array Projection
```python
input_data = [{"tasks": [{"name": "Task1"}, {"name": "Task2"}]}]
query = ".[0].tasks[].name"
# Returns: ["Task1", "Task2"]
```

### Example 3: Filtering
```python
input_data = [{"tasks": [
    {"name": "T1", "become": True},
    {"name": "T2", "become": False}
]}]
query = '[.[0].tasks[] | select(.become == true)]'
# Returns: [{"name": "T1", "become": True}]
```

### Example 4: Conditional
```python
input_data = {"environment": "production"}
query = 'if .environment == "production" then "secure" else "insecure" end'
# Returns: "secure"
```

## Example Policy Files

### policy_jq_query_ansible.json
Comprehensive Ansible playbook validation policy demonstrating:
- Privilege escalation checks
- Region validation
- Task count requirements
- Task naming conventions
- Service configuration validation
- Package state checks
- Template parameter validation

Run it with:
```bash
tirith -input-path playbook_jmespath.yml -policy-path policy_jq_query_ansible.json
```

## Common jq_query Query Patterns

### Count filtered items:
```json
{
  "query": "[.[] | select(.condition == true)] | length"
}
```

### Extract multiple fields:
```json
{
  "query": ".object | {field1, field2, field3}"
}
```

### Check all items match condition:
```json
{
  "query": "[.items[] | .enabled] | all"
}
```

### Get unique values:
```json
{
  "query": "[.items[].name] | unique"
}
```

### Nested filtering:
```json
{
  "query": "[.[] | select(.tags | contains([\"important\"]))]"
}
```

## Expected Test Results

All 14 tests should pass:
```
test_jq_query_basic_query PASSED                             [  7%]
test_jq_query_array_projection PASSED                        [ 14%]
test_jq_query_select_filter PASSED                           [ 21%]
test_jq_query_length_function PASSED                         [ 28%]
test_jq_query_object_construction PASSED                     [ 35%]
test_jq_query_map_function PASSED                            [ 42%]
test_jq_query_conditional PASSED                             [ 50%]
test_jq_query_pipe_expression PASSED                         [ 57%]
test_jq_query_invalid_query PASSED                           [ 64%]
test_jq_query_missing_query PASSED                           [ 71%]
test_jq_query_no_results PASSED                              [ 78%]
test_jq_query_complex_ansible_playbook PASSED                [ 85%]
test_jq_query_has_key_check PASSED                           [ 92%]
test_jq_query_type_checking PASSED                           [100%]

14 passed in 0.06s
```

## Comparison with JMESPath Tests

Both test suites follow similar patterns but use different query syntaxes:

| Test Case | JMESPath Query | jq_query Query |
|-----------|----------------|----------|
| Basic field | `[0].vars.region` | `.[0].vars.region` |
| Array projection | `[0].tasks[*].name` | `.[0].tasks[].name` |
| Filter | `[0].tasks[?become]` | `[.[0].tasks[] \| select(.become)]` |
| Length | `length([0].tasks)` | `.[0].tasks \| length` |
| Multi-select | `[0].{name: name, id: id}` | `.[0] \| {name, id}` |

## Debugging Tips

1. **Test queries interactively**: Use https://jq_queryplay.org/ to test jq_query queries
2. **Start simple**: Build complex queries incrementally
3. **Check types**: Use `| type` to verify data types
4. **Pretty print**: Use `jq_query .` to format JSON for inspection
5. **Use filters**: Add `select()` filters step by step

## Integration Tests

The jq_query operation integrates seamlessly with:
- **All Tirith conditions**: Equals, Contains, RegexMatch, etc.
- **Error tolerance levels**: Low, Medium, High
- **Eval expressions**: Combine multiple jq_query evaluators with `&&`, `||`, `!`
- **Other operation types**: Mix with `get_value` and `jmespath`

## Contributing

When adding new tests:
1. Follow the existing test structure
2. Use descriptive test names starting with `test_jq_query_`
3. Include docstrings explaining what's being tested
4. Test both success and failure cases
5. Use realistic data structures when possible
6. Ensure all tests use `is` for boolean comparisons (PEP 8)

## References

- **jq_query Documentation**: https://stedolan.github.io/jq_query/manual/
- **Python jq_query Package**: https://github.com/mwilliamson/jq_query.py
- **Tirith Core Tests**: `tests/core/`
- **JSON Provider Tests**: `tests/providers/json/`
