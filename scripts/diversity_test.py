from datetime import datetime
import json
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
    # print(f"Starting BGP path diversity analysis for the {lab_name} topology on router {router_name} ...")
    # Get BGP IPv6 routes with details
    output = run_docker_command("vtysh -c 'show bgp ipv6 unicast json'", lab_name, router_name)
    if not output:
        return
    
    # parse the json output
    output = json.loads(output)
    
    # Initialize counters
    total_prefixes = 0
    path_counts = {}  # Dictionary to store prefix -> number of paths
    
    # Process routes from JSON output
    routes = output.get('routes', {})
    for prefix, paths in routes.items():
        # Skip the fc00:2142:1::/48 prefix
        if prefix == 'fc00:2142:1::/48':
            continue
            
        # Count unique nexthops for this prefix
        nexthops = set()
        for path in paths:
            for nexthop in path.get('nexthops', []):
                nexthops.add(nexthop['ip'])
        
        path_counts[prefix] = len(nexthops)
        total_prefixes += 1

    # Print results
    print(f"BGP Path Diversity Analysis: {lab_name} - {router_name}")
    print("==========================")
    print(f"Total prefixes in RIB: {total_prefixes}")
    print("\nUnique paths per prefix:")
    print("--------------------------")
    for prefix, paths in path_counts.items():
        print(f"Prefix: {prefix:<30} Unique Paths: {paths} \t- Total Paths: {len(routes[prefix])}")
    
    # Calculate average path diversity
    if total_prefixes > 0:
        avg_paths = sum(path_counts.values()) / total_prefixes
        print(f"\nAverage unique paths per prefix: {avg_paths:.2f}")
        avg_total_paths = sum([len(paths) for paths in routes.values()]) / total_prefixes
        print(f"Average total paths per prefix: {avg_total_paths:.2f}")
        results = {
            'lab_name': lab_name,
            'timestamp': datetime.now().timestamp(),
            'total_prefixes': total_prefixes,
            'path_counts': path_counts,
            'average_paths': avg_paths,
            'router': router_name
        }
        save_results_to_file(results, lab_name)
        compare_current_res_to_other_lab_res(lab_name, results, router_name)

def save_results_to_file(results, lab_name):
    with open(f"./scripts/bgp_path_diversity_results_{lab_name}.json", 'w') as f:
        json.dump(results, f, indent=2)
        

def compare_current_res_to_other_lab_res(lab_name, results, router_name):
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    RESET = '\033[0m'

    other_lab = 'full-mesh' if lab_name == 'better-hierarchy' else 'better-hierarchy'
    # Load previous results (if any)
    try:
        with open(f"./scripts/bgp_path_diversity_results_{other_lab}.json", 'r') as f:
            prev_results = json.load(f)
    except FileNotFoundError:
        return
    
    print("\n")

    if router_name != prev_results['router']:
        print(f"{RED}Previous results for {lab_name} were generated for a different router ({prev_results['router']}), the comparison will not be accurate.{RESET}\n")

    print(f"Comparing path diversity results of {lab_name} to results of {other_lab}")
    # Compare average path diversity
    current_avg = results['average_paths']
    other_avg = prev_results['average_paths']
    
    # Determine which lab has better path diversity
    if current_avg > other_avg:
        current_format = f"{GREEN}"
        other_format = f"{BLUE}"
    else:
        current_format = f"{BLUE}"
        other_format = f"{GREEN}"
    
    print(f"Average unique paths per prefix ({lab_name} - Current): {current_format}{current_avg:.2f}{RESET}")
    print(f"Average unique paths per prefix ({other_lab} - Previous): {other_format}{other_avg:.2f}{RESET}")


if __name__ == "__main__":
    analyze_bgp_paths(lab_name='hierarchy', router_name='RR1T')
    # analyze_bgp_paths(lab_name='full-mesh', router_name='R1')

