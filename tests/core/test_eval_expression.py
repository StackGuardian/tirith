"""
Security regression tests for `final_evaluator`.

An `eval_expression` comes from a policy file, which is untrusted input (policies are pulled from
repositories, pull requests and the platform). It must be interpreted, never executed.

None of these tests runs a hostile payload. They check that the expression is rejected *before*
evaluation, and a guard fails the test if `eval`, `exec` or code-compiling `compile` is reached at all.
"""

import ast
import builtins
import inspect

import pytest

from tirith.core import core
from tirith.core.core import MAX_EVAL_EXPRESSION_LENGTH, final_evaluator

_UNSUPPORTED_PREFIX = "Unsupported syntax in eval_expression: "

PY_COMPILE_ONLY_AST = ast.PyCF_ONLY_AST


@pytest.fixture
def no_code_execution(monkeypatch):
    """Fail the test if the expression is ever compiled to code or passed to eval/exec."""
    real_compile = builtins.compile

    def forbidden(name):
        def _fail(*args, **kwargs):
            raise AssertionError(f"final_evaluator reached builtins.{name}()")

        return _fail

    def guarded_compile(source, filename, mode, flags=0, *args, **kwargs):
        # ast.parse() calls compile() with PyCF_ONLY_AST, which builds a tree and runs nothing.
        if not flags & PY_COMPILE_ONLY_AST:
            raise AssertionError("final_evaluator compiled an expression to executable code")
        return real_compile(source, filename, mode, flags, *args, **kwargs)

    monkeypatch.setattr(builtins, "eval", forbidden("eval"))
    monkeypatch.setattr(builtins, "exec", forbidden("exec"))
    monkeypatch.setattr(builtins, "compile", guarded_compile)


def test_core_never_calls_eval_exec_or_compile():
    """Static check: the module has no call to eval/exec/compile that a refactor could re-introduce."""
    tree = ast.parse(inspect.getsource(core))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"eval", "exec", "compile"}
    }
    assert called == set()


# -- documented expressions keep their meaning ---------------------------------------------------


@pytest.mark.parametrize(
    "expression, values, expected",
    [
        ("a", dict(a=True), True),
        ("a", dict(a=False), False),
        ("!a", dict(a=False), True),
        ("!!a", dict(a=True), True),
        ("a && b", dict(a=True, b=True), True),
        ("a && b", dict(a=True, b=False), False),
        ("a || b", dict(a=False, b=True), True),
        ("a || b", dict(a=False, b=False), False),
        ("(a || b) && c", dict(a=True, b=False, c=True), True),
        ("(a || b) && c", dict(a=True, b=False, c=False), False),
        ("!(a && b) && c", dict(a=False, b=True, c=True), True),
        # Precedence is documented: `!` binds tighter than `&&`, which binds tighter than `||`.
        ("a || b && c", dict(a=True, b=False, c=False), True),
        ("!a || b", dict(a=True, b=True), True),
        # Whitespace is ignored, including none at all.
        ("a&&b||!c", dict(a=True, b=True, c=True), True),
        ("  a   &&   b  ", dict(a=True, b=True), True),
        # An id that is not a valid Python name still works when it is defined.
        ("eval-id-1 && !eval-id-2", {"eval-id-1": True, "eval-id-2": False}, True),
        # An id that is a prefix of another is not confused with it.
        ("check && check_2", dict(check=True, check_2=False), False),
    ],
)
def test_documented_expressions(expression, values, expected, no_code_execution):
    assert final_evaluator(expression, values) == (expected, [])


@pytest.mark.parametrize(
    "expression, values, expected",
    [
        # A skipped check is removed together with its `!`, not treated as false.
        ("!skipped && ok", dict(skipped=None, ok=True), True),
        ("!skipped && ok", dict(skipped=None, ok=False), False),
        ("skipped && ok", dict(skipped=None, ok=True), True),
        ("skipped || ok", dict(skipped=None, ok=False), False),
        # Everything removed: nothing left to evaluate.
        ("skipped", dict(skipped=None), None),
        ("!skipped", dict(skipped=None), None),
        ("a && b", dict(a=None, b=None), None),
        ("!(a || b)", dict(a=None, b=None), None),
    ],
)
def test_skipped_checks_are_removed(expression, values, expected, no_code_execution):
    assert final_evaluator(expression, values) == (expected, [])


def test_undefined_ids_are_removed_and_reported_in_order(no_code_execution):
    result, errors = final_evaluator("ghost_a && real && ghost_b", dict(real=True))
    assert result is True
    assert errors == ["The following evaluator ids are not defined and have been removed: ghost_a, ghost_b"]


def test_all_undefined_ids_gives_none(no_code_execution):
    result, errors = final_evaluator("ghost", {})
    assert result is None
    assert errors == ["The following evaluator ids are not defined and have been removed: ghost"]


# -- unsupported syntax is rejected without evaluation -------------------------------------------


