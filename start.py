#! /usr/bin/python3
import argparse
import subprocess
import sys
import os
from pathlib import Path
import json
from datetime import datetime
from scripts.generate_routers import generate_routers

verbose = False

def run_command(command, check=True, override_verbose=False):
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=(not verbose or override_verbose), text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def stop_lab(lab_name):
    print(f"Stopping lab {lab_name}...")
    run_command(f"sudo containerlab destroy -t {lab_name}.clab.yml", check=False)
    remove_info_file(lab_name)

# Start a new lab deployment
def start_lab(lab_name):
    print(f"Starting lab {lab_name}...")
    
    run_command(f"sudo containerlab deploy -t {lab_name}.clab.yml")
    
    print(f"\nLab {lab_name} has been started successfully!")
    print("\nYou can access the routers using:")
    print(f"./connect.py RR1T" if lab_name == "better-hierarchy" else "./connect.py R1")
    print("\nTest connectivity and path diversity using:")
    print("./launch_tests.py")
    print("\nCheck routes when connected to a router using:")
    print("show bgp ipv6 detail")
    print("show bgp ipv6 unicast")
    print("show ipv6 route")

def write_info_file(lab_name):
    # write info about the lab to a json file
    info = {
        'lab': lab_name,
        'timestamp': datetime.now().timestamp(),
    }

    with open(f'./scripts/out/lab_info_{lab_name}.json', 'w') as f:
        json.dump(info, f, indent=2)


def remove_info_file(lab_name):
    try:
        os.remove(f'./scripts/out/lab_info_{lab_name}.json')
    except FileNotFoundError:
        pass

def check_host_image():
    result = run_command("sudo docker image inspect host:latest", check=False, override_verbose=True)
    if result.returncode != 0:
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Start a network lab scenario', allow_abbrev=True)
    parser.add_argument('lab', choices=['better-hierarchy', 'full-mesh'],
                      help='Lab scenario to start (better-hierarchy or full-mesh)')
    parser.add_argument('-c', '--clean-only', action='store_true', help='Clean up previous lab deployments and exit', default=False)
    parser.add_argument('-s', '--stop-previous', action='store_true',
                      help='Stop any previous lab deployment before starting', default=True)
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output", default=False)
    # parser.add_argument('-r', '--rebuild_rr_configs', action='store_true', help="Rebuild the RR configurations", default=False)
    parser.add_argument('-a', '--allow-multiple', action='store_true', help="Allow multiple containers to run at the same time (NOT RECOMMENDED)", default=False)

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help']) # parse the arguments or show help message if no arguments are provided

    start_with_args(args.lab, args.clean_only, args.stop_previous, args.verbose, False, args.allow_multiple)


def start_with_args(lab_name, clean_only, stop_previous, verbose_arg, rebuild_rr_configs, allow_multiple):
    # check if docker and clab are installed
    if not (Path('/usr/bin/docker').exists() or Path('/usr/local/bin/docker').exists()):
        print("Error: docker is not installed")
        sys.exit(1)
    
    if not (Path('/usr/bin/clab').exists() or Path('/usr/local/bin/clab').exists() or Path('/usr/bin/containerlab').exists() or Path('/usr/local/bin/containerlab').exists()):
        print("Error: containerlab (clab) is not installed")
        sys.exit(1)

    global verbose
    verbose = verbose_arg

    host_image_exists = check_host_image()
    if not host_image_exists:
        # build host image if it doesn't exist
        print("Building host image because it doesn't exist")
        run_command("sudo docker build -t host:latest -f Dockerfile.host .")

    if clean_only:
        print("Cleaning up previous lab deployments... (and not starting a new lab)")
        stop_lab('better-hierarchy')
        stop_lab('full-mesh')
        return

    if not allow_multiple:
        if lab_name == 'better-hierarchy':
            stop_lab('full-mesh')
        elif lab_name  == 'full-mesh':
            stop_lab('better-hierarchy')

    # stop previous lab if requested
    if stop_previous:
        if lab_name == 'better-hierarchy':
            stop_lab('better-hierarchy')
        elif lab_name == 'full-mesh':
            stop_lab('full-mesh')


    start_lab(lab_name)

    write_info_file(lab_name)

if __name__ == "__main__":
    main()
