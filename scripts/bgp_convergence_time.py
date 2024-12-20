import subprocess
import time
from datetime import datetime
import sys

def run_docker_command(command, lab_name, router_name):
    """Run a command on a router using docker exec"""
    docker_command = f"docker exec clab-scenario-{lab_name}-{router_name} {command}"
    result = subprocess.run(docker_command, shell=True, capture_output=True, text=True, timeout=60)
    if "No such container" in result.stderr:
        print("Error: Lab not running")
        sys.exit(1)
    return result.stdout

def ping_router(source_router, dest_ip, lab_name):
    """Ping a destination from source router, return True if successful"""
    output = run_docker_command(f"ping -c 1 {dest_ip}", lab_name, source_router)
    return "0% packet loss" in output

def check_connectivity(lab_name, router_name):
    # """Check connectivity to all other routers in the AS"""
    
    # external hosts
    router_ips = {
        "AS2_H1": "fc00:2142:a:2::2",
        "AS3_H1": "fc00:2142:b:2::2",
    }

    print(f"Checking BGP convergence for {router_name} in {lab_name} lab...")
    start_time = datetime.now()
    while True:
        all_reachable = True
        for dest_router, dest_ip in router_ips.items():
            if not ping_router(router_name, dest_ip, lab_name):
                all_reachable = False
                break
                
        if all_reachable:
            convergence_time = (datetime.now() - start_time).total_seconds()
            print(f"Convergence successful in {convergence_time:.3f} seconds")
            return True, convergence_time
            
        time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 is_is_convergence.py <lab_name> <router_name>")
        sys.exit(1)
        
    lab = sys.argv[1]
    router = sys.argv[2]
    success, time = check_connectivity(lab, router)
    print(f"Convergence successful: {success}")
    print(f"Convergence time: {time:.3f} seconds")
