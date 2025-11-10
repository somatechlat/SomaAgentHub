package soma.budget

# Defaults
default decision := {
  "allow_pricing": false,
  "within_budget": false,
  "not_stale": false,
  "within_quota": false,
  "drift_ok": true,
}

# Helper defaults
max_age_min := input.max_price_age_min
default max_age_min := 30

max_drift_ratio := input.max_drift_ratio
default max_drift_ratio := 0.2

# Guards
within_budget {
  input.estimated_total <= input.budget_cap
}

not_stale {
  # If last_quote_age_min not provided, consider it fresh (0)
  age := input.last_quote_age_min
  not is_invalid_age(age)
  age <= max_age_min
}

is_invalid_age(x) {
  x == null
}

within_quota {
  input.quota_used <= input.quota_limit
}

drift_ok {
  # If no drift_ratio provided, treat as OK (precheck phase)
  not input.drift_ratio
}

drift_ok {
  input.drift_ratio <= max_drift_ratio
}

# Final decision object
decision := {
  "allow_pricing": allow_pricing,
  "within_budget": within_budget,
  "not_stale": not_stale,
  "within_quota": within_quota,
  "drift_ok": drift_ok,
}

allow_pricing {
  within_budget
  not_stale
  within_quota
  drift_ok
}
