#!/usr/bin/env python3
"""
Script to download and analyze GitHub Actions artifacts
This allows the AI to inspect test results from workflow runs
"""

import os
import sys
import json
import zipfile
import requests
from pathlib import Path
import argparse

def get_workflow_runs(token, owner, repo, branch="main"):
    """Get recent workflow runs"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs"
    params = {"branch": branch, "per_page": 5}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    return response.json()["workflow_runs"]

def get_run_artifacts(token, owner, repo, run_id):
    """Get artifacts for a specific run"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts"
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    return response.json()["artifacts"]

def download_artifact(token, owner, repo, artifact_id, output_dir):
    """Download a specific artifact"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get download URL
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/{artifact_id}/zip"
    
    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    
    # Save zip file
    zip_path = output_dir / f"artifact_{artifact_id}.zip"
    with open(zip_path, "wb") as f:
        f.write(response.content)
    
    # Extract
    extract_dir = output_dir / f"artifact_{artifact_id}"
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Remove zip
    zip_path.unlink()
    
    return extract_dir

def analyze_test_results(artifact_dir):
    """Analyze the downloaded test results"""
    results = {
        "serial_outputs": {},
        "test_summary": None,
        "qemu_log": None
    }
    
    # Look for serial output files
    serial_dir = artifact_dir / "output"
    if serial_dir.exists():
        for serial_file in serial_dir.glob("serial_*.txt"):
            with open(serial_file, "r", errors="replace") as f:
                results["serial_outputs"][serial_file.name] = f.read()
    
    # Look for test report
    report_file = artifact_dir / "test_report.md"
    if report_file.exists():
        with open(report_file, "r") as f:
            results["test_summary"] = f.read()
    
    # Look for QEMU log
    qemu_log = artifact_dir / "output" / "qemu_debug.log"
    if qemu_log.exists():
        with open(qemu_log, "r", errors="replace") as f:
            # Just last 100 lines
            lines = f.readlines()
            results["qemu_log"] = "".join(lines[-100:])
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Download and analyze GitHub Actions artifacts")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument("--owner", default="cmraible", help="Repository owner")
    parser.add_argument("--repo", default="ai-os-dev", help="Repository name")
    parser.add_argument("--run-id", help="Specific run ID (optional)")
    parser.add_argument("--output", default="artifacts", help="Output directory")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    try:
        if args.run_id:
            run_id = args.run_id
        else:
            # Get latest run
            runs = get_workflow_runs(args.token, args.owner, args.repo)
            if not runs:
                print("No workflow runs found")
                return
            
            run_id = runs[0]["id"]
            print(f"Using latest run: {runs[0]['display_title']} (ID: {run_id})")
            print(f"Status: {runs[0]['status']}, Conclusion: {runs[0]['conclusion']}")
        
        # Get artifacts
        artifacts = get_run_artifacts(args.token, args.owner, args.repo, run_id)
        
        if not artifacts:
            print("No artifacts found for this run")
            return
        
        print(f"\nFound {len(artifacts)} artifacts:")
        for artifact in artifacts:
            print(f"  - {artifact['name']} ({artifact['size_in_bytes']} bytes)")
        
        # Download and analyze each artifact
        all_results = {}
        for artifact in artifacts:
            print(f"\nDownloading {artifact['name']}...")
            artifact_dir = download_artifact(
                args.token, args.owner, args.repo, 
                artifact['id'], output_dir
            )
            
            print(f"Analyzing {artifact['name']}...")
            results = analyze_test_results(artifact_dir)
            all_results[artifact['name']] = results
        
        # Generate summary report
        print("\n=== ANALYSIS RESULTS ===\n")
        
        for artifact_name, results in all_results.items():
            print(f"## {artifact_name}\n")
            
            if results["test_summary"]:
                print("### Test Summary")
                print(results["test_summary"])
            
            if results["serial_outputs"]:
                print("\n### Serial Outputs")
                for filename, content in results["serial_outputs"].items():
                    print(f"\n#### {filename}")
                    print("```")
                    print(content[:500])  # First 500 chars
                    if len(content) > 500:
                        print("...")
                    print("```")
            
            if results["qemu_log"]:
                print("\n### QEMU Log (last 100 lines)")
                print("```")
                print(results["qemu_log"])
                print("```")
        
        # Save full results as JSON
        results_file = output_dir / "analysis_results.json"
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\nFull results saved to: {results_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
