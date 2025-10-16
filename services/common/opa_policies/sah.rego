package soma.sah.authz

# Default deny; explicit allow per rule.
default allow = false

allow {
  input.context.authenticated
  input.request.method == "GET"
  not forbidden_get_path
}

allow {
  input.context.roles[_] == "admin"
}

allow {
  input.context.client == "sa01"
  startswith(input.request.path, "/v1/sessions")
}

forbidden_get_path {
  startswith(input.request.path, "/healthz")
}

forbidden_get_path {
  startswith(input.request.path, "/metrics")
}
