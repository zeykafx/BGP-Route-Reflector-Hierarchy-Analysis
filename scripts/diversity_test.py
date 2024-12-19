import subprocess
import re

def run_docker_command(command, lab_name, router_name):
    """Run a command on router RR1T using docker exec"""
    full_command = f"sudo docker exec -it clab-scenario-{lab_name}-{router_name} {command}"
    try:
        result = subprocess.run(full_command, shell=True, check=True, 
                              capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return None

def analyze_bgp_paths(lab_name, router_name):
    print(f"Starting BGP path diversity analysis for the {lab_name} topology on router {router_name} ...")
    # Get BGP IPv6 routes with details
    output = run_docker_command("vtysh -c 'show bgp ipv6 unicast'", lab_name, router_name)
    if not output:
        return
    
    # Initialize counters
    total_prefixes = 0
    path_counts = {}  # Dictionary to store prefix -> number of paths
    
    # Regular expression to match prefix lines
    prefix_pattern = r'^[*>= ]*(i *)*(fc00:[0-9a-f:]+/\d+)'
    
    # Process the output
    current_prefix = None
    current_paths = 0
    
    for line in output.split('\n'):
        # Look for prefix lines
        match = re.search(prefix_pattern, line)
        if match:
            # If we were processing a prefix, save its count
            if current_prefix:
                path_counts[current_prefix] = current_paths
            
            # Start counting for new prefix
            current_prefix = match.group(2)
            current_paths = 1
            total_prefixes += 1
        elif '*' in line and current_prefix:
            # Additional paths for current prefix
            current_paths += 1
    
    # Save the last prefix count
    if current_prefix:
        path_counts[current_prefix] = current_paths
    
    # Print results
    print(f"BGP Path Diversity Analysis: {lab_name} - {router_name}")
    print("==========================")
    print(f"Total prefixes in RIB: {total_prefixes}")
    print("\nPath diversity per prefix:")
    print("--------------------------")
    for prefix, paths in path_counts.items():
        print(f"Prefix: {prefix:<30} Paths: {paths}")
    
    # Calculate average path diversity
    if total_prefixes > 0:
        avg_paths = sum(path_counts.values()) / total_prefixes
        print(f"\nAverage paths per prefix: {avg_paths:.2f}")

if __name__ == "__main__":
    analyze_bgp_paths(lab_name='hierarchy', router_name='RR1T')
    # analyze_bgp_paths(lab_name='full-mesh', router_name='R1')
