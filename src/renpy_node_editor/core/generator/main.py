"""Main Ren'Py code generator"""
from __future__ import annotations
import re

from typing import List, Dict, Set, Optional, Tuple
from renpy_node_editor.core.model import Project, Scene, Block, BlockType
from renpy_node_editor.core.generator.utils import (
    get_block_connections, find_start_blocks, get_reverse_connections,
    topological_sort_blocks, INDENT
)
from renpy_node_editor.core.generator.blocks import (
    generate_label, generate_if, generate_while, generate_for,
    BLOCK_GENERATORS, safe_get_str
)


def normalize_variable_name(name: str) -> str:
    """
    Нормализует имя переменной для Ren'Py.
    Имена должны начинаться с буквы или подчеркивания, не с цифры.
    Поддерживает кириллицу и другие Unicode символы.
    
    Args:
        name: Исходное имя
        
    Returns:
        Валидное имя переменной
    """
    if not name:
        return "var"
    
    # Заменяем пробелы и дефисы на подчеркивания
    normalized = name.replace(" ", "_").replace("-", "_")
    
    # Убираем только действительно недопустимые символы
    # Оставляем буквы (включая кириллицу), цифры и подчеркивания
    # Python/Ren'Py поддерживает Unicode в именах переменных
    normalized = re.sub(r'[^\w]', '_', normalized, flags=re.UNICODE)
    
    # Если начинается с цифры, добавляем префикс
    if normalized and normalized[0].isdigit():
        normalized = f"char_{normalized}"
    
    # Если пустое после обработки, используем дефолтное имя
    if not normalized:
        # Сохраняем исходное имя, заменяя только пробелы
        normalized = f"char_{name.replace(' ', '_')}" if name else "var"
        # Убираем недопустимые символы
        normalized = re.sub(r'[^\w]', '_', normalized, flags=re.UNICODE)
    
    # Убираем множественные подчеркивания
    normalized = re.sub(r'_+', '_', normalized)
    
    # Убираем подчеркивания в начале и конце
    normalized = normalized.strip('_')
    
    # Если все еще пустое или начинается с цифры, добавляем префикс
    if not normalized or (normalized and normalized[0].isdigit()):
        normalized = f"char_{normalized}" if normalized else "var"
    
    return normalized


def generate_block(block: Block, indent: str, char_name_map: Optional[Dict[str, str]] = None) -> str:
    """Generate code for a single block"""
    # START блок не генерирует код - это просто точка входа
    if block.type == BlockType.START:
        return ""
    
    # Special handling for blocks that need connection traversal
    if block.type in (BlockType.IF, BlockType.WHILE, BlockType.FOR):
        return ""  # Handled separately in chain generation
    
    generator = BLOCK_GENERATORS.get(block.type)
    if generator:
        # Для SAY блока всегда используем маппинг, если он передан
        if block.type == BlockType.SAY and char_name_map is not None:
            return generate_say_with_mapping(block, indent, char_name_map)
        return generator(block, indent)
    
    # Handle LABEL block
    if block.type == BlockType.LABEL:
        label = safe_get_str(block.params, "label")
        if label:
            return f"label {label}:\n"
    
    return ""


def generate_say_with_mapping(block: Block, indent: str, char_name_map: Dict[str, str]) -> str:
    """Generate SAY block with character name mapping"""
    from renpy_node_editor.core.generator.blocks import safe_get_str, escape_text
    
    who = safe_get_str(block.params, "who")
    text = safe_get_str(block.params, "text")
    
    if not text:
        return ""
    
    text = escape_text(text)
    
    attrs = []
    if who:
        # Используем нормализованное имя из маппинга, если нет - нормализуем на лету
        if who in char_name_map:
            normalized_who = char_name_map[who]
        else:
            # Если персонаж не в маппинге, нормализуем имя
            normalized_who = normalize_variable_name(who)
        
        expression = safe_get_str(block.params, "expression")
        if expression:
            normalized_who = f"{normalized_who} {expression}"
        
        at_pos = safe_get_str(block.params, "at")
        if at_pos:
            attrs.append(f"at {at_pos}")
        
        with_trans = safe_get_str(block.params, "with_transition")
        if with_trans:
            attrs.append(f"with {with_trans}")
        
        result = f"{indent}{normalized_who} \"{text}\""
        if attrs:
            result += " " + " ".join(attrs)
        return result + "\n"
    
    return f"{indent}\"{text}\"\n"


