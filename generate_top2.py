import json

# Test a different multicast role topology 
# S: Source (7)
# F: Forwarder (3, 4, 5, 6)
# R: Receiver (1, 2)
nodes = {
    1: {"role": "R", "neighbors": [(2, 2), (3, 5)]},
    2: {"role": "R", "neighbors": [(1, 2), (3, 6), (4, 4), (5, 5)]},
    3: {"role": "F", "neighbors": [(1, 5), (2, 6), (5, 2), (6, 2), (7, 5)]},
    4: {"role": "F", "neighbors": [(2, 4), (5, 5), (7, 4)]},
    5: {"role": "F", "neighbors": [(2, 5), (3, 2), (4, 5), (7, 2)]},
    6: {"role": "F", "neighbors": [(3, 2), (7, 5)]},
    7: {"role": "S", "neighbors": [(3, 5), (4, 4), (5, 2), (6, 5)]}
}

base_port = 65000

for node_id, data in nodes.items():
    config = {
        "id": node_id,
        "role": data["role"],
        "port": base_port + node_id,
        "neighbors": [{"id": n[0], "port": base_port + n[0], "cost": n[1]} for n in data["neighbors"]]
    }
    
    with open(f"config{node_id}.json", "w") as f:
        json.dump(config, f, indent=4)

print("Successfully generated Topology 2 for config1.json through config7.json!")