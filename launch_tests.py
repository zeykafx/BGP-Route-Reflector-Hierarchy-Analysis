#! /usr/bin/python3

from datetime import datetime, timedelta
import json
import sys
import subprocess
import time
import argparse
from scripts.full_mesh_connectivity_tests import test_connectivity as full_mesh_test
from scripts.rr_hierarchy_connectivity_test import test_connectivity as hierarchy_test
from scripts.diversity_test import analyze_bgp_paths

def is_lab_running(lab_name):
    # Check if the lab is running by trying to access a router
    router = "R1"
    full_command = f"sudo docker exec -it clab-scenario-{lab_name}-{router} vtysh -c 'show bgp ipv6 unicast'"
    result = subprocess.run(full_command, shell=True, check=False, capture_output=True, text=True)
    if "No such container" in result.stderr:
        return False
    return True

def get_running_lab():
    if is_lab_running("better-hierarchy"):
        return "better-hierarchy"
    elif is_lab_running("full-mesh"):
        return "full-mesh"
    return None

def main():
    parser = argparse.ArgumentParser(description='Run connectivity tests on lab topology')
    parser.add_argument('-l', '--lab', choices=['better-hierarchy', 'full-mesh'], help='Specify the lab to test')
    parser.add_argument('-r', '--router', help='Specify the router from which to analyze BGP paths', default='R10')
    args = parser.parse_args()

    lab_name = args.lab if args.lab else get_running_lab()
    if not lab_name:
        print("Error: No lab is running and no lab was specified")
        sys.exit(1)

    # Read lab info from JSON file
    try:
        with open(f'./scripts/lab_info_{lab_name}.json', 'r') as f:
            lab_info = json.load(f)
    except FileNotFoundError:
        print("Error: lab_info.json not found. Please run start.py first")
        sys.exit(1)

    # Get lab start time from info
    start_time_timestamp = lab_info.get('timestamp')
    if not start_time_timestamp:
        print("Error: Could not determine start time")
        sys.exit(1)
    
    start_date = datetime.fromtimestamp(start_time_timestamp)
    current_date = datetime.now()
  
    if (current_date - start_date).seconds < 50:
        remaining = 50 - (current_date - start_date).seconds
        print(f"Waiting for IGP to converge (Otherwise nothing is reachable)")
        for i in range(int(remaining)):
            sys.stdout.write(f'\rTime remaining: {remaining-i} seconds')
            sys.stdout.flush()
            time.sleep(1)
        print("\nConvergence time complete")

    print(f"Running connectivity tests for lab: {lab_name}")

    BOLD_YELLOW = '\033[1;33m'
    RESET = '\033[0m'
    
    router_name = args.router

    # Run appropriate test script
    if lab_name == 'better-hierarchy':
        full_mesh_test('better-hierarchy')
        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        analyze_bgp_paths(lab_name='better-hierarchy', router_name=router_name)
    elif lab_name == 'full-mesh':
        full_mesh_test("full-mesh")
        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        analyze_bgp_paths(lab_name='full-mesh', router_name=router_name)

if __name__ == "__main__":
    main()
