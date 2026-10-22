from fastapi import APIRouter
from database import db
import json
import os
import math

router = APIRouter(tags=["Navigation"])

# Configuration for different cameras
# Dynamic path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CAM_NODE_DIR = os.path.join(BASE_DIR, "camera_node")

CAM_CONFIG = {
    "CAM_1": {
        "lanes": os.path.join(CAM_NODE_DIR, "camera1", "lanes.json"),
        "slots": os.path.join(CAM_NODE_DIR, "camera1", "arial11.json"),
        "image": "arial2.jpg"
    },
    "CAM_2": {
        "lanes": os.path.join(CAM_NODE_DIR, "camera2", "vid4_lanes.json"),
        "slots": os.path.join(CAM_NODE_DIR, "camera2", "vid4.json"),
        "image": "vid4.jpg"
    }
}

def get_dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def generate_dynamic_instructions(path_coords, slot_id, camera_id):
    if len(path_coords) < 2:
        return ["🚩 Your vehicle is already at the destination."]

    instructions = []
    
    # 1. Opening Instruction
    if camera_id == "CAM_1":
        instructions.append("🚗 **START**: Drive Right from the entrance gate.")
    else:
        instructions.append("🚗 **START**: Enter the parking area and follow the path.")

    # 2. Analyze Path for Turns
    # We look at sets of 3 nodes to detect a 'turn'
    i = 0
    while i < len(path_coords) - 2:
        p1 = path_coords[i]
        p2 = path_coords[i+1]
        p3 = path_coords[i+2]
        
        # Vectors
        v1 = (p2[0]-p1[0], p2[1]-p1[1])
        v2 = (p3[0]-p2[0], p3[1]-p2[1])
        
        # Cross product (2D) to find Left vs Right
        # In image coords (Y down), cross > 0 is a Right turn, cross < 0 is Left
        cp = v1[0]*v2[1] - v1[1]*v2[0]
        
        # Dot product for the angle
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 > 0 and mag2 > 0:
            cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
            angle = math.degrees(math.acos(cos_theta))
            
            # If the angle is significant (> 30 degrees), it's a turn
            if angle > 30:
                if cp > 0:
                    instructions.append("➡️ **TURN**: Take a **Sharp Right** following the lane.")
                else:
                    instructions.append("⬅️ **TURN**: Take a **Sharp Left** following the lane.")
                # Skip the middle node of the turn to avoid double-reporting one turn
                i += 1 
            else:
                # If we've gone straight for a while, give a "Continue" prompt
                if i % 5 == 0 and i > 0:
                    instructions.append("⬆️ **DRIVE**: Continue straight along the parking row.")
        
        i += 1

    # 3. Final Arrival
    instructions.append(f"🏁 **ARRIVAL**: Turn into the row and Park in Slot **{slot_id}**.")
    return instructions

@router.get("/navigation-data/{camera_id}")
def get_navigation_data(camera_id: str):
    config = CAM_CONFIG.get(camera_id)
    if not config:
        return {"error": "Invalid camera ID"}
    
    if not os.path.exists(config["lanes"]) or not os.path.exists(config["slots"]):
        return {"error": "Config files missing for this camera"}
        
    with open(config["lanes"], "r") as f: lanes = json.load(f)
    with open(config["slots"], "r") as f: slots_data = json.load(f)
    
    slots = []
    for s in slots_data:
        pts = s["points"]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        slots.append({"slot_id": s["slot_id"], "center": [cx, cy]})
        
    return {
        "lanes": lanes, 
        "slots": slots,
        "image_name": config["image"]
    }

@router.get("/get-path/{camera_id}/{slot_id}")
def get_path(camera_id: str, slot_id: str):
    config = CAM_CONFIG.get(camera_id)
    if not config:
        return {"error": "Invalid camera ID"}
        
    if not os.path.exists(config["lanes"]) or not os.path.exists(config["slots"]):
        return {"error": "Config files missing"}
        
    with open(config["lanes"], "r") as f: lanes = json.load(f)
    with open(config["slots"], "r") as f: slots_data = json.load(f)
    
    target_slot = next((s for s in slots_data if s["slot_id"] == slot_id), None)
    if not target_slot: return {"error": "Slot not found"}
    s_pts = target_slot["points"]
    target_pos = [sum(p[0] for p in s_pts)/len(s_pts), sum(p[1] for p in s_pts)/len(s_pts)]
    
    nodes = lanes["nodes"].copy()
    edges = lanes["edges"].copy()
    entry_pos = lanes["entry"]

    # 1. Build Adjacency
    adj = {k: [] for k in nodes}
    for u, v in edges:
        if u in nodes and v in nodes:
            d = get_dist(nodes[u], nodes[v])
            adj[u].append((v, d))
            adj[v].append((u, d))

    start_node = "START"
    dest_node = "DEST"
    nodes[start_node] = entry_pos
    nodes[dest_node] = target_pos
    
    # 2. Entry Logic
    adj[start_node] = []
    if camera_id == "CAM_1":
        if "N0" in nodes:
            adj[start_node].append(("N0", get_dist(entry_pos, nodes["N0"])))
            adj["N0"].append((start_node, get_dist(entry_pos, nodes["N0"])))
    else:
        nearest_node = min([k for k in nodes.keys() if k not in [start_node, dest_node]], 
                          key=lambda k: get_dist(nodes[k], entry_pos))
        adj[start_node].append((nearest_node, get_dist(entry_pos, nodes[nearest_node])))
        adj[nearest_node].append((start_node, get_dist(entry_pos, nodes[nearest_node])))

    # 3. Target Logic
    adj[dest_node] = []
    possible_connectors = [k for k in nodes.keys() if k not in [start_node, dest_node]]
    
    if camera_id == "CAM_1" and slot_id == "P2" and "N7_P2" in nodes:
        nearest_node = "N7_P2"
    else:
        nearest_node = min(possible_connectors, key=lambda k: get_dist(nodes[k], target_pos))
    
    adj[dest_node].append((nearest_node, get_dist(nodes[nearest_node], target_pos)))
    adj[nearest_node].append((dest_node, get_dist(nodes[nearest_node], target_pos)))

    # 4. Dijkstra
    distances = {k: float('inf') for k in nodes}
    parents = {k: None for k in nodes}
    distances[start_node] = 0
    pq = [(0, start_node)]
    visited = set()
    while pq:
        pq.sort()
        d, u = pq.pop(0)
        if u in visited: continue
        visited.add(u)
        if u == dest_node: break
        for v, weight in adj.get(u, []):
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                parents[v] = u
                pq.append((distances[v], v))
                
    # 5. Reconstruct
    path_nodes = []
    path_coords = []
    if distances[dest_node] != float('inf'):
        curr = dest_node
        while curr:
            path_nodes.append(curr)
            path_coords.append(nodes[curr])
            curr = parents[curr]
        path_nodes.reverse()
        path_coords.reverse()
    else:
        path_coords = [entry_pos, target_pos]
        path_nodes = ["START", "DEST"]

    # 6. Generate Dynamic Instructions
    directions = generate_dynamic_instructions(path_coords, slot_id, camera_id)

    return {"path": path_coords, "instructions": directions}
