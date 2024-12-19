#! /usr/bin/python3

from datetime import datetime, timedelta
import json
import sys
import time
from scripts.full_mesh_connectivity_tests import test_connectivity as full_mesh_test
from scripts.rr_hierarchy_connectivity_test import test_connectivity as hierarchy_test

def main():
    # Read lab info from JSON file
    try:
        with open('lab_info.json', 'r') as f:
            lab_info = json.load(f)
    except FileNotFoundError:
        print("Error: lab_info.json not found. Please run start.py first")
        sys.exit(1)

    # Get lab name from info
    lab_name = lab_info.get('lab')
    if not lab_name:
        print("Error: Could not determine lab name")
        sys.exit(1)

    
    # Check if 30 seconds have passed since start time (Since ISIS convergence takes 30 seconds i think)
    start_time_timestamp = lab_info.get('timestamp')
    if not start_time_timestamp:
        print("Error: Could not determine start time")
        sys.exit(1)
    
    
    start_date = datetime.fromtimestamp(start_time_timestamp)
    current_date = datetime.now()
  
    if (current_date - start_date).seconds < 40:
        remaining = 40 - (current_date - start_date).seconds
        print(f"Waiting {remaining:.1f} seconds for ISIS to converge")
        for _ in range(int(remaining)):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)
        print("\nConvergence time complete")

    print(f"Running connectivity tests for lab: {lab_name}")

    # Run appropriate test script
    if lab_name == 'hierarchy':
        hierarchy_test()
    elif lab_name == 'full_mesh':
        full_mesh_test()
    

if __name__ == "__main__":
    main()
