import subprocess
import re
import time

def run_docker_command(router, command, lab_name):
    # run a command in a docker container and return the output
    docker_command = f"docker exec clab-scenario-{lab_name}-{router} {command}"
    result = subprocess.run(docker_command, shell=True, capture_output=True, text=True, timeout=60)
    return result.stdout

def ping_host(router, host_ip,lab_name, count=1):
    # Ping a host from a router and return True if successful
    output = run_docker_command(router, f"ping -c {count} {host_ip}", lab_name)
    # Check if we received any successful ping replies
    success = "0% packet loss" in output
    return success

def test_connectivity(lab_name):
    has_failed_tests = False

    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    RESET = '\033[0m'

    routers = [
        'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8',
        'R9', 'R10', 'R11', 'R12', 'R13', 'R14'
    ]

    hosts = {
        'H1': 'fc00:2142:1:1::2',
        'H2': 'fc00:2142:1:2::2',
        'H3': 'fc00:2142:1:3::2',
        'AS2_H1': 'fc00:2142:a:2::2',  # host in AS 65010
        'AS3_H1': 'fc00:2142:b:2::2'   # host in AS 65020
    }

    # Test connectivity from each router to each host
    results = []
    for router in routers:
        print(f"\nTesting connectivity from {router} for {lab_name} lab...")
        for host_name, host_ip in hosts.items():
            success = ping_host(router, host_ip, lab_name)
            results.append({
                'router': router,
                'host': host_name,
                'ip': host_ip,
                'success': success
            })
            status = f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"
            print(f"{router} → {host_name} ({host_ip}): {status}")


    print("\nConnectivity Test Summary:")
    print("=" * 50)
    success_count = len([r for r in results if r['success']])
    total_tests = len(results)
    print(f"Total tests: {BLUE}{total_tests}{RESET}")
    print(f"Successful:  {GREEN}{success_count}{RESET}")
    print(f"Failed:  {RED}{total_tests - success_count}{RESET}")
    
    # Print failed tests if any
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        has_failed_tests = True
        print("\nFailed Tests:")
        print("-" * 50)
        for test in failed_tests:
            print(f"{test['router']} → {test['host']} ({test['ip']})")

    return has_failed_tests

if __name__ == "__main__":
    # Give some time for the network to converge
    print("Starting connectivity tests...")
    print("Testing connectivity between all routers and hosts...")
    test_connectivity("full-mesh")
