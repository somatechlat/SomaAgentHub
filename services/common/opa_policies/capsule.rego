package somagent.capsule

default allow_write_capsule_results = false

# Simple example policy:
# - user must be non-empty
# - tenant must be non-empty
# - allow if user has role "capsule.writer" or is the tenant owner

allow_write_capsule_results {
  input.user != ""
  input.tenant != ""
  some role
  role := input.roles[_]
  role == "capsule.writer"
}

allow_write_capsule_results {
  input.user != ""
  input.tenant != ""
  input.user == sprintf("%s-owner", [input.tenant])
}
