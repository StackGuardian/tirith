"""
The Builder: assemble a policy by picking a provider, an operation and a condition.

The form is generated from tui/schema.py, so the fields change with the operation and every
argument shown is one the provider actually reads. That is the value over writing JSON by
hand: the terraform provider alone has seven operations taking different arguments, none of
them documented in a machine-readable form anywhere in the engine.

Checks accumulate into a list, and the generated policy is shown as JSON as it is built --
the policy is the output, so it is never hidden behind a "generate" button.
"""

import json

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, Label, ListItem, ListView, Select, Static

from .. import render, schema, validate


# What a value typed into the condition's value box should become. The engine compares against
# real JSON types -- `Equals: "true"` and `Equals: true` are different questions -- so the box
# is parsed as JSON with a fallback to string, which is what a user typing `production` means.
def parse_value(raw: str):
    """
    Parse a condition value the way the policy will hold it.

    Bare words become strings, so `production` works without quoting, but `true`, `42`, `null`
    and `["a","b"]` keep their JSON meaning. Without this every value would be a string and
    numeric comparisons would silently never match.
    """
    text = raw.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except ValueError:
        return text


class BuilderView(Vertical):
    """Form on the left, generated policy on the right."""

    def __init__(self, on_policy_built=None, **kwargs):
        super().__init__(**kwargs)
        # Called with the generated policy dict when the user sends it to the playground.
        self._on_policy_built = on_policy_built
        self._checks = []
        # Opens on terraform_plan rather than the alphabetically-first provider: it is what
        # nearly every policy targets, and starting on infracost would make the first form a
        # user sees the least representative one.
        self._provider_name = schema.DEFAULT_PROVIDER
        self._operation_name = ""
        # Set once the user edits the expression themselves; see current_expression.
        self._expression_is_custom = False

    DESCRIPTION = "Assemble a policy from fields the chosen provider actually reads. Values keep their JSON types."

    def compose(self) -> ComposeResult:
        yield Static(self.DESCRIPTION, classes="tab-description")
        with Horizontal(id="builder-body"):
            with VerticalScroll(id="builder-form"):
                yield Label("Provider", classes="field-label")
                yield Select(
                    [(name, name) for name in schema.provider_names()],
                    value=self._provider_name,
                    allow_blank=False,
                    id="provider-select",
                )
                yield Static("", id="provider-summary", classes="field-help")

                yield Label("Operation", classes="field-label")
                # Populated with the first provider's operations rather than left empty:
                # Select rejects an empty option list when it cannot be blank.
                yield Select(
                    [(op.name, op.name) for op in schema.operations_for(self._provider_name)],
                    allow_blank=False,
                    id="operation-select",
                )
                yield Static("", id="operation-summary", classes="field-help")

                yield Static("", id="arg-fields")

                yield Label("Condition", classes="field-label")
                yield Select(
                    [(name, name) for name in schema.evaluator_names()],
                    value="Equals",
                    allow_blank=False,
                    id="evaluator-select",
                )
                yield Static("", id="evaluator-summary", classes="field-help")
                yield Input(placeholder="Value to compare against, as JSON", id="value-input")

                yield Label("Check id", classes="field-label")
                yield Input(placeholder="e.g. bucket_is_private", id="id-input")

                yield Horizontal(
                    Button("Add check", variant="primary", id="add-check"),
                    Button("Clear", id="clear-checks"),
                    id="builder-buttons",
                )

            # The right pane holds the things that concern the policy as a whole -- its checks,
            # how they combine, and the JSON that results -- while the left builds one check at
            # a time. It also keeps the expression box on screen: stacked under the form it
            # landed below the fold on a normal terminal, which is no use for the one field
            # that cannot be derived from anything else.
            with Vertical(id="builder-preview"):
                yield Static("Generated policy", classes="pane-title")
                yield VerticalScroll(Static(id="policy-json"), id="policy-json-scroll")

                yield Static("Checks in this policy", classes="pane-title")
                yield ListView(id="check-list")

                yield Static("How the checks combine", classes="pane-title")
                yield Static(
                    "&& all must pass · || any may pass · ! negates · ( ) group",
                    classes="field-help",
                )
                yield Input(placeholder="e.g. a && !b", id="expression-input")

                yield Static("", id="builder-findings")
                yield Button("Open in playground", variant="success", id="send-to-playground")

    def on_mount(self) -> None:
        self._refresh_provider()

    # ---------------------------------------------------------------- events

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "provider-select":
            self._provider_name = str(event.value)
            self._refresh_provider()
        elif event.select.id == "operation-select":
            self._operation_name = str(event.value)
            self._refresh_operation()
        elif event.select.id == "evaluator-select":
            self._refresh_evaluator()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "expression-input":
            return
        # Anything the user types here -- including clearing it back to empty -- takes over
        # from the generated default. Emptying it is a deliberate state, not a reset.
        self._expression_is_custom = True
        self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-check":
            self._add_check()
        elif event.button.id == "clear-checks":
            self._checks = []
            # The expression named checks that no longer exist, so a custom one is not worth
            # keeping either -- it would report every id in it as undefined.
            self._expression_is_custom = False
            self._refresh_preview()
        elif event.button.id == "send-to-playground":
            if self._on_policy_built and self._checks:
                self._on_policy_built(self.build_policy())

    # ----------------------------------------------------------------- form

    def _refresh_provider(self) -> None:
        provider = schema.PROVIDERS[self._provider_name]
        # Naming the document the provider expects, because choosing a provider is choosing
        # what you must feed it -- and a plan evaluated against the kubernetes provider fails
        # in a way that says nothing about the real mistake.
        self.query_one("#provider-summary", Static).update(
            f"{render.escape(provider.summary)}\n[b]Expects:[/b] {render.escape(provider.input_hint)}"
        )

        operations = provider.operations
        select = self.query_one("#operation-select", Select)
        select.set_options([(op.name, op.name) for op in operations])
        if operations:
            self._operation_name = operations[0].name
            select.value = self._operation_name
        self._refresh_operation()

    def _refresh_operation(self) -> None:
        operation = schema.operation_for(self._provider_name, self._operation_name)
        summary = self.query_one("#operation-summary", Static)
        if operation is None:
            summary.update("")
            return
        summary.update(render.escape(operation.summary))
        self._rebuild_arg_fields(operation)
        self._refresh_preview()

    def _rebuild_arg_fields(self, operation) -> None:
        """
        Replace the argument inputs with the ones this operation takes.

        Rebuilt rather than hidden, because the arguments differ per operation and a stale
        value left in a hidden field would end up in the generated policy.

        The removal is awaited before anything is mounted. `remove_children()` is asynchronous,
        so mounting straight after it races the removal: two operations that share an argument
        name -- and most of the terraform ones share `terraform_resource_type` -- collide on
        the widget id and Textual raises DuplicateIds.
        """
        container = self.query_one("#arg-fields", Static)

        widgets = []
        for arg in operation.args:
            # Name and help on one line. Two lines per argument pushed the expression box off
            # the bottom of a normal terminal, and the help is short enough to sit inline.
            marker = " [b]*[/b]" if arg.required else ""
            widgets.append(
                Static(
                    f"[b]{render.escape(arg.name)}[/b]{marker}  [dim]{render.escape(arg.help)}[/dim]",
                    classes="field-label-inline",
                )
            )
            if arg.choices:
                widgets.append(
                    Select(
                        [(choice, choice) for choice in arg.choices],
                        allow_blank=True,
                        id=f"arg-{arg.name}",
                    )
                )
            else:
                widgets.append(Input(placeholder=arg.placeholder, id=f"arg-{arg.name}"))

        async def replace():
            await container.remove_children()
            await container.mount_all(widgets)

        self.call_next(replace)

    def _refresh_evaluator(self) -> None:
        name = str(self.query_one("#evaluator-select", Select).value)
        info = schema.EVALUATORS.get(name)
        summary = self.query_one("#evaluator-summary", Static)
        value_input = self.query_one("#value-input", Input)

        if info is None:
            summary.update("")
            return

        summary.update(render.escape(info.summary))
        # IsEmpty and IsNotEmpty take no comparison value, so offering the box invites a value
        # that the policy would then carry meaninglessly.
        takes_value = info.value_kind != "none"
        value_input.display = takes_value
        if not takes_value:
            value_input.value = ""
        elif info.value_kind == "list":
            value_input.placeholder = 'A JSON list, e.g. ["a", "b"]'
        elif info.value_kind == "regex":
            value_input.placeholder = "A regular expression, e.g. ^prod-"
        else:
            value_input.placeholder = "Value to compare against, as JSON"

    # ---------------------------------------------------------------- checks

    def _collect_provider_args(self) -> dict:
        operation = schema.operation_for(self._provider_name, self._operation_name)
        if operation is None:
            return {}

        provider = schema.PROVIDERS[self._provider_name]
        args = {}
        if provider.uses_operation_type:
            args["operation_type"] = operation.name

        for arg in operation.args:
            try:
                widget = self.query_one(f"#arg-{arg.name}")
            except Exception:
                continue
            raw = widget.value
            # Select.NULL is the unselected sentinel; Select.BLANK is the literal False, so
            # testing against it here would let the sentinel through and serialise
            # "Select.NULL" into the policy as the argument's value.
            if raw is None or raw is Select.NULL or str(raw).strip() == "":
                continue
            # Provider args are JSON too: exclude_resource_types and infracost's resource_type
            # are lists, and typing one should not produce the string "[\"*\"]".
            args[arg.name] = parse_value(str(raw))
        return args

    def _add_check(self) -> None:
        check_id = self.query_one("#id-input", Input).value.strip()
        if not check_id:
            check_id = f"check{len(self._checks) + 1}"

        evaluator_name = str(self.query_one("#evaluator-select", Select).value)
        info = schema.EVALUATORS.get(evaluator_name)

        condition = {"type": evaluator_name}
        if info and info.value_kind != "none":
            condition["value"] = parse_value(self.query_one("#value-input", Input).value)

        self._checks.append(
            {
                "id": check_id,
                "provider_args": self._collect_provider_args(),
                "condition": condition,
            }
        )

        self.query_one("#id-input", Input).value = ""
        self.query_one("#value-input", Input).value = ""
        self._refresh_preview()

    def default_expression(self) -> str:
        """Every check must pass -- the commonest intent, and the one to start from."""
        return " && ".join(check["id"] for check in self._checks)

    def current_expression(self) -> str:
        """
        The expression to write into the policy.

        The field tracks the checks automatically until the user types something of their own,
        at which point it is left alone: an expression is the one part of a policy that cannot
        be derived from the checks, so silently rewriting `a && !b` back to `a && b` on the
        next Add check would discard the only thing the user could not express any other way.
        """
        if self._expression_is_custom:
            try:
                return self.query_one("#expression-input", Input).value.strip()
            except Exception:
                # Called before the field exists, during the first refresh in compose.
                return self.default_expression()
        return self.default_expression()

    def build_policy(self) -> dict:
        """The policy as currently assembled."""
        return {
            "meta": {"version": "v1", "required_provider": self._provider_name},
            "evaluators": list(self._checks),
            "eval_expression": self.current_expression(),
        }

    def _refresh_preview(self) -> None:
        # Keep the field showing the generated expression while it is still generated, so the
        # user can see what they are about to edit rather than an empty box. `with_expression`
        # suppresses the resulting Changed event, which would otherwise look like a user edit
        # and pin the expression the first time a check was added.
        if not self._expression_is_custom:
            field = self.query_one("#expression-input", Input)
            generated = self.default_expression()
            if field.value != generated:
                with self.prevent(Input.Changed):
                    field.value = generated

        policy = self.build_policy()
        self.query_one("#policy-json", Static).update(render.escape(json.dumps(policy, indent=2)))

        listing = self.query_one("#check-list", ListView)
        listing.clear()
        for check in self._checks:
            listing.append(ListItem(Label(render.escape(check["id"]))))

        findings = self.query_one("#builder-findings", Static)
        if not self._checks:
            findings.update("[dim]Add a check to build a policy.[/dim]")
            return

        problems = validate.check_policy(policy)
        if problems:
            findings.update("\n".join(render.finding_markup(f) for f in problems[:4]))
        else:
            findings.update("[green]✔ Valid policy[/green]")
