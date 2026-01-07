"""Utility functions for code generation"""
from __future__ import annotations

from typing import Dict, List, Set, Tuple
from collections import defaultdict

from renpy_node_editor.core.model import Scene, Block

INDENT = "    "


def calculate_distance(block1: Block, block2: Block) -> float:
    """Calculate Euclidean distance between two blocks"""
    dx = block2.x - block1.x
    dy = block2.y - block1.y
    return (dx * dx + dy * dy) ** 0.5  # Faster than math.sqrt


def get_block_connections(scene: Scene) -> Dict[str, List[Tuple[str, float]]]:
    """
    Create mapping: block_id -> list of (next_block_id, distance) tuples
    Sorted by distance (shorter connections first for parallel branches)
    """
    connections_map: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    
    # Create port_id -> block_id mapping
    port_to_block: Dict[str, str] = {}
    for port in scene.ports:
        port_to_block[port.id] = port.node_id
    
    # Create block_id -> Block mapping
    block_map: Dict[str, Block] = {block.id: block for block in scene.blocks}
    
    # Process all connections with distance calculation
    for conn in scene.connections:
        from_block_id = port_to_block.get(conn.from_port_id)
        to_block_id = port_to_block.get(conn.to_port_id)
        
        if from_block_id and to_block_id:
            from_block = block_map.get(from_block_id)
            to_block = block_map.get(to_block_id)
            
            if from_block and to_block:
                distance = calculate_distance(from_block, to_block)
                connections_map[from_block_id].append((to_block_id, distance))
    
    # Sort connections by distance (shorter first) for parallel branches
    for block_id in connections_map:
        connections_map[block_id].sort(key=lambda x: x[1])
    
    return connections_map


def find_start_blocks(scene: Scene, connections_map: Dict[str, List[Tuple[str, float]]]) -> List[Block]:
    """Find starting blocks (those with no inputs), sorted by position (top to bottom, left to right)"""
    has_input: Set[str] = set()
    for targets_with_dist in connections_map.values():
        # Extract block IDs from (block_id, distance) tuples
        has_input.update(block_id for block_id, _ in targets_with_dist)
    
    start_blocks = [b for b in scene.blocks if b.id not in has_input]
    
    if not connections_map:
        return sorted(scene.blocks, key=lambda b: (b.y, b.x))
    
    # Sort start blocks by position (top to bottom, left to right)
    return sorted(start_blocks, key=lambda b: (b.y, b.x))


def escape_text(text: str) -> str:
    """Escape quotes in text"""
    return text.replace('"', '\\"')


def format_value(value: str) -> str:
    """Format value for Ren'Py code (detect type)"""
    if not value:
        return '""'
    
    # Try as number
    try:
        float(value)
        return value
    except ValueError:
        pass
    
    # Already quoted or list/dict
    if (value.startswith('"') and value.endswith('"')) or \
       value.startswith('[') or value.startswith('{'):
        return value
    
    # String
    return f'"{value}"'
