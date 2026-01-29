#!/usr/bin/env python3
"""
Verification script for strands-cli init behavior.
This script creates a test project and checks which files are generated.
"""

import os
import shutil
import subprocess
import sys
import tempfile

def main():
    """Main function."""
    print("Verifying strands-cli init behavior...")

    # Create a temporary directory for the test
    test_dir = tempfile.mkdtemp()
    project_name = "test-project"

    try:
        # Run the strands-cli init command
        print(f"Creating project {project_name} in {test_dir}...")
        cmd = f"strands-cli init {project_name} --output-dir {test_dir}"
        subprocess.run(cmd, shell=True, check=True)

        project_dir = os.path.join(test_dir, project_name)

        # Check if the project directory was created
        if not os.path.exists(project_dir):
            print("ERROR: Project directory was not created.")
            return 1

        # Check the directory structure
        print("\nVerifying directory structure:")

        helm_chart_dir = os.path.join(project_dir, "deployment/helm")
        helm_templates_dir = os.path.join(helm_chart_dir, "templates")
        k8s_dir = os.path.join(project_dir, "deployment/k8s")

        # Check if the directories exist
        print(f"- Helm chart directory: {os.path.exists(helm_chart_dir)}")
        print(f"- Helm templates directory: {os.path.exists(helm_templates_dir)}")
        print(f"- K8s manifests directory: {os.path.exists(k8s_dir)}")

        # List files in the Helm templates directory
        if os.path.exists(helm_templates_dir):
            print("\nHelm template files:")
            for file in os.listdir(helm_templates_dir):
                print(f"  - {file}")

        # List files in the K8s directory
        if os.path.exists(k8s_dir):
            print("\nK8s manifest files:")
            k8s_files = os.listdir(k8s_dir)
            if k8s_files:
                for file in k8s_files:
                    print(f"  - {file}")
            else:
                print("  No K8s manifest files found (expected)")

        # Check the values.yaml file
        values_file = os.path.join(helm_chart_dir, "values.yaml")
        values_dev_file = os.path.join(helm_chart_dir, "values-dev.yaml")
        values_prod_file = os.path.join(helm_chart_dir, "values-prod.yaml")
        values_md_file = os.path.join(helm_chart_dir, "VALUES.md")

        print("\nValues files:")
        print(f"- values.yaml: {os.path.exists(values_file)}")
        print(f"- values-dev.yaml: {os.path.exists(values_dev_file)}")
        print(f"- values-prod.yaml: {os.path.exists(values_prod_file)}")
        print(f"- VALUES.md: {os.path.exists(values_md_file)}")

        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

    finally:
        # Clean up
        print(f"\nCleaning up test directory: {test_dir}")
        shutil.rmtree(test_dir)

if __name__ == "__main__":
    sys.exit(main())