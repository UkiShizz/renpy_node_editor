"""Main Ren'Py code generator"""
from __future__ import annotations

from typing import List, Dict, Set, Optional, Tuple
from renpy_node_editor.core.model import Project, Scene, Block, BlockType
from renpy_node_editor.core.generator.utils import (
    get_block_connections, find_start_blocks, INDENT
)
from renpy_node_editor.core.generator.blocks import (
    generate_label, generate_if, generate_while, generate_for,
    BLOCK_GENERATORS
)


def generate_block(block: Block, indent: str) -> str:
    """Generate code for a single block"""
    # Special handling for blocks that need connection traversal
    if block.type in (BlockType.IF, BlockType.WHILE, BlockType.FOR):
        return ""  # Handled separately in chain generation
    
    generator = BLOCK_GENERATORS.get(block.type)
    if generator:
        return generator(block, indent)
    
    # Handle LABEL block
    if block.type == BlockType.LABEL:
        label = block.params.get("label", "").strip()
        if label:
            return f"label {label}:\n"
    
    return ""


def generate_block_chain(
    scene: Scene,
    start_block_id: str,
    connections_map: Dict[str, List[Tuple[str, float]]],
    visited: Set[str],
    indent: str
) -> str:
    """
    Recursively generate chain of blocks.
    For parallel connections, processes shorter connections first.
    """
    if start_block_id in visited:
        return ""  # Prevent cycles
    
    visited.add(start_block_id)
    block = scene.find_block(start_block_id)
    if not block:
        return ""
    
    lines: List[str] = []
    
    # Generate code for current block
    if block.type == BlockType.IF:
        condition = block.params.get("condition", "").strip()
        if condition:
            # Get connections sorted by distance
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            
            true_branch = ""
            false_branch = ""
            
            if len(next_blocks) >= 1:
                true_branch = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            if len(next_blocks) >= 2:
                false_branch = generate_block_chain(
                    scene, next_blocks[1], connections_map, visited.copy(), indent + INDENT
                )
            
            from renpy_node_editor.core.generator.blocks import generate_if
            lines.append(generate_if(block, indent, true_branch, false_branch))
    elif block.type == BlockType.WHILE:
        condition = block.params.get("condition", "").strip()
        if condition:
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            loop_body = ""
            
            if next_blocks:
                loop_body = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            from renpy_node_editor.core.generator.blocks import generate_while
            lines.append(generate_while(block, indent, loop_body))
    elif block.type == BlockType.FOR:
        var = block.params.get("variable", "").strip()
        iterable = block.params.get("iterable", "").strip()
        if var and iterable:
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            loop_body = ""
            
            if next_blocks:
                loop_body = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            from renpy_node_editor.core.generator.blocks import generate_for
            lines.append(generate_for(block, indent, loop_body))
    else:
        code = generate_block(block, indent)
        if code:
            lines.append(code)
        
        # Continue through connections (already sorted by distance)
        # Process shorter connections first for parallel branches
        next_blocks_with_dist = connections_map.get(block.id, [])
        for next_id, _ in next_blocks_with_dist:
            if next_id not in visited:
                next_code = generate_block_chain(
                    scene, next_id, connections_map, visited.copy(), indent
                )
                if next_code:
                    lines.append(next_code)
    
    return "".join(lines)


def generate_scene(scene: Scene) -> str:
    """Generate code for a scene"""
    lines: List[str] = []
    
    lines.append(generate_label(scene))
    
    if not scene.blocks:
        lines.append(f"{INDENT}pass\n\n")
        return "".join(lines)
    
    connections_map = get_block_connections(scene)
    start_blocks = find_start_blocks(scene, connections_map)
    
    if not start_blocks:
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            code = generate_block(block, indent)
            if code:
                lines.append(code)
    else:
        visited: Set[str] = set()
        for start_block in start_blocks:
            code = generate_block_chain(
                scene, start_block.id, connections_map, visited.copy(), INDENT
            )
            if code:
                lines.append(code)
        
        # Add unprocessed blocks
        processed = set()
        for start_block in start_blocks:
            processed.add(start_block.id)
            stack = [start_block.id]
            while stack:
                current_id = stack.pop()
                # Extract block IDs from (block_id, distance) tuples
                next_blocks_with_dist = connections_map.get(current_id, [])
                for next_id, _ in next_blocks_with_dist:
                    if next_id not in processed:
                        processed.add(next_id)
                        stack.append(next_id)
        
        for block in scene.blocks:
            if block.id not in processed:
                code = generate_block(block, INDENT)
                if code:
                    lines.append(code)
    
    lines.append("\n")
    return "".join(lines)


def extract_characters(project: Project) -> Set[str]:
    """Extract all characters from project"""
    characters: Set[str] = set()
    
    # Add from global definitions
    for char_name in project.characters.keys():
        characters.add(char_name)
    
    # Extract from blocks
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.SAY:
                who = block.params.get("who", "").strip()
                if who:
                    characters.add(who)
            elif block.type in (BlockType.SHOW, BlockType.HIDE):
                char = block.params.get("character", "").strip()
                if char:
                    characters.add(char)
            elif block.type == BlockType.CHARACTER:
                name = block.params.get("name", "").strip()
                if name:
                    characters.add(name)
    
    return characters


def generate_definitions(project: Project) -> str:
    """Generate global definitions (define, default, image)"""
    lines: List[str] = []
    
    # Image definitions
    if project.images:
        lines.append("# Image Definitions\n")
        for name, path in sorted(project.images.items()):
            lines.append(f"image {name} = \"{path}\"\n")
        lines.append("\n")
    
    # Character definitions
    if project.characters:
        lines.append("# Character Definitions\n")
        for name, char_data in sorted(project.characters.items()):
            display_name = char_data.get("display_name", "")
            if display_name:
                display_name = display_name.replace("'", "\\'")
                lines.append(f"define {name} = Character('{display_name}')\n")
            else:
                lines.append(f"define {name} = Character(None)\n")
        lines.append("\n")
    
    return "".join(lines)


def generate_renpy_script(project: Project) -> str:
    """Generate full Ren'Py script for project"""
    lines: List[str] = []
    
    # Header
    lines.append("# Generated by RenPy Node Editor\n")
    lines.append("# This file is auto-generated. Do not edit manually.\n\n")
    
    # Global definitions
    def_lines = generate_definitions(project)
    if def_lines:
        lines.append(def_lines)
    
    # Extract characters and create define
    characters = extract_characters(project)
    if characters:
        lines.append("# Characters (auto-detected)\n")
        for char in sorted(characters):
            # Check if already defined in project.characters
            if char not in project.characters:
                char_name = char.replace(" ", "_").replace("-", "_")
                lines.append(f"define {char_name} = Character('{char}')\n")
        lines.append("\n")
    elif not project.characters:
        # Default narrator
        lines.append("define narrator = Character('Narrator')\n\n")
    
    # Generate scenes
    for scene in project.scenes:
        lines.append(generate_scene(scene))
    
    return "".join(lines)
