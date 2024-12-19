#! /usr/bin/python3
import json
import sys
import subprocess

def connect_to_router(router_name):
    # Read lab info from JSON file
    try:
        with open('lab_info.json', 'r') as f:
            lab_info = json.load(f)
    except FileNotFoundError:
        print("Error: lab_info.json not found, please run start.py first")
        sys.exit(1)

    # Get lab name from info
    lab_name = lab_info.get('lab')
    if not lab_name:
        print("Error: Could not determine lab name")
        sys.exit(1)
        
    # Build container name
    container = f"clab-scenario-{lab_name}-{router_name}"

    # Connect to router's vtysh
    try:
        subprocess.run(['sudo', 'docker', 'exec', '-it', container, 'vtysh'], check=True)
    except subprocess.CalledProcessError:
        print(f"Error: Could not connect to router {router_name}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./connect.py ROUTER_NAME")
        sys.exit(1)
        
    connect_to_router(sys.argv[1])
