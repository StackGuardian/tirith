"""
The three screens of the TUI.

Each is a container widget rather than a Screen, so the app can hold them in tabs and keep one
shared policy/input state across all of them -- building a policy in one tab and evaluating it
in another is the point.

Importing this package requires textual.
"""
