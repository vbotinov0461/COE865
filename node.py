import socket
import threading
import json
import sys
import time
import uuid

class DynamicMulticastNode:
    def __init__(self, config_file):
        # Initialization Phase [cite: 56]
        with open(config_file, 'r') as f:
            self.config = json.load(f)
            
        self.node_id = self.config['id']
        self.role = self.config['role']
        self.host = '127.0.0.1' # Loopback [cite: 54]
        self.port = self.config['port']
        self.neighbors = self.config.get('neighbors', [])
        
        self.peers = {} # Active TCP connections [cite: 55]
        self.routing_table = {} # group -> list of next hops 
        self.parents = {} # group -> parent node id (for reverse path)
        self.seen_messages = set() # To prevent flooding loops
        self.running = True

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)
        print(f"[Node {self.node_id}] Booted up on port {self.port} | Role: {self.role}")
        
        while self.running:
            try:
                client_socket, addr = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except Exception:
                if self.running: break

    def handle_client(self, client_socket):
        while self.running:
            try:
                data = client_socket.recv(4096)
                if not data: break
                
                # Handle potentially multiple JSON objects in one stream
                messages = data.decode('utf-8').strip().split('\n')
                for msg_str in messages:
                    if msg_str:
                        self.process_message(json.loads(msg_str))
            except:
                break
        client_socket.close()

    def connect_to_peers(self):
        for neighbor in self.neighbors:
            peer_id, peer_port = neighbor['id'], neighbor['port']
            for attempt in range(5):
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((self.host, peer_port))
                    self.peers[peer_id] = sock
                    break
                except ConnectionRefusedError:
                    time.sleep(1)

    def send_to_peer(self, peer_id, message):
        if peer_id in self.peers:
            try:
                # Append newline to separate JSON messages in stream
                self.peers[peer_id].send((json.dumps(message) + '\n').encode('utf-8'))
            except Exception as e:
                print(f"[Node {self.node_id}] Send error to Node {peer_id}: {e}")

    def process_message(self, message):
        msg_id = message.get("msg_id")
        msg_type = message.get("type")
        group = message.get("group")
        sender = message.get("sender")

        # Display received message content [cite: 61]
        if msg_type == "DATA":
             print(f"\n[Node {self.node_id}] RECEIVED {msg_type} from Node {sender} | Content: '{message.get('content')}'")
        else:
             print(f"[Node {self.node_id}] Received {msg_type} for group {group} from Node {sender}")

        # Process ANNOUNCE (Flooding to build reverse path)
        if msg_type == "ANNOUNCE":
            if msg_id in self.seen_messages: return
            self.seen_messages.add(msg_id)
            
            # Record the first node we heard the announcement from as our parent for this group
            if group not in self.parents and self.role != 'S':
                self.parents[group] = sender
                print(f"[Node {self.node_id}] Set Node {sender} as parent for group {group}")
                
                # If I am a receiver, I need to send a JOIN up the tree
                if self.role == 'R':
                    self.send_join(group)

            # Forward the announcement to all other neighbors
            self.forward_to_all_except(message, sender)

        # Process JOIN (Building the forward routing table)
        elif msg_type == "JOIN":
            if group not in self.routing_table:
                self.routing_table[group] = set()
            
            if sender not in self.routing_table[group]:
                self.routing_table[group].add(sender)
                print(f"[Node {self.node_id}] Added Node {sender} to routing table for {group}")
                
                # Forward the JOIN up the tree towards the source
                if self.role != 'S' and group in self.parents:
                    join_msg = {"type": "JOIN", "group": group, "sender": self.node_id}
                    self.send_to_peer(self.parents[group], join_msg)

        # Process DATA (Multicasting along the built tree)
        elif msg_type == "DATA":
            if msg_id in self.seen_messages: return
            self.seen_messages.add(msg_id)
            
            if self.role == 'R':
                print(f"*** Node {self.node_id} (Receiver) consumed DATA: {message.get('content')} ***")
            
            # Forward to all next hops in the routing table 
            if group in self.routing_table:
                forward_msg = message.copy()
                forward_msg["sender"] = self.node_id
                for hop in self.routing_table[group]:
                    self.send_to_peer(hop, forward_msg)

    def send_join(self, group):
        parent = self.parents.get(group)
        if parent:
            join_msg = {"type": "JOIN", "group": group, "sender": self.node_id}
            self.send_to_peer(parent, join_msg)

    def forward_to_all_except(self, message, exclude_id):
        forward_msg = message.copy()
        forward_msg["sender"] = self.node_id
        for peer_id in self.peers:
            if peer_id != exclude_id:
                self.send_to_peer(peer_id, forward_msg)

    def display_routing_table(self):
        print(f"\n--- Node {self.node_id} Routing Table ---")
        for group, next_hops in self.routing_table.items():
            print(f" Group {group} -> Next Hops: {list(next_hops)}")
        print("-----------------------------\n")

    def run(self):
        threading.Thread(target=self.start_server, daemon=True).start()
        time.sleep(2) # Wait for all nodes to spin up
        self.connect_to_peers()

        # Source initiates the dynamic tree building
        if self.role == 'S':
            time.sleep(3)
            group = "G1"
            print(f"\n[Node {self.node_id}] Initiating Tree Building with ANNOUNCE for {group}")
            announce_msg = {
                "msg_id": str(uuid.uuid4()),
                "type": "ANNOUNCE",
                "group": group,
                "sender": self.node_id
            }
            self.seen_messages.add(announce_msg["msg_id"])
            self.forward_to_all_except(announce_msg, None)
            
            # Wait for JOINs to propagate back, then display table and send data
            time.sleep(4)
            self.display_routing_table() # Display routing table [cite: 62]
            
            content = "Hello Figure 1 Multicast Group!"
            print(f"\n[Node {self.node_id}] Sending Multicast DATA to {group}")
            data_msg = {
                "msg_id": str(uuid.uuid4()),
                "type": "DATA",
                "group": group,
                "content": content,
                "sender": self.node_id
            }
            self.seen_messages.add(data_msg["msg_id"])
            if group in self.routing_table:
                for hop in self.routing_table[group]:
                    self.send_to_peer(hop, data_msg)
        else:
            # Display tables for Non-Source nodes after tree building phase [cite: 62]
            time.sleep(8)
            self.display_routing_table()

        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

if __name__ == "__main__":
    node = DynamicMulticastNode(sys.argv[1])
    node.run()