# BGP Route Reflector Hierarchy

**Group 3**: Thomas Juan, Detry Corentin

## Introduction

This lab is designed to showcase BGP Route Reflection in a hiearchical design using FRRouting and containerlab (IPv6 only).

## Route Reflector Hierarchy Topology

![Diagram of Route Reflector Hierarchy](./diagram_rr_hierarchy.png)

Our main AS (65000) has 2 Top Level Route Reflectors (RR1T and RR2T) connected in full mesh with each other, then we have 4 Second Level Route Reflectors (RR1S->RR4S), both connected to each top level route reflectors but not in full mesh with the others.

Finally we have 8 regular BGP routers (R1->R8), each connected to 2 second level route reflectors for redundancy.

As you can see on the diagram, the BGP topology follows the IGP topology.

We have 2 external ASes (65010 and 65020) connected to our main AS:
- AS 65010 is connected to RR4S, and has a host (AS2_H1, address: `fc00:2142:a:2::2`) connected to it.
- AS 65020 is connected to R2, and has a host (AS3_H1, address: `fc00:2142:b:2::2`) connected to it.

There are three hosts in our AS:
- H1 connected to RR1S (Host address: `fc00:2142:1:1::2`)
- H2 connected to R4 (Host address: `fc00:2142:1:2::2`)
- H3 connected to R8 (Host address: `fc00:2142:1:3::2`)

The hosts are reachable from any router/host in any AS.

## Full Mesh Topology
![Diagram of Full Mesh Topology](./diagram_full_mesh.png)

To be able to compare the performances of the Route Reflector Hierarchy with a full mesh topology, we also created a full mesh topology with the same ASes and hosts.

The diagram shows all the IGP links between the routers, for clarity we opted to not show the BGP sessions since we know that in a full mesh topology, all routers of an AS/Area are connected to each other using iBGP.

There is the same number of routers, but the number of IGP links is not exactly the same.

There are still 2 external ASes (65010 and 65020) connected to our main AS:
- AS 65010 is connected to R9, and has a host (AS2_H1, address: `fc00:2142:a:2::2`) connected to it.
- AS 65020 is connected to R7, and has a host (AS3_H1, address: `fc00:2142:b:2::2`) connected to it.

There are three hosts in our AS:
- H1 connected to R8 (Host address: `fc00:2142:1:1::2`)
- H2 connected to R6 (Host address: `fc00:2142:1:2::2`)
- H3 connected to R11 (Host address: `fc00:2142:1:3::2`)

## Configuration Generation Script
For the Route Reflector Hierarchy, we used a script to generate the configurations of the routers.

Our router configurations are created using the `generate_configs.py` script. This script uses the `jinja` template engine to create configurations from the `templates` directory.

This simplifies the generation of router configurations and makes it easy to change them. Instead of manually modifying each router's configurations, we can simply modify the templates and rerun the script.

We started this lab by configuring the routers manually to make sure that everything worked, then after lots of small errors due to mismatched configurations, we decided to automate the process.
The templates are not super readable, so we still advise you to read the configurations manually to understand what is going on.

## Running the lab
# TODO
To run the lab, you just need to run the `run.sh` script. This script will compile the host docker image and start the containerlab topology.

Once everything is running, you can test that the hosts are reachable by running these commands in any routers (you can access the routers by running `sudo docker exec -it clab-scenario-hierarchy-{ROUTER-NAME} vtysh`):
- `ping fc00:2142:a:2::2`
- `ping fc00:2142:1:3::2`

You can also check the BGP routes by running `show bgp ipv6 detail` or `show bgp ipv6 unicast` in any router.
To view all the routes, run `show ipv6 route`.
