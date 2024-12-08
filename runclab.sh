rm -r clab-scenario-hierarchy/
python3.11 generate_routers.py -slr 6 -nr 9
mkdir clab-scenario-hierarchy/h2
touch clab-scenario-hierarchy/h2/frr.conf
mkdir clab-scenario-hierarchy/h3
touch clab-scenario-hierarchy/h3/frr.conf

# sudo containerlab destroy -t hierarchy.clab.yml 
sudo containerlab deploy -t hierarchy.clab.yml 