def generate_block_chain(
    scene: Scene,
    start_block_id: str,
    connections_map: Dict[str, List[Tuple[str, float]]],
    visited: Set[str],
    indent: str,
    char_name_map: Optional[Dict[str, str]] = None,
    reverse_connections: Optional[Dict[str, Set[str]]] = None,
    recursive: bool = True
) -> str:
    """
    Generate code for a block and optionally its chain.
    
    Args:
        recursive: If True, recursively processes connected blocks.
                  If False, only processes the current block.
        reverse_connections: Mapping from block_id to set of block_ids that connect to it.
                            Used to detect merge points (blocks that should wait for all inputs).
    """
    if start_block_id in visited:
        return ""  # Prevent cycles
    
    # Проверяем, все ли входы блока обработаны (для точек слияния)
    if reverse_connections:
        input_blocks = reverse_connections.get(start_block_id, set())
        if input_blocks:
            # Проверяем, все ли входные блоки обработаны
            if not all(inp_id in visited for inp_id in input_blocks):
                # Не все входы обработаны - пропускаем этот блок пока
                return ""
    
    visited.add(start_block_id)
    block = scene.find_block(start_block_id)
    if not block:
        return ""
    
    lines: List[str] = []
    
    # Generate code for current block
    if block.type == BlockType.IF:
        condition = safe_get_str(block.params, "condition")
        if condition:
            # Get connections sorted by distance
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            
            true_branch = ""
            false_branch = ""
            
            if len(next_blocks) >= 1:
                true_branch = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True
                )
            
            if len(next_blocks) >= 2:
                false_branch = generate_block_chain(
                    scene, next_blocks[1], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True
                )
            
            from renpy_node_editor.core.generator.blocks import generate_if
            lines.append(generate_if(block, indent, true_branch, false_branch))
    elif block.type == BlockType.WHILE:
        condition = safe_get_str(block.params, "condition")
        if condition:
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            loop_body = ""
            
            if next_blocks:
                loop_body = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True
                )
            
            from renpy_node_editor.core.generator.blocks import generate_while
            lines.append(generate_while(block, indent, loop_body))
    elif block.type == BlockType.FOR:
        var = safe_get_str(block.params, "variable")
        iterable = safe_get_str(block.params, "iterable")
        if var and iterable:
            next_blocks_with_dist = connections_map.get(block.id, [])
            next_blocks = [block_id for block_id, _ in next_blocks_with_dist]
            loop_body = ""
            
            if next_blocks:
                loop_body = generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True
                )
            
            from renpy_node_editor.core.generator.blocks import generate_for
            lines.append(generate_for(block, indent, loop_body))
    else:
        # IMAGE и CHARACTER блоки не генерируются в цепочке - они в секции определений
        if block.type in (BlockType.IMAGE, BlockType.CHARACTER):
            # Пропускаем генерацию, но продолжаем цепочку
            pass
        else:
            code = generate_block(block, indent, char_name_map)
            if code:
                lines.append(code)
        
        # Continue through connections only if recursive mode is enabled
        if recursive:
            # Continue through connections (already sorted by distance)
            # Process shorter connections first for parallel branches
            # ВАЖНО: используем то же множество visited, чтобы избежать дублирования
            next_blocks_with_dist = connections_map.get(block.id, [])
            
            # Обрабатываем все параллельные ветки последовательно
            # (в Ren'Py параллельные блоки выполняются последовательно в коде)
            for next_id, _ in next_blocks_with_dist:
                if next_id not in visited:
                    # Проверяем, все ли входы этого блока обработаны (для точек слияния)
                    if reverse_connections:
                        input_blocks = reverse_connections.get(next_id, set())
                        # Если есть несколько входов, проверяем, все ли обработаны
                        if len(input_blocks) > 1:
                            if not all(inp_id in visited for inp_id in input_blocks):
                                # Не все входы обработаны - пропускаем пока
                                # Этот блок будет обработан позже, когда все его входы будут готовы
                                continue
                    
                    next_code = generate_block_chain(
                        scene, next_id, connections_map, visited, indent, char_name_map, reverse_connections, recursive
                    )
                    if next_code:
                        lines.append(next_code)
    
    return "".join(lines)


