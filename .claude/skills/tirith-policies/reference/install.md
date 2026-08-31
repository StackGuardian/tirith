# Install Tirith

## Tirith is not on PyPI

`pip install tirith` installs an **unrelated project of the same name**, and `pip install
py-tirith` finds nothing. Always install from git.

```bash
pip install git+https://github.com/StackGuardian/tirith.git
```

Pin a tag rather than tracking the default branch, so a CI job cannot change behaviour underneath
you:

```bash
pip install "git+https://github.com/StackGuardian/tirith.git@1.0.5"
```

`git ls-remote --tags https://github.com/StackGuardian/tirith.git` lists the available tags.

## Verify

```bash
tirith --version
```

## Python versions

| | Needs |
| --- | --- |
| Tirith itself | Python 3.8 or newer |
| The `[tui]` extra (`tirith ui`) | Python 3.9 or newer |

## The optional interface

`tirith ui` is an interactive terminal interface — explore a failing evaluation down to the
resource, assemble a policy from a form, or experiment in a playground. It is an extra rather than
a dependency, because using Tirith as a CI gate should not pay for an interface it never opens.

```bash
pip install 'py-tirith[tui] @ git+https://github.com/StackGuardian/tirith.git'
tirith ui
```

The extra is requested against the git URL for the same reason as above. On Python 3.8 the extra
installs and simply provides nothing.

## Developing against a checkout

```bash
git clone https://github.com/StackGuardian/tirith.git
cd tirith
python -m venv .venv && source .venv/bin/activate
pip install -e .
```
