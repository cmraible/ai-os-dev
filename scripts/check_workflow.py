#!/usr/bin/env python3
"""
GitHub Actions Integration Script
Allows AI to check workflow status and results
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return None, result.stderr
        return result.stdout.strip(), None
    except Exception as e:
        return None, str(e)

def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated"""
    output, error = run_command("gh --version")
    if error:
        return False, "GitHub CLI (gh) not installed"
    
    output, error = run_command("gh auth status")
    if error:
        return False, "GitHub CLI not authenticated. Run: gh auth login"
    
    return True, "GitHub CLI ready"

def get_latest_run(owner="cmraible", repo="ai-os-dev"):
    """Get the latest workflow run"""
    cmd = f"gh run list --repo {owner}/{repo} --limit 1 --json databaseId,displayTitle,status,conclusion,createdAt"
    output, error = run_command(cmd)
    
    if error:
        return None, error
    
    try:
        runs = json.loads(output)
        if not runs:
            return None, "No workflow runs found"
        return runs[0], None
    except json.JSONDecodeError:
        return None, "Failed to parse workflow runs"

def download_artifacts(owner, repo, run_id, output_dir):
    """Download all artifacts from a run"""
    # Create temp directory
    temp_dir = Path(output_dir) / f"run_{run_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Download artifacts
    cmd = f"gh run download {run_id} --repo {owner}/{repo} --dir {temp_dir}"
    output, error = run_command(cmd)
    
    if error:
        return None, error
    
    return temp_dir, None

def analyze_artifacts(artifact_dir):
    """Analyze downloaded artifacts and generate report"""
    report = {
        "test_results": {},
        "serial_outputs": {},
        "summary": ""
    }
    
    # Find all artifact directories
    for artifact_path in artifact_dir.iterdir():
        if not artifact_path.is_dir():
            continue
            
        artifact_name = artifact_path.name
        
        # Look for serial outputs
        if "serial-output" in artifact_name:
            for txt_file in artifact_path.glob("*.txt"):
                with open(txt_file, "r", errors="replace") as f:
                    content = f.read()
                    report["serial_outputs"][txt_file.name] = content
        
        # Look for test results
        elif "test-results" in artifact_name:
            # Check for test report
            report_file = artifact_path / "test_report.md"
            if report_file.exists():
                with open(report_file, "r") as f:
                    report["summary"] = f.read()
            
            # Check for serial outputs in test results
            output_dir = artifact_path / "output"
            if output_dir.exists():
                for txt_file in output_dir.glob("serial_*.txt"):
                    with open(txt_file, "r", errors="replace") as f:
                        content = f.read()
                        report["serial_outputs"][txt_file.name] = content
    
    return report

def print_report(run_info, report):
    """Print analysis report in AI-friendly format"""
    print("=== GITHUB ACTIONS WORKFLOW ANALYSIS ===")
    print(f"\nRun: {run_info['displayTitle']}")
    print(f"Status: {run_info['status']}")
    print(f"Conclusion: {run_info['conclusion']}")
    print(f"Created: {run_info['createdAt']}")
    
    if report["summary"]:
        print("\n=== TEST SUMMARY ===")
        print(report["summary"])
    
    print("\n=== SERIAL OUTPUTS ===")
    
    # Sort outputs for consistent order
    for filename in sorted(report["serial_outputs"].keys()):
        content = report["serial_outputs"][filename]
        print(f"\n--- {filename} ---")
        print(content[:1000])  # First 1000 chars
        if len(content) > 1000:
            print("... (truncated)")
    
    # Look for specific test results
    print("\n=== KEY FINDINGS ===")
    
    # Check boot message
    boot_output = report["serial_outputs"].get("serial_boot.txt", "")
    if "AI-OS Boot v0.3" in boot_output:
        print("✓ Bootloader v0.3 booted successfully")
    else:
        print("✗ Bootloader boot issue")
    
    # Check CPU info
    cpu_output = report["serial_outputs"].get("serial_cpu.txt", "")
    if "CPU Information" in cpu_output:
        print("✓ CPU info command working")
        if "Vendor:" in cpu_output:
            # Extract vendor
            for line in cpu_output.split('\n'):
                if "Vendor:" in line:
                    print(f"  - {line.strip()}")
    else:
        print("✗ CPU info command issue")
    
    # Check tests
    test_output = report["serial_outputs"].get("serial_test.txt", "")
    if "All tests passed" in test_output:
        print("✓ All self-tests passed")
    else:
        print("✗ Self-tests failed")

def main():
    # Check prerequisites
    ok, message = check_gh_cli()
    if not ok:
        print(f"Error: {message}")
        return 1
    
    # Get latest run
    run_info, error = get_latest_run()
    if error:
        print(f"Error getting runs: {error}")
        return 1
    
    print(f"Found run: {run_info['displayTitle']} (ID: {run_info['databaseId']})")
    
    # Download artifacts
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact_dir, error = download_artifacts("cmraible", "ai-os-dev", run_info['databaseId'], temp_dir)
        if error:
            print(f"Error downloading artifacts: {error}")
            return 1
        
        # Analyze
        report = analyze_artifacts(artifact_dir)
        
        # Print report
        print_report(run_info, report)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