def generate_scene(scene: Scene, char_name_map: Optional[Dict[str, str]] = None) -> str:
    """Generate code for a scene"""
    lines: List[str] = []
    
    lines.append(generate_label(scene))
    
    if not scene.blocks:
        lines.append(f"{INDENT}pass\n\n")
        return "".join(lines)
    
    connections_map = get_block_connections(scene)
    reverse_connections = get_reverse_connections(connections_map)
    start_blocks = find_start_blocks(scene, connections_map)
    
    if not start_blocks:
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            code = generate_block(block, indent, char_name_map)
            if code:
                lines.append(code)
    else:
        # Используем топологическую сортировку для правильного порядка обработки
        from renpy_node_editor.core.generator.utils import topological_sort_blocks
        
        # Получаем упорядоченный список блоков
        sorted_block_ids = topological_sort_blocks(scene, connections_map, reverse_connections)
        
        visited: Set[str] = set()
        
        # Обрабатываем блоки в топологическом порядке
        for block_id in sorted_block_ids:
            if block_id in visited:
                continue
            
            block = scene.find_block(block_id)
            if not block:
                continue
            
            # START блок не генерирует код, но обрабатывается для обхода графа
            if block.type == BlockType.START:
                visited.add(block_id)
                # Продолжаем обработку выходов START блока
                continue
            
            # Генерируем код для блока
            code = generate_block(block, INDENT, char_name_map)
            if code:
                lines.append(code)
            visited.add(block_id)
        
        # Обрабатываем блоки без соединений (если есть)
        for block in scene.blocks:
            if block.id not in visited and block.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START):
                code = generate_block(block, INDENT, char_name_map)
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
                who = safe_get_str(block.params, "who")
                if who:
                    characters.add(who)
            elif block.type in (BlockType.SHOW, BlockType.HIDE):
                char = safe_get_str(block.params, "character")
                if char:
                    characters.add(char)
            elif block.type == BlockType.CHARACTER:
                name = safe_get_str(block.params, "name")
                if name:
                    characters.add(name)
    
    return characters


def extract_image_blocks(project: Project) -> Dict[str, str]:
    """
    Извлекает все IMAGE блоки из всех сцен проекта.
    Возвращает словарь {имя: путь}
    """
    from renpy_node_editor.core.generator.blocks import safe_get_str
    
    images: Dict[str, str] = {}
    
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.IMAGE:
                name = safe_get_str(block.params, "name")
                path = safe_get_str(block.params, "path")
                if name and path:
                    # Нормализуем имя
                    normalized_name = normalize_variable_name(name)
                    images[normalized_name] = path
    
    return images


def generate_definitions(project: Project) -> str:
    """Generate global definitions (define, default, image)"""
    lines: List[str] = []
    
    # Image definitions - собираем из всех IMAGE блоков в сценах
    images = extract_image_blocks(project)
    if images:
        lines.append("# Image Definitions\n")
        for name, path in sorted(images.items()):
            lines.append(f"image {name} = \"{path}\"\n")
        lines.append("\n")
    
    # Также добавляем изображения из project.images (если есть)
    if project.images:
        for name, path in sorted(project.images.items()):
            if name not in images:  # Не дублируем
                lines.append(f"image {name} = \"{path}\"\n")
        if project.images and not images:
            lines.append("\n")
    
    # Character definitions
    if project.characters:
        lines.append("# Character Definitions\n")
        for name, char_data in sorted(project.characters.items()):
            # Нормализуем имя переменной (не может начинаться с цифры)
            normalized_name = normalize_variable_name(name)
            display_name = char_data.get("display_name", "")
            if display_name:
                display_name = display_name.replace("'", "\\'")
                lines.append(f"define {normalized_name} = Character('{display_name}')\n")
            else:
                lines.append(f"define {normalized_name} = Character(None)\n")
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
    
    # Создаем маппинг оригинальных имен на нормализованные
    char_name_map: Dict[str, str] = {}
    
    if characters:
        lines.append("# Characters (auto-detected)\n")
        for char in sorted(characters):
            # Check if already defined in project.characters
            if char not in project.characters:
                char_name = normalize_variable_name(char)
                char_name_map[char] = char_name
                lines.append(f"define {char_name} = Character('{char}')\n")
        lines.append("\n")
    elif not project.characters:
        lines.append("define narrator = Character('Narrator')\n\n")
    
    # Добавляем персонажей из project.characters в маппинг
    for name in project.characters.keys():
        normalized_name = normalize_variable_name(name)
        char_name_map[name] = normalized_name
    
    # Проверяем, есть ли метка start в сценах
    has_start_label = any(scene.label == "start" for scene in project.scenes)
    
    # Если нет метки start, создаем её в начале (после определений, перед сценами)
    # Это стандартная практика Ren'Py - метка start обычно идет в начале файла
    if not has_start_label and project.scenes:
        # Используем первую сцену как точку входа
        lines.append("\n# Main entry point\n")
        lines.append("label start:\n")
        first_scene = project.scenes[0]
        lines.append(f"    jump {first_scene.label}\n\n")
    elif not has_start_label:
        # Если вообще нет сцен, создаем пустую метку start
        lines.append("\n# Main entry point\n")
        lines.append("label start:\n")
        lines.append("    return\n\n")
    
    # Generate scenes
    for scene in project.scenes:
        lines.append(generate_scene(scene, char_name_map))
    
    return "".join(lines)
