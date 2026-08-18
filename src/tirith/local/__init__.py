"""
Local policy evaluation -- the credential-free path.

Everything here runs on the machine it is invoked from and talks to nothing. Policy files committed
in the repository are evaluated against a document, and the same report the platform path produces
is written out, so a caller's reporting is identical in both modes.

Two deliberate choices about *how* this reuses the rest of tirith, both about not owning a second
copy of anything:

  * Rendering, masking and document discovery are imported from `tirith.platform`
    (`report` / `redact` / `discover`). A second markdown renderer would drift from the platform
    path's, and the whole point is that both modes report identically. Those three modules live
    under `platform/` for historical reasons and are mode-agnostic; they are not moved here, because
    code outside this repository imports them by that path.
  * Evaluation shells out to `tirith -policy-path P -input-path I --json`, one policy at a time.
    That stdout document is tirith's frozen contract -- pinned byte-for-byte by
    tests/core/test_output_compatibility.py -- which makes it the most stable interface it has.
    Calling the engine's Python API instead would couple this to internals that carry no such
    promise. Now that this code lives inside the package, the temptation to do so is real; the
    argv is pinned by a test so that becomes a deliberate change rather than a silent one.

This began life in the GitHub Action, which needed to be usable before anyone had a StackGuardian
account. It moved here so a second front end (GitLab CI) drives one implementation rather than
forking it.
"""
