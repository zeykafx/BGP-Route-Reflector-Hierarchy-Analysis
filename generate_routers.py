import os
from jinja2 import Environment, FileSystemLoader
import argparse


parser = argparse.ArgumentParser(description="Generate a YAML file using Jinja2.")
parser.add_argument("-slr", type=int, default=4, help="Number of second-level routers")
parser.add_argument("-nr", type=int, default=2, help="Number of normal routers")

# Define the template directory and the output directory
template_dir = './templates'
scripts_dir = './clab-scenario-hierarchy'

# Create the environment and load the template
env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)

def generate_top_level_rr(sr):
    template_top_rr = env.get_template("top_rr.jinja")

    # Define the contexts for each router
    contexts = []
    for i in range(1, 3):  # Assuming we have 2 RRs: RR1T and RR2T
        hostname = f'RR{i}T'
        bgp_router_cluster_id = f'1.0.0.{i}'
        net = f'49.0001.0000.0000.000{i}.00'
        # Interface connecting to the other top-level peer
        interfaces = [
            {'name': f'eth-rr{3-i}t', 'ipv6_address': f'fc00:2142:1:2::{i}/64'}
        ]
        for j in range(1, sr+1):
            interfaces.append({'name': f'eth-rr{j}s', 'ipv6_address': f'fc00:2142:1:{i}{j}::1/64'})
        loopback = {'ipv6_address': f'fc00:2142:1::{i}/128'}
        context = {
            'hostname': hostname,
            'bgp_router_cluster_id': bgp_router_cluster_id,
            'net': net,
            'interfaces': interfaces,
            'loopback': loopback,
        }
        contexts.append(context)

    # Generate configuration files for each context
    for ctx in contexts:
        output = template_top_rr.render(ctx)
        output_dir = f"{scripts_dir}/{ctx['hostname']}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'frr.conf')
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Configuration file generated at {output_file}")


def generate_second_level_rr(n, nr):
    template_second_rr = env.get_template('second_rr.jinja')

    # Define contexts for second level RRs (RR1S through RR4S)
    contexts = []
    for i in range(1, n+1):
        hostname = f'RR{i}S'
        bgp_router_cluster_id = f'2.0.0.{i}'
        net = f'49.0001.0000.0000.000{i+2}.00'
        
        # Interfaces connecting to top-level RRs
        top_rr_interfaces = [
            {'name': 'eth-rr1t', 'ipv6_address': f'fc00:2142:1:1{i}::2/64'},
            {'name': 'eth-rr2t', 'ipv6_address': f'fc00:2142:1:2{i}::2/64'}
        ]
        
        # Client interfaces - RR1S/RR2S connect to R1-R4, RR3S/RR4S connect to R5-R8
        client_interfaces = []
        # start_router = 1 if i <= 2 else 5
        # end_router = 5 if i <= 2 else 9
        i_values = get_router_index(i,n,nr)
        print(i_values)
        for r in i_values:
            client_interfaces.append(
                {'name': f'eth-r{r}', 'ipv6_address': f'fc00:2142:1:{i+2}{r}::1/64'}
            )
        
        loopback = {'ipv6_address': f'fc00:2142:1::{i+2}/128'}
        
        context = {
            'hostname': hostname,
            'bgp_router_cluster_id': bgp_router_cluster_id,
            'net': net,
            'top_rr_interfaces': top_rr_interfaces,
            'client_interfaces': client_interfaces,
            'loopback': loopback,
            'has_external_peer': (i == 4),  # Only RR4S has external peer
            'has_host': (i == 1),  # Only RR1S has host interface
        }
        
        # Add host interface for RR1S
        if i == 1:
            context['host_interface'] = {
                'name': 'eth-h2',
                'ipv6_address': 'fc00:2142:1:3::1/64'
            }
            context['host_prefix'] = 'fc00:2142:1:3::2/64'
            
        contexts.append(context)

    # Generate configuration files
    for ctx in contexts:
        output = template_second_rr.render(ctx)
        output_dir = f"{scripts_dir}/{ctx['hostname']}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'frr.conf')
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Configuration file generated at {output_file}")

def get_router_index(rr_pair,sr,nr):
    if rr_pair < 1 or rr_pair > sr:
        raise ValueError("rr_pair must be in the range [1, sr]")

    # Calculate all possible values of i
    i_values = []
    k = 0
    while True:
        i = k * sr + rr_pair
        if nr is not None and i > nr:
            break
        i_values.append(i)
        k += 1
    
    return i_values

def generate_regular_routers(n,sr):
    template_regular = env.get_template('regular_router.jinja')
    
    # Define contexts for regular routers (R1 through R8)
    contexts = []
    for i in range(1, n+1):
        hostname = f'R{i}'
        bgp_router_id = f'3.0.0.{i}'
        net = f'49.0001.0000.0000.00{i+10:02d}.00'
        
        # Each router connects to two RRs based on position
        rr_pair = ((i-1)%sr) + 1  # This will give 1 for R1-R4, and 3 for R5-R8
        print(rr_pair)
        # basically, R1-R4 connect to RR1S and RR2S, while R5-R8 connect to RR3S and RR4S
        rr_interfaces = [
            {'name': f'eth-rr{rr_pair}s', 'ipv6_address': f'fc00:2142:1:{(rr_pair+2)}{i}::2/64'},
            {'name': f'eth-rr{rr_pair+1}s', 'ipv6_address': f'fc00:2142:1:{(rr_pair+3)}{i}::2/64'}
        ]
        
        loopback = {'ipv6_address': f'fc00:2142:1::{i+10:02d}/128'}
        
        context = {
            'hostname': hostname,
            'bgp_router_id': bgp_router_id,
            'net': net,
            'rr_interfaces': rr_interfaces,
            'loopback': loopback,
        }
        contexts.append(context)

    # Generate configuration files
    for ctx in contexts:
        output = template_regular.render(ctx)
        output_dir = f"{scripts_dir}/{ctx['hostname']}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'frr.conf')
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Configuration file generated at {output_file}")


def generate_external_router():
    template_external = env.get_template('external_router.jinja')

    # Define context for external router E1
    context = {
        'hostname': 'E1',
        'bgp_router_id': '4.0.0.1', 
        'bgp_as': '65010',
        'net': '49.0001.0000.0000.0021.00',
        'loopback': {'ipv6_address': 'fc00:2142:a::1/128'},
        'has_host': True,
        'host_interface': {
            'ipv6_address': 'fc00:2142:a:2::1/64'
        }
    }

    # Generate configuration file
    output = template_external.render(context)
    output_dir = f"{scripts_dir}/E1"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'frr.conf')
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"Configuration file generated at {output_file}")

def generate_clab_file(sr, nr):
    template_clab = env.get_template('clab_file.jinja')

    # Generate configuration file
    output = template_clab.render(sr=sr, nr=nr)
    output_dir = "./"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'hierarchy.clab.yml')
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"Containerlab file generated at {output_file}")


if __name__ == '__main__':
    args = parser.parse_args()    
    
    print(args)
    second_level_routers = args.slr
    normal_routers = args.nr

    generate_clab_file(second_level_routers, normal_routers)
    generate_top_level_rr(second_level_routers)
    generate_second_level_rr(second_level_routers,normal_routers)
    generate_external_router()
    generate_regular_routers(normal_routers,second_level_routers)
