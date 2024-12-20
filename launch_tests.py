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
from scripts.convergence_test import main as convergence_test
from scripts.bgp_convergence_time import check_connectivity

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

def write_complete_test_results(lab_name, avg_paths, convergence_detected, convergence_time, router_name):
    results = {
        'lab_name': lab_name,
        'timestamp': datetime.now().timestamp(),
        'average_paths': avg_paths,
        'convergence_detected': convergence_detected,
        'convergence_time': convergence_time,
        'router_name': router_name
    }
    with open(f"./scripts/out/{lab_name}_complete_test_results.json", "w") as f:
        json.dump(results, f, indent=4)

def main():
    parser = argparse.ArgumentParser(description='Run connectivity tests on lab topology')
    parser.add_argument('-l', '--lab', choices=['better-hierarchy', 'full-mesh'], help='Specify the lab to test')
    parser.add_argument('-r', '--router', help='Specify the router from which to analyze BGP paths', default='R10')
    args = parser.parse_args()
    launch_test(args.lab, args.router)

def launch_test(lab, router_name, should_exit=True):

    lab_name = lab if lab else get_running_lab()
    if not lab_name:
        print("Error: No lab is running and no lab was specified")
        if should_exit:
            sys.exit(1)
        else:
            return False

    # read info from JSON file
    try:
        with open(f'./scripts/out/lab_info_{lab_name}.json', 'r') as f:
            lab_info = json.load(f)
    except FileNotFoundError:
        print("Error: lab_info.json not found. Please run start.py first")
        if should_exit:
            sys.exit(1)
        else:
            return False

    # get start time from info
    start_time_timestamp = lab_info.get('timestamp')
    if not start_time_timestamp:
        print("Error: Could not determine start time")
        if should_exit:
            sys.exit(1)
        else:
            return False
    
    start_date = datetime.fromtimestamp(start_time_timestamp)
    current_date = datetime.now()
    
    # wait for BGP to converge (i.e., wait for R7 to be able to reach both external hosts)
    success, time = check_connectivity(lab_name, router_name="R7")
    if not success:
        print("Error: BGP has not converged, or at least R7 cannot reach both external hosts.")
        if should_exit:
            sys.exit(1)
        else:
            return False
        

    print(f"Running connectivity tests for lab: {lab_name}")

    BOLD_YELLOW = '\033[1;33m'
    RESET = '\033[0m'


    if lab_name == 'better-hierarchy':
        has_failed_tests= full_mesh_test('better-hierarchy')
        if has_failed_tests:
            print(f"{BOLD_YELLOW}Some tests failed, skipping the rest of the tests!...{RESET}")
            if should_exit:
                sys.exit(1)
            else:
                return False

        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        avg_paths = analyze_bgp_paths(lab_name='better-hierarchy', router_name=router_name)
        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        convergence_detected, convergence_time = convergence_test("better-hierarchy", router_name, "R3", "fc00:2142:a:2::/64")
        write_complete_test_results("better-hierarchy", avg_paths, convergence_detected, convergence_time, router_name)

    elif lab_name == 'full-mesh':
        has_failed_tests = full_mesh_test("full-mesh")
        if has_failed_tests:
            print(f"{BOLD_YELLOW}Some tests failed, skipping the rest of the tests!...{RESET}")
            if should_exit:
                sys.exit(1)
            else:
                return False
            
        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        avg_paths = analyze_bgp_paths(lab_name='full-mesh', router_name=router_name)
        print(f"{BOLD_YELLOW}-{RESET}" * 100)
        convergence_detected, convergence_time = convergence_test("full-mesh", router_name, "R3", "fc00:2142:a:2::/64")
        write_complete_test_results("full-mesh", avg_paths, convergence_detected, convergence_time, router_name)

    return True


if __name__ == "__main__":
    main()
