#! /usr/bin/python3
import json
import sys
import subprocess
import argparse

def is_lab_running(lab_name):
    # Check if the lab is running by trying to access a router
    router = "RR1T" if lab_name == "hierarchy" else "R1"
    full_command = f"sudo docker exec -it clab-scenario-{lab_name}-{router} vtysh -c 'show bgp ipv6 unicast'"
    result = subprocess.run(full_command, shell=True, check=False, capture_output=True, text=True)
    if "No such container" in result.stderr:
        return False
    return True

def get_running_lab():
    lab = None
    if is_lab_running("hierarchy"):
        lab = "hierarchy"

    if is_lab_running("full-mesh"):
        lab = "full-mesh"
        if lab is not None:
            print("Warning: Both labs are running. This is not recommended.")
    return lab

def connect_to_router(router_name, lab_name=None):
    if lab_name is None:
        lab_name = get_running_lab()
        if lab_name is None:
            print("Error: No lab is running")
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
    parser = argparse.ArgumentParser(description='Connect to a router in a lab environment')
    parser.add_argument('router', help='Name of the router to connect to')
    parser.add_argument('-l', '--lab', choices=['hierarchy', 'full-mesh'], help='Lab environment (optional)')
    
    args = parser.parse_args()
    connect_to_router(args.router, args.lab)
