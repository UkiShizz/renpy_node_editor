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
    """
    Find starting blocks (those with no inputs), sorted by position (top to bottom, left to right).
    Если есть START блок, он всегда является единственным стартовым блоком.
    IMAGE and CHARACTER blocks are excluded from start_blocks even if they have no inputs,
    as they should be in the definitions section, not in the scene flow.
    """
    from renpy_node_editor.core.model import BlockType
    
    # Сначала ищем START блок - если он есть, он всегда является точкой входа
    start_block = next((b for b in scene.blocks if b.type == BlockType.START), None)
    if start_block:
        return [start_block]
    
    # Если нет START блока, используем старую логику
    has_input: Set[str] = set()
    for targets_with_dist in connections_map.values():
        # Extract block IDs from (block_id, distance) tuples
        has_input.update(block_id for block_id, _ in targets_with_dist)
    
    # Исключаем IMAGE и CHARACTER блоки из start_blocks
    # Они должны быть в секции определений, а не в начале сцены
    start_blocks = [
        b for b in scene.blocks 
        if b.id not in has_input and b.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START)
    ]
    
    # Если все блоки - IMAGE/CHARACTER, но есть соединения, 
    # нужно найти первый блок после них (например, SCENE)
    if not start_blocks and connections_map:
        # Находим блоки, которые подключены от IMAGE/CHARACTER
        image_char_ids = {
            b.id for b in scene.blocks 
            if b.type in (BlockType.IMAGE, BlockType.CHARACTER)
        }
        # Блоки, которые подключены от IMAGE/CHARACTER
        next_after_image_char = set()
        for block_id in image_char_ids:
            if block_id in connections_map:
                next_after_image_char.update(
                    target_id for target_id, _ in connections_map[block_id]
                )
        # Если есть такие блоки, используем их как start_blocks
        if next_after_image_char:
            start_blocks = [
                b for b in scene.blocks 
                if b.id in next_after_image_char and b.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START)
            ]
    
    if not connections_map:
        # Если нет соединений, возвращаем все блоки кроме IMAGE/CHARACTER/START
        return sorted(
            [b for b in scene.blocks if b.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START)],
            key=lambda b: (b.y, b.x)
        )
    
    # Sort start blocks by position (top to bottom, left to right)
    return sorted(start_blocks, key=lambda b: (b.y, b.x))


def get_reverse_connections(connections_map: Dict[str, List[Tuple[str, float]]]) -> Dict[str, Set[str]]:
    """
    Create reverse mapping: block_id -> set of block_ids that connect to it.
    This helps identify merge points (blocks that receive inputs from multiple sources).
    """
    reverse_map: Dict[str, Set[str]] = defaultdict(set)
    for from_block_id, targets_with_dist in connections_map.items():
        for to_block_id, _ in targets_with_dist:
            reverse_map[to_block_id].add(from_block_id)
    return reverse_map


def escape_text(text: str) -> str:
    """Escape quotes in text"""
    return text.replace('"', '\\"')


def topological_sort_blocks(
    scene: Scene,
    connections_map: Dict[str, List[Tuple[str, float]]],
    reverse_connections: Dict[str, Set[str]]
) -> List[str]:
    """
    Топологическая сортировка блоков для правильного порядка обработки.
    Возвращает список ID блоков в правильном порядке.
    При параллельных ветках сортирует по позиции (сверху вниз, слева направо).
    """
    from renpy_node_editor.core.model import BlockType
    
    # Исключаем IMAGE и CHARACTER блоки из сортировки
    block_ids = [
        block.id for block in scene.blocks
        if block.type not in (BlockType.IMAGE, BlockType.CHARACTER)
    ]
    
    # Создаем словарь для быстрого доступа к блокам
    block_map: Dict[str, Block] = {block.id: block for block in scene.blocks}
    
    # Вычисляем количество необработанных входов для каждого блока
    in_degree: Dict[str, int] = {}
    for block_id in block_ids:
        in_degree[block_id] = len(reverse_connections.get(block_id, set()))
    
    # Находим блоки без входов (стартовые блоки)
    queue: List[str] = [
        block_id for block_id in block_ids
        if in_degree[block_id] == 0
    ]
    
    # Функция для получения позиции блока
    def get_position(block_id: str) -> Tuple[float, float]:
        block = block_map.get(block_id)
        if block:
            return (block.y, block.x)
        return (0.0, 0.0)
    
    # Сортируем стартовые блоки по позиции (сверху вниз, слева направо)
    queue.sort(key=get_position)
    
    result: List[str] = []
    
    while queue:
        # Берем блок с наименьшей позицией
        current = queue.pop(0)
        result.append(current)
        
        # Обрабатываем все выходы этого блока
        # Сортируем выходы по позиции для правильного порядка параллельных веток
        next_blocks_with_dist = connections_map.get(current, [])
        next_blocks_sorted = sorted(
            next_blocks_with_dist,
            key=lambda x: get_position(x[0])
        )
        
        for next_id, _ in next_blocks_sorted:
            if next_id in block_ids:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)
                    # Сортируем очередь по позиции
                    queue.sort(key=get_position)
    
    return result


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
