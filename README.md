# BGP Route Reflector Hierarchy

**Group 3**: Thomas Juan, Detry Corentin

## Introduction

This lab is designed to showcase BGP Route Reflection in a hiearchical design. Our main AS (65000) has 2 Top Level Route Reflectors (RR1T and RR2T) connected in full mesh with each other, then we have 4 Second Level Route Reflectors (RR1S->RR4S), both connected to each top level route reflectors but not in full mesh with the others.
Finally we have 8 regular BGP routers (R1->R8), each connected to 2 second level route reflectors for redundancy.

RR4S has an eBGP session with a remote AS (65010) and advertises the routes to the other routers in the AS.
This other AS has 1 router (E1) which has a host (h3) connected to it (Host address: `fc00:2142:a:2::2`).
That host is reachable from any router in our AS.

RR1S has a host connected to it (Host address: `fc00:2142:1:3::2`) which is reachable from any router in our AS and from the neighbor AS.


## Diagram

![Diagram of Route Reflector Hierarchy](./diagram_rr_hierarchy.png)

## Configuration Generation

Our router configurations are created using the `generate_configs.py` script. This script uses the `jinja` template engine to create configurations from the `templates` directory.

This simplifies the generation of router configurations and makes it easy to change them. Instead of manually modifying each router's configurations, we can simply modify the templates and rerun the script.

We started this lab by configuring the routers manually to make sure that everything worked, then after lots of small errors due to mismatched configurations, we decided to automate the process.
The templates are not super readable, so we still advise you to read the configurations manually to understand what is going on.

## Running the lab

To run the lab, you just need to run the `run.sh` script. This script will compile the hosts and start the containerlab topology.

Once everything is running, you can test that the hosts are reachable by running these commands in any routers (you can access the routers by running `sudo docker exec -it clab-scenario-hierarchy-{ROUTER-NAME} vtysh`):
- `ping fc00:2142:a:2::2`
- `ping fc00:2142:1:3::2`

You can also check the BGP routes by running `show bgp ipv6 detail` or `show bgp ipv6 unicast` in any router.
To view all the routes, run `show ipv6 route`.
