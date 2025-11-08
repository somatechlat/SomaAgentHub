"""
This script simulates the initial phase of the "Accounting Software for Ecuador" use case.
It demonstrates:
1. Capturing the initial user request.
2. Running a simulated wizard to gather requirements.
3. Generating a structured ProjectPlan JSON file.

This output file can then be used as the input for the Multi-Agent Orchestrator.
"""

import json
import logging
import os
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_wizard():
    """Simulates an interactive wizard to gather project requirements."""
    logging.info("🤖 Agent: I can help with that. To build the right accounting software, I need a bit more information.")
    
    requirements = {}
    
    # Question 1: Business Size
    business_size = input("🤖 Agent: Is this for personal use, a small business, or a large enterprise? ")
    requirements["business_size"] = business_size.lower()
    
    # Question 2: Ecuadorian Compliance
    logging.info("🤖 Agent: Understood. For a business in Ecuador, compliance with the SRI is crucial.")
    sri_compliance = input("🤖 Agent: Do you require 'facturación electrónica' (electronic invoicing) integration? (yes/no) ")
    requirements["sri_compliance"] = sri_compliance.lower() == "yes"
    
    # Question 3: Payroll
    payroll = input("🤖 Agent: Do you need payroll processing? (yes/no) ")
    requirements["payroll"] = payroll.lower() == "yes"
    
    # Question 4: Hosting
    hosting = input("🤖 Agent: Should this be a cloud-hosted web application or a desktop application? (cloud/desktop) ")
    requirements["hosting"] = hosting.lower()
    
    logging.info("🤖 Agent: Thank you. I have all the information I need to generate a project plan.")
    
    return requirements

def generate_project_plan(requirements):
    """Generates a project plan based on the collected requirements."""
    
    plan = {
        "projectName": "Ecuadorian Accounting Software for SMBs",
        "requestDate": datetime.now(timezone.utc).isoformat(),
        "approved": False,
        "modules": [
            # Infrastructure is always needed for cloud projects
            {
                "id": "Module-Infra",
                "capsule": "ProvisionAWSEKS",
                "dependencies": [],
                "description": "Provision a secure EKS cluster on AWS."
            },
            {
                "id": "Module-Database",
                "capsule": "SetupPostgresRDS",
                "dependencies": ["Module-Infra"],
                "description": "Set up a managed PostgreSQL database on RDS."
            },
            # Backend and Frontend are standard for web apps
            {
                "id": "Module-Backend",
                "capsule": "ScaffoldFastAPIApp",
                "dependencies": ["Module-Database"],
                "description": "Create the backend API using FastAPI."
            },
            {
                "id": "Module-Frontend",
                "capsule": "BuildReactFrontend",
                "dependencies": ["Module-Backend"],
                "description": "Build the user interface with React."
            }
        ]
    }
    
    # Conditionally add modules based on requirements
    if requirements.get("sri_compliance"):
        plan["modules"].append({
            "id": "Module-SRI",
            "capsule": "IntegrateSRI-API",
            "dependencies": ["Module-Backend"],
            "description": "Integrate with the Ecuadorian SRI for electronic invoicing."
        })
        
    if requirements.get("payroll"):
        plan["modules"].append({
            "id": "Module-Payroll",
            "capsule": "BuildPayrollModule",
            "dependencies": ["Module-Backend", "Module-Frontend"],
            "description": "Implement payroll calculation and processing features."
        })
        
    return plan

def main():
    """Main function to run the simulation."""
    
    logging.info("--- Initiating Complex Use Case: Accounting Software for Ecuador ---")
    
    # 1. Simulate user request
    user_request = "I need accounting software for my business in Ecuador."
    logging.info(f"👤 User: {user_request}")
    
    # 2. Run the wizard
    requirements = run_wizard()
    
    # 3. Generate the project plan
    project_plan = generate_project_plan(requirements)
    
    # 4. Present the plan for approval
    logging.info("\n🤖 Agent: Based on your requirements, I've drafted the following project plan:")
    logging.info(json.dumps(project_plan, indent=2))
    
    approval = input("\n🤖 Agent: Do you approve this plan? (yes/no) ")
    
    if approval.lower() == "yes":
        project_plan["approved"] = True
        logging.info("🤖 Agent: Great! The plan is approved and will now be sent to the Multi-Agent Orchestrator for execution.")
        
        # 5. Save the plan to a file
        output_filename = "project_plan_accounting_ecuador.json"
        output_path = os.path.join(os.path.dirname(__file__), output_filename)
        
        with open(output_path, "w") as f:
            json.dump(project_plan, f, indent=2)
            
        logging.info(f"✅ Project plan saved to '{output_path}'")
        logging.info("--- Simulation Complete ---")
    else:
        logging.info("🤖 Agent: Plan not approved. Please restart the process to make changes.")
        logging.info("--- Simulation Canceled ---")

if __name__ == "__main__":
    main()
