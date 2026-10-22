from fastapi import APIRouter
from database import db
from fastapi.responses import JSONResponse
from typing import Any
import json
import os
import math
import time

# Custom Response for Pretty Printing
class PrettyJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")

router = APIRouter(tags=["Navigation"], default_response_class=PrettyJSONResponse)

# Configuration for different videos
def get_video_config(video_id: str):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT lanes_file, slots_file, image_file, latitude, longitude 
        FROM videos 
        WHERE video_id = ? AND is_active = 1
    """, (video_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            "lanes": row["lanes_file"],
            "slots": row["slots_file"],
            "image": row["image_file"],
            "latitude": row["latitude"],
            "longitude": row["longitude"]
        }
    return None

def get_dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def generate_dynamic_instructions(path_coords, slot_id, video_id):
    if len(path_coords) < 2:
        return ["🚩 Your vehicle is already at the destination."]

    instructions = []
    
    # 1. Opening Instruction (START)
    if video_id == "VID_1":
        instructions.append("🚗 **START**: Drive Right from the entrance gate.")
    else:
        instructions.append("🚗 **START**: Enter the parking area and follow the path.")

    # 2. Analyze Path for Turns (SKIP START AND END NODES)
    i = 0
    while i < len(path_coords) - 2:
        p1 = path_coords[i]
        p2 = path_coords[i+1]
        p3 = path_coords[i+2]
        
        # Vectors
        v1 = (p2[0]-p1[0], p2[1]-p1[1])
        v2 = (p3[0]-p2[0], p3[1]-p2[1])
        
        cp = v1[0]*v2[1] - v1[1]*v2[0]
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 > 0 and mag2 > 0:
            cos_theta = max(-1.0, min(1.0, dot / (mag1 * mag2)))
            angle = math.degrees(math.acos(cos_theta))
            
            if angle > 40: # Increased threshold to avoid micro-turns
                if cp > 0:
                    instructions.append("➡️ **TURN**: Take a **Sharp Right** following the lane.")
                else:
                    instructions.append("⬅️ **TURN**: Take a **Sharp Left** following the lane.")
                i += 1 
            else:
                # Occasional "Continue" prompts for long straights
                if i % 8 == 0 and i > 0:
                    instructions.append("⬆️ **DRIVE**: Continue straight along the parking row.")
        i += 1

    # 3. Final Arrival (STRICTLY ONCE)
    instructions.append(f"🏁 **ARRIVAL**: Reach the row and park in Slot **{slot_id}**.")
    return instructions

@router.get("/navigation-data/{video_id}")
def get_navigation_data(video_id: str):
    config = get_video_config(video_id)
    if not config:
        return {"error": "Invalid video ID or video not active"}
    
    if not os.path.exists(config["lanes"]) or not os.path.exists(config["slots"]):
        return {"error": "Config files missing for this video"}
        
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
        "image_name": config["image"],
        "geo_location": {
            "latitude": config["latitude"],
            "longitude": config["longitude"]
        }
    }

@router.get("/get-path/{video_id}/{slot_id}")
def get_path(video_id: str, slot_id: str):
    config = get_video_config(video_id)
    if not config:
        return {"error": "Invalid video ID"}
        
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
    if video_id == "VID_1":
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
    
    if video_id == "VID_1" and slot_id == "P2" and "N7_P2" in nodes:
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
    directions = generate_dynamic_instructions(path_coords, slot_id, video_id)

    return {"path": path_coords, "instructions": directions}

@router.post("/reserve-slot/{video_id}/{slot_id}")
def reserve_slot(video_id: str, slot_id: str, minutes: float = 30.0):
    conn = db()
    cur = conn.cursor()
    now = math.floor(time.time())
    
    # Check if already reserved or occupied
    cur.execute("SELECT status, is_reserved FROM slots WHERE video_id = ? AND slot_id = ?", (video_id, slot_id))
    row = cur.fetchone()
    if row and (row["status"] == "occupied" or row["is_reserved"] == 1):
        conn.close()
        return {"error": "Slot already occupied or reserved"}
        
    cur.execute("""
        UPDATE slots 
        SET is_reserved = 1, reserved_at = ?, status = 'reserved', last_seen = ?, reservation_timeout = ?
        WHERE video_id = ? AND slot_id = ?
    """, (now, now, minutes * 60, video_id, slot_id))
    
    conn.commit()
    conn.close()
    return {
        "message": f"Slot {slot_id} reserved successfully", 
        "reserved_at": now,
        "expires_in_minutes": float(minutes)
    }

@router.get("/check-reservation/{video_id}/{slot_id}")
def check_reservation(video_id: str, slot_id: str):
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT is_reserved, reserved_at, status FROM slots WHERE video_id = ? AND slot_id = ?", (video_id, slot_id))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        return {"status": "not_found"}
        
    return {
        "is_reserved": bool(row["is_reserved"]),
        "reserved_at": row["reserved_at"],
        "status": row["status"]
    }

@router.post("/cancel-reservation/{video_id}/{slot_id}")
def cancel_reservation(video_id: str, slot_id: str):
    """
    Cancels a reservation and immediately releases the slot back to FREE status.
    This makes the slot instantly available for LED dashboard and other users.
    """
    conn = db()
    cur = conn.cursor()
    now = time.time()
    
    # Check if slot exists and is actually reserved
    cur.execute("SELECT is_reserved, status FROM slots WHERE video_id = ? AND slot_id = ?", (video_id, slot_id))
    row = cur.fetchone()
    
    if not row:
        conn.close()
        return {"error": "Slot not found"}
    
    # Release the reservation - set back to FREE if it was reserved
    cur.execute("""
        UPDATE slots 
        SET is_reserved = 0, reserved_at = 0, reservation_timeout = 0, status = 'free', last_seen = ?
        WHERE video_id = ? AND slot_id = ? AND status != 'occupied'
    """, (now, video_id, slot_id))
    
    conn.commit()
    affected = cur.rowcount
    conn.close()
    
    if affected > 0:
        return {
            "message": f"Reservation for slot {slot_id} cancelled successfully",
            "slot_id": slot_id,
            "video_id": video_id,
            "new_status": "free"
        }
    else:
        return {
            "message": "Slot was already free or occupied",
            "slot_id": slot_id,
            "video_id": video_id
        }
