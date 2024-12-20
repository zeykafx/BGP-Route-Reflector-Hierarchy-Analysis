#!/usr/bin/python3

import subprocess
import json
import time
import seaborn as sns
import pandas as pd
from pathlib import Path
from launch_tests import launch_test
from start import start_with_args
import matplotlib.pyplot as plt

def run_command(command):
    """Run a shell command and handle errors"""
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False
    return True

def start_lab_and_test(lab_name):
    """Start a lab and run its tests"""
    print(f"\nStarting {lab_name} lab...")
    
    start_with_args(lab_name, clean_only=False, stop_previous=True, verbose_arg=True, allow_multiple=False,rebuild_rr_configs=False)
    
    print(f"Running tests for {lab_name}...")
    res = launch_test(lab_name, "R10", should_exit=False)
    return res

def load_test_results(lab_name):
    """Load test results from json file"""
    try:
        with open(f"./scripts/out/{lab_name}_complete_test_results.json", 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Could not find test results for {lab_name}")
        return None

def create_convergence_graph():
    """Create and save a graph comparing convergence times"""
    better_hierarchy_results = load_test_results("better-hierarchy")
    full_mesh_results = load_test_results("full-mesh")
    
    if not better_hierarchy_results or not full_mesh_results:
        return False
        
    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6))

    data = pd.DataFrame([
        {"Topology": "Route Reflector Hierarchy", "Convergence Time (s)": better_hierarchy_results["convergence_time"]},
        {"Topology": "Full Mesh topology", "Convergence Time (s)": full_mesh_results["convergence_time"]}
    ])

    ax = sns.barplot(x="Topology", y="Convergence Time (s)", data=data, palette='Set2', hue="Topology")

    plt.title("BGP Convergence Time after Failure of R3 (Lower is Better)", pad=20)
    plt.ylabel("Convergence Time (seconds)")
    plt.xlabel('''Topology
            
    R3 has an eBGP session towards AS 65010 (and is is a second level RR in the RR Hierarchy).
    This test makes R3 fail then waits until BGP chooses the path through R9 (also has an eBGP session towards AS 65010)''')

    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f sec', label_type='center')

    plt.tight_layout()
    plt.savefig('convergence_comparison.png')
    print("\nGraph saved as 'convergence_comparison.png'")

    sns.set_style("whitegrid")
    plt.figure(figsize=(10, 6))

    data = pd.DataFrame([
        {"Topology": "Route Reflector Hierarchy", "Average Number of Unique Paths": better_hierarchy_results["average_paths"]},
        {"Topology": "Full Mesh topology", "Average Number of Unique Paths": full_mesh_results["average_paths"]}
    ])

    ax = sns.barplot(x="Topology", y="Average Number of Unique Paths", data=data, palette='Set2', hue="Topology")

    plt.title("Average Number of Unique Paths Comparison (Higher is better)", pad=20)
    plt.ylabel("Average Number of Unique Paths")

    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', label_type='center')

    plt.tight_layout()
    plt.savefig('unique_paths_comparison.png')
    print("\nGraph saved as 'unique_paths_comparison.png'")
    return True

def main():
    # ensure we're starting fresh
    start_with_args("better-hierarchy", clean_only=True, stop_previous=True, verbose_arg=True, rebuild_rr_configs=False, allow_multiple=False)
    
    # run both labs sequentially
    labs = ["better-hierarchy", "full-mesh"]
    for lab in labs:
        if not start_lab_and_test(lab):
            print(f"Failed to complete tests for {lab}")
            return
            
    if not create_convergence_graph():
        print("Failed to create comparison graph")
        return
        
    print("\nAll done! Check convergence_comparison.png and unique_paths_comparison for the results")

if __name__ == "__main__":
    main()
