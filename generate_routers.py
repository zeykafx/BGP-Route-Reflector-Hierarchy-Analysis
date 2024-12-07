import os
from jinja2 import Environment, FileSystemLoader

# Define the template directory and the output directory
template_dir = './templates'
template_file = 'top_rr.jinja'

# Create the environment and load the template
env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
template = env.get_template(template_file)

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
    for j in range(1, 5):
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
    output = template.render(ctx)
    output_dir = f"script_tests/{ctx['hostname']}"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'frr.conf')
    with open(output_file, 'w') as f:
        f.write(output)
    print(f"Configuration file generated at {output_file}")
