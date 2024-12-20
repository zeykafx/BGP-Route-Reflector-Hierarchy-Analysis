import subprocess
import json
import time
from datetime import datetime

def run_docker_command(command, lab_name, router_name):
    """Run a command on a router using docker exec"""
    full_command = f"sudo docker exec clab-scenario-{lab_name}-{router_name} {command}"
    try:
        result = subprocess.run(full_command, shell=True, check=True, 
                              capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None

def get_rib(lab_name, router_name):
    """Get BGP RIB from router"""
    output = run_docker_command("vtysh -c 'show bgp ipv6 unicast json'", lab_name, router_name)
    if not output:
        return None
    return json.loads(output)

def compare_ribs(old_rib, new_rib, prefix_to_watch):
    """Compare RIBs to detect path changes for a specific prefix"""
    if not old_rib or not new_rib:
        return False
    
    old_paths = old_rib.get('routes', {}).get(prefix_to_watch, [])
    new_paths = new_rib.get('routes', {}).get(prefix_to_watch, [])
    
    # Get sets of nexthops
    old_nexthops = {nh['ip'] for path in old_paths for nh in path.get('nexthops', [])}
    new_nexthops = {nh['ip'] for path in new_paths for nh in path.get('nexthops', [])}
    
    return old_nexthops != new_nexthops

def main(lab_name, router_to_monitor, router_to_pause, prefix_to_watch, check_interval=0.1):
    LAB_NAME = lab_name
    ROUTER_TO_MONITOR = router_to_monitor
    ROUTER_TO_PAUSE = router_to_pause
    PREFIX_TO_WATCH = prefix_to_watch
    CHECK_INTERVAL = check_interval


    print(f"Starting convergence test...")
    print(f"1. Getting initial RIB from {ROUTER_TO_MONITOR}")
    initial_rib = get_rib(LAB_NAME, ROUTER_TO_MONITOR)
    if not initial_rib:
        print("Failed to get initial RIB")
        return

    print(f"2. Pausing router {ROUTER_TO_PAUSE}")
    pause_command = f"sudo docker pause clab-scenario-{LAB_NAME}-{ROUTER_TO_PAUSE}"
    subprocess.run(pause_command, shell=True)
    start_time = datetime.now()

    print(f"3. Monitoring RIB changes on {ROUTER_TO_MONITOR}")
    convergence_detected = False
    convergence_time = 0
    iterations = 0
    max_iterations = 1000  # 1000 seconds maximum

    while not convergence_detected and iterations < max_iterations:
        time.sleep(CHECK_INTERVAL)
        current_rib = get_rib(LAB_NAME, ROUTER_TO_MONITOR)
        iterations += 1

        # if the RIBs are different, then i think that bgp converged
        if compare_ribs(initial_rib, current_rib, PREFIX_TO_WATCH):
            convergence_time = (datetime.now() - start_time).total_seconds()
            print(f"\nConvergence detected after {convergence_time:.3f} seconds")
            convergence_detected = True
            
            # Print the old and new paths
            old_paths = initial_rib.get('routes', {}).get(PREFIX_TO_WATCH, [])
            new_paths = current_rib.get('routes', {}).get(PREFIX_TO_WATCH, [])
            
            print("\nOld paths:")
            for path in old_paths:
                nexthops = [nh['ip'] for nh in path.get('nexthops', [])]
                print(f"- via {nexthops}")
            
            print("\nNew paths:")
            for path in new_paths:
                nexthops = [nh['ip'] for nh in path.get('nexthops', [])]
                print(f"- via {nexthops}")

    if not convergence_detected:
        print("\nNo convergence detected within 30 seconds")

    print(f"\n4. Unpausing router {ROUTER_TO_PAUSE}")
    unpause_command = f"sudo docker unpause clab-scenario-{LAB_NAME}-{ROUTER_TO_PAUSE}"
    subprocess.run(unpause_command, shell=True)

    return convergence_detected, convergence_time

if __name__ == "__main__":
    main("better-hierarchy", "R14", "R3", "fc00:2142:a:2::/64", 0.1)
