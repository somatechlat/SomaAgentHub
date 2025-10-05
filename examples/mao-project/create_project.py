"""
⚠️ WE DO NOT MOCK - Real example of creating a multi-agent project.

This example demonstrates:
1. Creating a project with multiple tasks
2. Task dependencies (DAG execution)
3. Different personas for different tasks
4. Real-time monitoring
"""

import asyncio
import requests
import json

# MAO service API
MAO_API = "http://localhost:8007/v1"


async def create_example_project():
    """Create an example multi-agent project."""
    
    project_config = {
        "project_name": "Build Sample Web App",
        "execution_mode": "dag",
        "git_repo_url": "https://github.com/somagent/starter-template.git",
        "artifact_storage": "s3://somagent-artifacts",
        "max_parallel_tasks": 3,
        "tasks": [
            {
                "task_id": "task-1-setup",
                "capsule_id": "project-scaffolder",
                "persona_id": "architect-persona",
                "description": "Create project structure and package.json",
                "dependencies": [],
                "timeout_seconds": 600,
            },
            {
                "task_id": "task-2-backend",
                "capsule_id": "fastapi-builder",
                "persona_id": "backend-developer-persona",
                "description": "Build FastAPI backend with CRUD endpoints",
                "dependencies": ["task-1-setup"],
                "timeout_seconds": 1800,
            },
            {
                "task_id": "task-3-frontend",
                "capsule_id": "react-builder",
                "persona_id": "frontend-developer-persona",
                "description": "Build React frontend with Tailwind CSS",
                "dependencies": ["task-1-setup"],
                "timeout_seconds": 1800,
            },
            {
                "task_id": "task-4-tests",
                "capsule_id": "test-writer",
                "persona_id": "qa-engineer-persona",
                "description": "Write unit and integration tests",
                "dependencies": ["task-2-backend", "task-3-frontend"],
                "timeout_seconds": 1200,
            },
            {
                "task_id": "task-5-docs",
                "capsule_id": "doc-writer",
                "persona_id": "technical-writer-persona",
                "description": "Generate API documentation and README",
                "dependencies": ["task-2-backend", "task-3-frontend"],
                "timeout_seconds": 900,
            },
            {
                "task_id": "task-6-deploy",
                "capsule_id": "deployer",
                "persona_id": "devops-engineer-persona",
                "description": "Create Docker containers and deploy to staging",
                "dependencies": ["task-4-tests", "task-5-docs"],
                "timeout_seconds": 1200,
            },
        ],
    }
    
    print("🚀 Creating multi-agent project...")
    print(f"   Project: {project_config['project_name']}")
    print(f"   Tasks: {len(project_config['tasks'])}")
    print(f"   Execution Mode: {project_config['execution_mode']}")
    print()
    
    # Create project
    response = requests.post(
        f"{MAO_API}/projects",
        json=project_config,
        headers={"Content-Type": "application/json"},
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to create project: {response.text}")
        return
    
    project = response.json()
    project_id = project["project_id"]
    
    print(f"✅ Project created!")
    print(f"   Project ID: {project_id}")
    print(f"   Workflow ID: {project['workflow_id']}")
    print()
    
    # Monitor progress
    print("📊 Monitoring progress...")
    print("   (Press Ctrl+C to stop monitoring)")
    print()
    
    try:
        while True:
            # Get status
            status_response = requests.get(f"{MAO_API}/projects/{project_id}")
            
            if status_response.status_code == 200:
                status = status_response.json()
                
                print(f"\r   Status: {status['current_status']} | " +
                      f"Completed: {status['completed_tasks']}/{status['total_tasks']} | " +
                      f"Workspace: {status['workspace_id'] or 'N/A'}", end="")
                
                # Check if completed
                if status['current_status'] in ['completed', 'failed', 'cancelled']:
                    print()
                    print()
                    print(f"🎉 Project {status['current_status']}!")
                    
                    # Get final result
                    result_response = requests.get(
                        f"{MAO_API}/projects/{project_id}/result",
                        timeout=5,
                    )
                    
                    if result_response.status_code == 200:
                        result = result_response.json()
                        print()
                        print("📋 Final Results:")
                        print(json.dumps(result, indent=2))
                    
                    break
            
            await asyncio.sleep(3)
            
    except KeyboardInterrupt:
        print()
        print()
        print("⏸️  Monitoring stopped (project still running)")
        print(f"   View status: {MAO_API}/projects/{project_id}")
        print(f"   Cancel project: POST {MAO_API}/projects/{project_id}/cancel")


if __name__ == "__main__":
    asyncio.run(create_example_project())
