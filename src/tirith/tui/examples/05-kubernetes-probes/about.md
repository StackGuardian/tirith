Kubernetes manifests, wildcard paths, and the `!` operator.

A third input shape: a **list** of manifests, not a single object. `kubernetes_kind` picks
which ones to look at, so the `Service` here is ignored and only the `Pod` is checked.

The `*` in `spec.containers.*.image` walks every container. This is the part worth
understanding, because it is where the engine surprises people: the wildcard collects the
containers into **one list**, and the condition is applied to that list rather than once
per container. So the question you ask has to be about the list.

That is why both checks are phrased as `Contains`:

- `has_liveness_probe` asks whether the list of probes contains `null` — a container with
  no probe contributes a `null`. Written as `IsNotEmpty` it would pass, because a list
  containing `null` is not empty.
- `uses_latest_tag` asks whether any image contains `:latest`. It is a *detector*, so the
  expression negates it with `!`.

Both fire on the same container: the `sidecar`, which has no probe and floats on `:latest`.

**Things to try**

- Give the sidecar a `livenessProbe` and pin its image to `acme/log-shipper:2.1.0`. The
  policy passes.
- Change `has_liveness_probe` to `IsNotEmpty` and watch it pass while the probe is still
  missing. This is the trap the check above avoids.
- Change `kubernetes_kind` to `Service` — no pod matches, so the checks report that the kind
  was found but the path was not, rather than passing silently.
