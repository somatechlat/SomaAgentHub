package somagent.capsule

# Simple policy that allows any authenticated user to write capsule results.
# In a real deployment this would check tenant ownership, roles, etc.
default allow_write_capsule_results = false

allow_write_capsule_results {
    # Expect the input to contain the required keys.
    input.user
    input.tenant
    input.capsule
    input.version
    # Unconditionally allow for the MVP.
    true
}