@pytest.mark.parametrize(
    "expression, node_type",
    [
        # The reported bypass: a lambda hides attribute access and calls from the old `co_names` check,
        # which only looked at the outermost code object.
        ("(lambda:().__class__.__base__.__subclasses__())()", "Lambda"),
        ("(lambda:ghost)()", "Lambda"),
        # Object-hierarchy access.
        ("[].__class__.__base__", "Attribute"),
        ("().__class__", "Attribute"),
        ("a.__class__", "Attribute"),
        # Calls.
        ("print(1)", "Call"),
        ("a()", "Call"),
        ("__import__('os')", "Call"),
        # Comprehensions and generators.
        ("[(x)for(x)in(a)]", "ListComp"),
        ("{(x)for(x)in(a)}", "SetComp"),
        ("{(x):(x)for(x)in(a)}", "DictComp"),
        ("((x)for(x)in(a))", "GeneratorExp"),
        # Containers, subscripts, slices.
        ("[a]", "List"),
        ("(a,b)", "Tuple"),
        ("{a}", "Set"),
        ("{1:2}", "Dict"),
        ("a[0]", "Subscript"),
        # Comparisons, conditionals, walrus, await, f-strings, starred.
        ("a == b", "Compare"),
        ("(a)in(b)", "Compare"),
        ("(a)if(b)else(c)", "IfExp"),
        ("(x:=a)", "NamedExpr"),
        ("f'{a}'", "JoinedStr"),
        ("[*a]", "Starred"),
        # Unary operators other than `!`.
        ("-a", "USub"),
        ("~a", "Invert"),
        ("+a", "UAdd"),
        # Literals other than True/False/None.
        ("1", "Constant"),
        ("'text'", "Constant"),
        ("1.5", "Constant"),
        ("b'x'", "Constant"),
        ("...", "Constant"),
    ],
)
def test_unsupported_syntax_is_rejected(expression, node_type, no_code_execution):
    # Written without spaces, which the engine strips before parsing, so every payload is one that
    # would still parse. No ids are defined, so nothing is substituted into the payload first.
    result, errors = final_evaluator(expression, {})
    assert result is False
    assert len(errors) == 1
    assert errors[0].startswith(_UNSUPPORTED_PREFIX)
    assert node_type in errors[0]


def test_reported_bypass_pattern_is_rejected_without_evaluation(no_code_execution):
    payload = "(lambda:().__class__.__base__.__subclasses__())()"
    result, errors = final_evaluator(payload, {})
    assert result is False
    assert errors[0].startswith(_UNSUPPORTED_PREFIX)
    assert "Lambda" in errors[0] and "Call" in errors[0] and "Attribute" in errors[0]


def test_unsupported_syntax_is_rejected_even_next_to_valid_operands(no_code_execution):
    # One bad node poisons the whole expression; a passing check must not carry it through.
    result, errors = final_evaluator("ok || [].__class__.__base__", dict(ok=True))
    assert result is False
    assert errors[0].startswith(_UNSUPPORTED_PREFIX)


def test_rejection_does_not_depend_on_names_resolving(no_code_execution):
    # The old guard keyed off the names left over after substitution; this must not.
    assert final_evaluator("(lambda:True)()", {})[0] is False


def test_hostile_text_in_a_check_id_cannot_inject_syntax(no_code_execution):
    # An id is substituted by regex, so a hostile id must be escaped rather than interpreted as a pattern.
    result, errors = final_evaluator("a.b", {"a.b": True})
    assert (result, errors) == (True, [])
    result, errors = final_evaluator("axb", {"a.b": False})
    assert result is None  # the id `a.b` must not match `axb`; `axb` is simply undefined
    assert errors == ["The following evaluator ids are not defined and have been removed: axb"]


# -- malformed input -----------------------------------------------------------------------------


@pytest.mark.parametrize("expression", ["", "   ", "a &&", "&& a", "a ||", "(a", "a)", "a && && b", "!", "a $ b"])
def test_malformed_expression_aborts_with_syntax_error(expression, no_code_execution):
    with pytest.raises(SyntaxError):
        final_evaluator(expression, dict(a=True, b=True))


@pytest.mark.parametrize(
    "expression, wrong, right",
    [("a & b", "&", "&&"), ("a | b", "|", "||")],
)
def test_single_bitwise_operators_name_the_correct_operator(expression, wrong, right, no_code_execution):
    with pytest.raises(ValueError, match=f"Unsupported operator '{wrong}' in eval_expression. Use '{right}' instead."):
        final_evaluator(expression, dict(a=True, b=True))


@pytest.mark.parametrize("expression", ["a + b", "a - b", "a * b", "a ** b", "a // b", "a << b", "a @ b"])
def test_other_binary_operators_are_rejected(expression, no_code_execution):
    with pytest.raises(ValueError, match="Unsupported operator in eval_expression"):
        final_evaluator(expression, dict(a=True, b=True))


def test_overlong_expression_is_rejected(no_code_execution):
    with pytest.raises(ValueError, match="longer than"):
        final_evaluator("a && " * MAX_EVAL_EXPRESSION_LENGTH + "a", dict(a=True))


def test_deeply_nested_expression_fails_cleanly_rather_than_crashing(no_code_execution):
    # Under the length limit but nested far past the interpreter's recursion limit.
    expression = "!" * 5000 + "a"
    assert len(expression) < MAX_EVAL_EXPRESSION_LENGTH
    # Must be the clean error on every interpreter: the 3.8 parser raises MemoryError for this, 3.9+
    # RecursionError, and neither may escape.
    with pytest.raises(ValueError, match="nested too deeply"):
        final_evaluator(expression, dict(a=True))


def test_long_but_legitimate_expression_is_accepted(no_code_execution):
    ids = {f"check_{i}": True for i in range(200)}
    expression = " && ".join(ids)
    assert final_evaluator(expression, ids) == (True, [])
