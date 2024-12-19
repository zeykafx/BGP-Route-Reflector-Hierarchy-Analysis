import os
from jinja2 import Environment, FileSystemLoader

# Define the template directory and the output directory
template_dir = './templates'
scripts_dir = './clab-scenario-hierarchy'

# Create the environment and load the template
env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)

def generate_top_level_rr():
    template_top_rr = env.get_template("top_rr.jinja")

    # Define the contexts for each router
    contexts = []
    for i in range(1, 3):  # Assuming we have 2 RRs: RR1T and RR2T
        hostname = f'RR{i}T'
        bgp_router_cluster_id = f'1.0.0.{i}'
        net = f'47.0003.0000.0000.0000.0000.0000.0000.0000.000{i}.00'

        # Interface connecting to the other top-level peer
        interfaces = [
            {'name': f'eth-rr{3-i}t', "has_ip": False, "address": f'fc00:2142:1::{3-i}'}
        ]
        for j in range(1, 5):
            interfaces.append({'name': f'eth-rr{j}s', 'has_ip': False, "address": f'fc00:2142:1::{j+2}'})
        
        loopback = {'ipv6_address': f'fc00:2142:1::{i}/128'}
        context = {
            'hostname': hostname,
            'isis_router_name': hostname,
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


def generate_second_level_rr():
    template_second_rr = env.get_template('second_rr.jinja')

    # Define contexts for second level RRs (RR1S through RR4S)
    contexts = []
    for i in range(1, 5):
        hostname = f'RR{i}S'
        bgp_router_cluster_id = f'2.0.0.{i}'
        net = f'47.0003.0000.0000.0000.0000.0000.0000.0000.000{i+2}.00'
        
        # Interfaces connecting to top-level RRs
        top_rr_interfaces = [
            {'name': 'eth-rr1t', 'has_ip': False, "address": 'fc00:2142:1::1'},
            {'name': 'eth-rr2t', 'has_ip': False, "address": 'fc00:2142:1::2'},
        ]
        
        # Client interfaces - RR1S/RR2S connect to R1-R4, RR3S/RR4S connect to R5-R8
        client_interfaces = []
        start_router = 1 if i <= 2 else 5
        end_router = 5 if i <= 2 else 9
        for r in range(start_router, end_router):
            client_interfaces.append(
                {'name': f'eth-r{r}', 'has_ip': False, 'address': f'fc00:2142:1::{r+6:02x}'}
            )
        
        loopback = {'ipv6_address': f'fc00:2142:1::{i+2}/128'}
        
        context = {
            'hostname': hostname,
            'isis_router_name': hostname,
            'bgp_router_cluster_id': bgp_router_cluster_id,
            'net': net,
            'top_rr_interfaces': top_rr_interfaces,
            'client_interfaces': client_interfaces,
            'loopback': loopback,
            'has_external_peer': (i == 4),  # Only RR4S has external peer
            'external_peer_interface': "eth-as2r1",
            'external_peer_as': 65010,
            'has_host': (i == 1),  # Only RR1S has host interface
        }
        
        # Add host interface for RR1S
        if i == 1:
            context['host_interface'] = {
                'name': 'eth-h1',
                'ipv6_address': 'fc00:2142:1:1::1/64'
            }
            context['host_prefix'] = 'fc00:2142:1:1::2/64'
            
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


def generate_regular_routers():
    template_regular = env.get_template('regular_router.jinja')
    
    # Define contexts for regular routers (R1 through R8)
    contexts = []
    for i in range(1, 9):
        hostname = f'R{i}'
        bgp_router_id = f'3.0.0.{i}'
        net = f'47.0003.0000.0000.0000.0000.0000.0000.0000.00{i+6:02d}.00'
        
        # Each router connects to two RRs based on position
        rr_pair = ((i-1) // 4) * 2 + 1  # This will give 1 for R1-R4, and 3 for R5-R8
        # basically, R1-R4 connect to RR1S and RR2S, while R5-R8 connect to RR3S and RR4S
        rr_interfaces = [
            {'name': f'eth-rr{rr_pair}s',   'has_ip': False, "address": f'fc00:2142:1::{rr_pair+2}'},
            {'name': f'eth-rr{rr_pair+1}s', 'has_ip': False, "address": f'fc00:2142:1::{rr_pair+3}'}            
        ]
        
        loopback = {'ipv6_address': f'fc00:2142:1::{i+6:02x}/128'}


        context = {
            'hostname': hostname,
            'isis_router_name': hostname,
            'bgp_router_id': bgp_router_id,
            'net': net,
            "rr_interfaces": rr_interfaces,
            'loopback': loopback,
            'has_external_peer': (i == 2),  # Only R2 has external peer on this level
            'external_peer_interface': "eth-as3r1",
            'external_peer_as': 65020,
            'has_host': (i == 4 or i == 8),  # Only 4 and 8 have hosts on this level
        }

        # Add host interface for R4 and R8
        if i == 4 or i == 8:
            context['host_interface'] = {
                'name': 'eth-h2' if i == 4 else 'eth-h3',
                'ipv6_address': f'fc00:2142:1:2::1/64' if i == 4 else f'fc00:2142:1:3::1/64'
            }
            context['host_prefix'] = f'fc00:2142:1:2::2/64' if i == 4 else f'fc00:2142:1:3::2/64'

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

    contexts = [
        {
            'hostname': 'AS2_R1',
            'isis_router_name': 'AS2_R1',
            'bgp_router_id': '4.0.0.1',
            'bgp_as': '65010',
            'prefix': 'fc00:2142:a::/48',
            'net': '47.0003.0000.0000.0000.0000.0000.0000.0004.0001.00',
            'external_peer_as': 65000,
            'external_peer_interface': 'eth-rr4s',
            'loopback': {'ipv6_address': 'fc00:2142:a::1/128'},
            'has_host': True,
            'host_interface': {
                'name': 'eth-h1',
                'ipv6_address': 'fc00:2142:a:2::1/64',
                'host_prefix': 'fc00:2142:a:2::2/64'
            }
        },
        {
            'hostname': 'AS3_R1', 
            'isis_router_name': 'AS3_R1',
            'bgp_router_id': '5.0.0.1',
            'bgp_as': '65020',
            'prefix': 'fc00:2142:b::/48',
            'net': '47.0003.0000.0000.0000.0000.0000.0000.0005.0001.00',
            'external_peer_as': 65000,
            'external_peer_interface': 'eth-r2',
            'loopback': {'ipv6_address': 'fc00:2142:b::1/128'},
            'has_host': True,
            'host_interface': {
                'name': 'eth-h1',
                'ipv6_address': 'fc00:2142:b:2::1/64',
                'host_prefix': 'fc00:2142:b:2::2/64'
            }
        }
    ]

    # Generate configuration files
    for context in contexts:
        output = template_external.render(context)
        output_dir = f"{scripts_dir}/{context['hostname']}"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'frr.conf')
        with open(output_file, 'w') as f:
            f.write(output)
        print(f"Configuration file generated at {output_file}")

def generate_clab_file():
    template_clab = env.get_template('clab_file.jinja')

    # Generate configuration file
    output = template_clab.render()
    output_dir = "./"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'hierarchy.clab.yml')
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"Containerlab file generated at {output_file}")


def create_hosts_directory():
    os.makedirs(f"{scripts_dir}/AS2_H1", exist_ok=True)
    with open(f"{scripts_dir}/AS2_H1/frr.conf", 'w') as f:
        f.write("")
    os.makedirs(f"{scripts_dir}/AS3_H1", exist_ok=True)
    with open(f"{scripts_dir}/AS3_H1/frr.conf", 'w') as f:
        f.write("")
    os.makedirs(f"{scripts_dir}/H1", exist_ok=True)
    with open(f"{scripts_dir}/H1/frr.conf", 'w') as f:
        f.write("")
    os.makedirs(f"{scripts_dir}/H2", exist_ok=True)
    with open(f"{scripts_dir}/H2/frr.conf", 'w') as f:
        f.write("")
    os.makedirs(f"{scripts_dir}/H3", exist_ok=True)
    with open(f"{scripts_dir}/H3/frr.conf", 'w') as f:
        f.write("")

if __name__ == '__main__':
    generate_clab_file()
    generate_top_level_rr()
    generate_second_level_rr()
    generate_external_router()
    generate_regular_routers()
    create_hosts_directory()
