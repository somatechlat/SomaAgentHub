import re
from collections import defaultdict

def parse_requirements_file(file_path):
    dependencies = defaultdict(list)
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-e'):
                    continue

                # Handle lines with environment markers or other complex syntax
                if ';' in line:
                    line = line.split(';')[0].strip()

                match = re.match(r'([a-zA-Z0-9._-]+)([<>=!~]+.*)?', line)
                if match:
                    package_name = match.group(1).lower()
                    version_spec = match.group(2) if match.group(2) else ''
                    dependencies[package_name].append(version_spec)
    except FileNotFoundError:
        print(f"Warning: {file_path} not found, skipping.")
    return dependencies

all_dependencies = defaultdict(list)
requirements_files = [
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/testing-workbench/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/scripts/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/agent-spawner/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/token-estimator/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/memory-gateway/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/mao-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/policy-engine/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/notification-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/airflow-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/static-templates/fastapi/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/marketplace/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/model-proxy/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/pricing-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/flink-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/settings-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/analytics-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/llm-hub/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/tool-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/identity-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/task-capsule-repo/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/billing-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/constitution-service/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/jobs/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/gateway-api/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/services/orchestrator/requirements.txt',
    '/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/requirements-dev.txt'
]

for file_path in requirements_files:
    deps = parse_requirements_file(file_path)
    for package, specs in deps.items():
        all_dependencies[package].extend(specs)

# Prepare output for manual review
output_lines = []
for package, specs in sorted(all_dependencies.items()):
    unique_specs = sorted(list(set(specs)))
    output_lines.append(f"{package}: {', '.join(unique_specs)}")

# Write to a temporary file for review
temp_output_file = "/Users/macbookpro201916i964gb1tb/Documents/GitHub/somaAgentHub/consolidated_requirements_output.txt"
with open(temp_output_file, 'w') as f:
    f.write("\n".join(output_lines))

print(f"Consolidated dependencies written to: {temp_output_file}")
print("Please review this file to manually resolve conflicts and create a new master requirements.txt.")
