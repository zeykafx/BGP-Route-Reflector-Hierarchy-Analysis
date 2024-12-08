# BGP Route Reflector Hierarchy
## Introduction

This lab is designed to showcase BGP Route Reflection in a hiearchical design. Our main AS (65000) has 2 top level route reflectors (RR1T and RR2T) connected in full mesh with each other, then we have 4 second level route reflectors (RR1S->RR4S), both connected to each top level route reflectors but not in full mesh with the others.
Finally we have 8 regular BGP routers (R1->R8), each connected to 2 second level route reflectors for redundancy.

RR4S has an eBGP session with a remote AS (65001) and advertises the routes to the other routers in the AS.
This other AS has 1 router (E1) which has a host (h3) connected to it (`fc00:2142:a:2::2`).
That host is reachable from any router in our AS.

RR1S has a host connected to it (`fc00:2142:1:3::2`) which is reachable from any router in our AS and from the neighbor AS.
