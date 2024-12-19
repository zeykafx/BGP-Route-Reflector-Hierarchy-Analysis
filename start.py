import argparse
import subprocess
import sys
import os
from pathlib import Path

verbose = False

def run_command(command, check=True):
    """Run a shell command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=not verbose, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

# Stop an existing lab
def stop_lab(lab_name):
    print(f"Stopping lab {lab_name}...")
    run_command(f"sudo clab destroy -t {lab_name}.clab.yml", check=False)

# Start a new lab deployment
def start_lab(lab_name, build_host_image=False):
    print(f"Starting lab {lab_name}...")
    
    # Build host image if it doesn't exist
    if build_host_image:
        print("Building host image...")
        run_command("sudo docker build -t host:latest -f Dockerfile.host .")
    
    # Deploy the lab
    run_command(f"sudo clab deploy -t {lab_name}.clab.yml")
    
    print(f"\nLab {lab_name} has been started successfully!")
    print("\nYou can access the routers using:")
    print(f"sudo docker exec -it clab-scenario-{lab_name}-<ROUTER-NAME> vtysh")
    print("\nTest connectivity using:")
    print("python3 full_mesh_connectivity_tests.py" if lab_name == "full_mesh" else "python3 rr_hierarchy_connectivity_test.py")
    print("\nCheck routes using:")
    print("show bgp ipv6 detail")
    print("show bgp ipv6 unicast")
    print("show ipv6 route")

def main():
    parser = argparse.ArgumentParser(description='Start a network lab scenario')
    parser.add_argument('lab', choices=['hierarchy', 'full_mesh'],
                      help='Lab scenario to start (hierarchy or full_mesh)')
    parser.add_argument('-s', '--stop-previous', action='store_true',
                      help='Stop any previous lab deployment before starting')
    parser.add_argument('-b', '--build-host-image', action='store_true', help="Build the host image")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
    parser.add_argument('-r', '--rebuild_rr_configs', action='store_true', help="Rebuild the RR configurations")
    
    args = parser.parse_args()

    # Check if docker and clab are installed
    if not (Path('/usr/bin/docker').exists() or Path('/usr/local/bin/docker').exists()):
        print("Error: docker is not installed")
        sys.exit(1)
    
    if not (Path('/usr/bin/clab').exists() or Path('/usr/local/bin/clab').exists()):
        print("Error: containerlab (clab) is not installed")
        sys.exit(1)

    global verbose
    verbose = args.verbose

    # Stop previous lab if requested
    if args.stop_previous:
        if args.lab == 'hierarchy':
            stop_lab('hierarchy')
        else:
            stop_lab('full_mesh')
            
    # Stop the current lab type if it exists
    stop_lab(args.lab)

    if args.rebuild_rr_configs and args.lab == 'hierarchy':
        print("Rebuilding Route Reflector configurations...")
        # Rebuild the configurations
        run_command("python3 generate_routers.py")
    
    # Start the requested lab
    start_lab(args.lab, args.build_host_image)

if __name__ == "__main__":
    main()
