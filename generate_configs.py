import json

# Define the topology from Figure 1 
# S: Source (1)
# F: Forwarder (2, 3, 5)
# R: Receiver (4, 6, 7)
nodes = {
    1: {"role": "S", "neighbors": [(2, 2), (3, 5)]},
    2: {"role": "F", "neighbors": [(1, 2), (3, 6), (4, 4), (5, 5)]},
    3: {"role": "F", "neighbors": [(1, 5), (2, 6), (5, 2), (6, 2)]},
    4: {"role": "R", "neighbors": [(2, 4), (5, 5), (7, 4)]},
    5: {"role": "F", "neighbors": [(2, 5), (3, 2), (4, 5), (6, 5), (7, 2)]},
    6: {"role": "R", "neighbors": [(3, 2), (5, 5), (7, 5)]},
    7: {"role": "R", "neighbors": [(4, 4), (5, 2), (6, 5)]}
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

print("Successfully generated config1.json through config7.json!")