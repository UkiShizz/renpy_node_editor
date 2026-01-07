"""Utility functions for code generation"""
from __future__ import annotations

from typing import Dict, List, Set
from collections import defaultdict

from renpy_node_editor.core.model import Scene, Block, Connection, Port

INDENT = "    "


def get_block_connections(scene: Scene) -> Dict[str, List[str]]:
    """Create mapping: block_id -> list of next block_ids by connections"""
    connections_map: Dict[str, List[str]] = defaultdict(list)
    
    # Create port_id -> block_id mapping
    port_to_block: Dict[str, str] = {}
    for port in scene.ports:
        port_to_block[port.id] = port.node_id
    
    # Process all connections
    for conn in scene.connections:
        from_block = port_to_block.get(conn.from_port_id)
        to_block = port_to_block.get(conn.to_port_id)
        if from_block and to_block:
            connections_map[from_block].append(to_block)
    
    return connections_map


def find_start_blocks(scene: Scene, connections_map: Dict[str, List[str]]) -> List[Block]:
    """Find starting blocks (those with no inputs)"""
    has_input: Set[str] = set()
    for targets in connections_map.values():
        has_input.update(targets)
    
    start_blocks = [b for b in scene.blocks if b.id not in has_input]
    
    if not connections_map:
        return sorted(scene.blocks, key=lambda b: (b.y, b.x))
    
    return start_blocks


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
