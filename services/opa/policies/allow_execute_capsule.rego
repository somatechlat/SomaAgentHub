package somagent.capsule

# Simple allow‑execute policy – permits any user to run any capsule.
# In production this would be replaced with proper tenant‑based checks.
default allow_execute_capsule = false

allow_execute_capsule {
    # The input is expected to contain the keys used in the request.
    input.user
    input.tenant
    input.capsule
    input.version
    # Unconditionally allow for the MVP.
    true
}
