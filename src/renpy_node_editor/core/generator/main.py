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
    BLOCK_GENERATORS, safe_get_str, get_start_block_label
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


def generate_block(block: Block, indent: str, char_name_map: Optional[Dict[str, str]] = None, project_scenes: Optional[list] = None, generated_labels: Optional[Set[str]] = None, all_possible_labels: Optional[Set[str]] = None) -> str:
    """Generate code for a single block"""
    # START блок генерирует свой собственный label, на который могут ссылаться JUMP и CALL
    if block.type == BlockType.START:
        from renpy_node_editor.core.generator.blocks import generate_start
        return generate_start(block, indent, project_scenes)
    
    # Special handling for blocks that need connection traversal
    if block.type in (BlockType.IF, BlockType.WHILE, BlockType.FOR):
        return ""  # Handled separately in chain generation
    
    # JUMP и CALL блоки проверяют существование целевого label
    # Используем all_possible_labels для проверки (все label'ы, которые будут сгенерированы)
    if block.type == BlockType.JUMP:
        from renpy_node_editor.core.generator.blocks import generate_jump
        return generate_jump(block, indent, all_possible_labels)
    
    if block.type == BlockType.CALL:
        from renpy_node_editor.core.generator.blocks import generate_call
        return generate_call(block, indent, all_possible_labels)
    
    generator = BLOCK_GENERATORS.get(block.type)
    if generator:
        # Для SAY блока всегда используем маппинг, если он передан
        if block.type == BlockType.SAY and char_name_map is not None:
            return _generate_say_with_mapping(block, indent, char_name_map)
        return generator(block, indent)
    
    # Handle LABEL block
    if block.type == BlockType.LABEL:
        label = safe_get_str(block.params, "label")
        if label:
            return f"label {label}:\n"
    
    return ""


def _generate_say_with_mapping(block: Block, indent: str, char_name_map: Dict[str, str]) -> str:
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
    recursive: bool = True,
    project_scenes: Optional[list] = None,
    generated_labels: Optional[Set[str]] = None,
    all_possible_labels: Optional[Set[str]] = None
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
        if input_blocks and not all(inp_id in visited for inp_id in input_blocks):
            return ""  # Not all inputs processed yet
    
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
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes, generated_labels=generated_labels, all_possible_labels=all_possible_labels
                )
            
            if len(next_blocks) >= 2:
                false_branch = generate_block_chain(
                    scene, next_blocks[1], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes, generated_labels=generated_labels, all_possible_labels=all_possible_labels
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
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes, generated_labels=generated_labels, all_possible_labels=all_possible_labels
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
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT, char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes, generated_labels=generated_labels, all_possible_labels=all_possible_labels
                )
            
            from renpy_node_editor.core.generator.blocks import generate_for
            lines.append(generate_for(block, indent, loop_body))
    else:
        # IMAGE, CHARACTER, DEFINE и DEFAULT блоки не генерируются в цепочке - они в секции определений
        if block.type in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.DEFINE, BlockType.DEFAULT):
            # Пропускаем генерацию, но продолжаем цепочку
            pass
        elif block.type == BlockType.START:
            # START блоки генерируют jump/call если указан target_label
            code = generate_block(block, indent, char_name_map, project_scenes, generated_labels, all_possible_labels)
            if code:
                lines.append(code)
            # Продолжаем цепочку после START блока
        else:
            code = generate_block(block, indent, char_name_map, project_scenes, generated_labels, all_possible_labels)
            if code:
                lines.append(code)
        
        # Continue through connections only if recursive mode is enabled
        if recursive:
            next_blocks_with_dist = connections_map.get(block.id, [])
            if next_blocks_with_dist:
                def get_block_position(block_id: str) -> Tuple[float, float]:
                    b = scene.find_block(block_id)
                    return (b.y, b.x) if b else (0.0, 0.0)
                
                next_blocks_sorted = sorted(next_blocks_with_dist, key=lambda x: get_block_position(x[0]))
                
                if len(next_blocks_sorted) == 1:
                    # Sequential chain - process single output
                    next_id, _ = next_blocks_sorted[0]
                    if next_id not in visited:
                        next_code = generate_block_chain(
                            scene, next_id, connections_map, visited, indent, char_name_map, 
                            reverse_connections, recursive, project_scenes=project_scenes, 
                            generated_labels=generated_labels, all_possible_labels=all_possible_labels
                        )
                        if next_code:
                            lines.append(next_code)
                else:
                    # Parallel branches - process all in position order
                    for next_id, _ in next_blocks_sorted:
                        if next_id not in visited:
                            # Check if all inputs are processed (for merge points)
                            if reverse_connections:
                                input_blocks = reverse_connections.get(next_id, set())
                                if len(input_blocks) > 1 and not all(inp_id in visited for inp_id in input_blocks):
                                    continue  # Wait for all inputs
                            
                            next_code = generate_block_chain(
                                scene, next_id, connections_map, visited, indent, char_name_map,
                                reverse_connections, recursive, project_scenes=project_scenes,
                                generated_labels=generated_labels, all_possible_labels=all_possible_labels
                            )
                            if next_code:
                                lines.append(next_code)
    
    return "".join(lines)


def generate_scene(scene: Scene, char_name_map: Optional[Dict[str, str]] = None, project_scenes: Optional[list] = None, generated_labels: Optional[Set[str]] = None, all_possible_labels: Optional[Set[str]] = None) -> str:
    """Generate code for a scene"""
    if generated_labels is None:
        generated_labels = set()
    if all_possible_labels is None:
        all_possible_labels = set()
    
    lines: List[str] = []
    
    if not scene.blocks:
        # Пустая сцена - не генерируем метку сцены, только pass
        lines.append(f"pass\n\n")
        return "".join(lines)
    
    connections_map = get_block_connections(scene)
    reverse_connections = get_reverse_connections(connections_map)
    start_blocks = find_start_blocks(scene, connections_map)
    
    # Check if there are START blocks with labels
    has_start_blocks_with_labels = any(get_start_block_label(block) for block in start_blocks)
    
    # Метки сцен НЕ генерируются - только START блоки генерируют метки
    # Поэтому не добавляем generate_label(scene) нигде
    
    if not start_blocks:
        # Нет START блоков - генерируем все блоки с отступом
        # Но если это первая сцена и нет label start, нужно создать его
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            # Пропускаем IMAGE, CHARACTER, DEFINE и DEFAULT блоки - они в секции определений
            if block.type in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.DEFINE, BlockType.DEFAULT):
                continue
            code = generate_block(block, indent, char_name_map, project_scenes, generated_labels, all_possible_labels)
            if code:
                lines.append(code)
    else:
        # Сначала нумеруем все блоки в порядке обработки с учетом параллельности
        # block_order: block_id -> (level, sublevel) где level - основной уровень, sublevel - для параллельных веток
        block_order: Dict[str, Tuple[int, float]] = {}
        visited_for_numbering: Set[str] = set()
        current_level = 0
        
        def number_blocks_recursive(block_id: str, level: int, sublevel: float = 0.0) -> None:
            """Нумерует блоки в порядке обработки"""
            if block_id in visited_for_numbering:
                return
            
            block = scene.find_block(block_id)
            if not block:
                return
            
            # Проверяем, все ли входы обработаны (для точек слияния)
            if reverse_connections:
                input_blocks = reverse_connections.get(block_id, set())
                if input_blocks:
                    if not all(inp_id in visited_for_numbering for inp_id in input_blocks):
                        return
            
            # Присваиваем номер
            block_order[block_id] = (level, sublevel)
            visited_for_numbering.add(block_id)
            
            # Получаем выходы этого блока
            next_blocks_with_dist = connections_map.get(block_id, [])
            
            if len(next_blocks_with_dist) > 1:
                # Это разветвление - все параллельные ветки получают одинаковый level, но разные sublevel
                next_blocks_sorted = sorted(
                    next_blocks_with_dist,
                    key=lambda x: (
                        next((b.y for b in scene.blocks if b.id == x[0]), 0),
                        next((b.x for b in scene.blocks if b.id == x[0]), 0)
                    )
                )
                
                # Нумеруем все параллельные ветки полностью до точки слияния
                for idx, (next_id, _) in enumerate(next_blocks_sorted):
                    if next_id not in visited_for_numbering:
                        number_chain_until_merge(next_id, level + 1, float(idx) / 1000.0)
            elif len(next_blocks_with_dist) == 1:
                # Один выход - продолжаем с тем же level
                next_id = next_blocks_with_dist[0][0]
                if next_id not in visited_for_numbering:
                    number_blocks_recursive(next_id, level, sublevel)
        
        def number_chain_until_merge(block_id: str, level: int, sublevel: float) -> None:
            """Нумерует цепочку блоков до точки слияния или разветвления"""
            current_id = block_id
            current_sublevel = sublevel
            
            while current_id and current_id not in visited_for_numbering:
                # Проверяем, все ли входы обработаны (для точек слияния)
                if reverse_connections:
                    input_blocks = reverse_connections.get(current_id, set())
                    if input_blocks:
                        if not all(inp_id in visited_for_numbering for inp_id in input_blocks):
                            return
                
                block = scene.find_block(current_id)
                if not block:
                    break
                
                # Присваиваем номер
                block_order[current_id] = (level, current_sublevel)
                visited_for_numbering.add(current_id)
                
                # Получаем выходы этого блока
                next_blocks_with_dist = connections_map.get(current_id, [])
                
                if len(next_blocks_with_dist) > 1:
                    # Это разветвление - обрабатываем все параллельные ветки
                    next_blocks_sorted = sorted(
                        next_blocks_with_dist,
                        key=lambda x: (
                            next((b.y for b in scene.blocks if b.id == x[0]), 0),
                            next((b.x for b in scene.blocks if b.id == x[0]), 0)
                        )
                    )
                    
                    for idx, (next_id, _) in enumerate(next_blocks_sorted):
                        if next_id not in visited_for_numbering:
                            number_chain_until_merge(next_id, level + 1, float(idx) / 1000.0)
                    break
                elif len(next_blocks_with_dist) == 1:
                    # Один выход - проверяем, не является ли он точкой слияния
                    next_id = next_blocks_with_dist[0][0]
                    if reverse_connections:
                        next_inputs = reverse_connections.get(next_id, set())
                        if len(next_inputs) > 1:
                            # Следующий блок - точка слияния, останавливаемся здесь
                            break
                    level += 1
                    current_id = next_id
                else:
                    break
        
        # Нумеруем все стартовые блоки
        for start_block in start_blocks:
            if start_block.id not in visited_for_numbering:
                number_blocks_recursive(start_block.id, 0, 0.0)
        
        # Многопроходная нумерация для оставшихся блоков (точки слияния)
        max_iterations = len(scene.blocks) * 3
        for iteration in range(max_iterations):
            progress_made = False
            
            blocks_sorted = sorted(
                scene.blocks,
                key=lambda b: (b.y, b.x)
            )
            
            for block in blocks_sorted:
                if block.id not in visited_for_numbering and block.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.DEFINE, BlockType.DEFAULT, BlockType.START):
                    if reverse_connections:
                        input_blocks = reverse_connections.get(block.id, set())
                        if input_blocks:
                            if not all(inp_id in visited_for_numbering for inp_id in input_blocks):
                                continue
                    
                    # Находим максимальный level среди входов
                    max_input_level = 0
                    if reverse_connections:
                        input_blocks = reverse_connections.get(block.id, set())
                        for inp_id in input_blocks:
                            if inp_id in block_order:
                                max_input_level = max(max_input_level, block_order[inp_id][0])
                    
                    number_blocks_recursive(block.id, max_input_level + 1, 0.0)
                    progress_made = True
            
            if not progress_made:
                break
        
        # Теперь генерируем код в порядке номеров
        # Сортируем блоки по (level, sublevel)
        blocks_to_generate = [
            (block_id, level, sublevel)
            for block_id, (level, sublevel) in block_order.items()
        ]
        blocks_to_generate.sort(key=lambda x: (x[1], x[2]))  # Сортируем по level, затем sublevel
        
        visited: Set[str] = set()
        
        # Generate blocks in numbered order
        for block_id, _, _ in blocks_to_generate:
            if block_id in visited:
                continue
            
            block = scene.find_block(block_id)
            if not block or block.type in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.DEFINE, BlockType.DEFAULT):
                continue
            
            indent = "" if block.type == BlockType.START else INDENT
            
            if block.type == BlockType.START:
                start_label = get_start_block_label(block)
                if start_label:
                    code = generate_block(block, indent, char_name_map, project_scenes, generated_labels, all_possible_labels)
                    if code:
                        lines.append(code)
                        generated_labels.add(start_label)
                    visited.add(block_id)
                    continue
            
            if block.type in (BlockType.IF, BlockType.WHILE, BlockType.FOR):
                code = generate_block_chain(
                    scene, block_id, connections_map, visited, indent,
                    char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes,
                    generated_labels=generated_labels, all_possible_labels=all_possible_labels
                )
                if code:
                    lines.append(code)
            else:
                code = generate_block(block, indent, char_name_map, project_scenes, generated_labels, all_possible_labels)
                if code:
                    lines.append(code)
            
            visited.add(block_id)
        
        # Process unconnected blocks
        for block in scene.blocks:
            if block.id in visited or block.type in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.DEFINE, BlockType.DEFAULT):
                continue
            
            if block.type == BlockType.START:
                start_label = get_start_block_label(block)
                if start_label:
                    code = generate_block(block, "", char_name_map, project_scenes, generated_labels, all_possible_labels)
                    if code:
                        lines.append(code)
                        if start_label not in generated_labels:
                            generated_labels.add(start_label)
            else:
                code = generate_block(block, INDENT, char_name_map, project_scenes, generated_labels, all_possible_labels)
                if code:
                    lines.append(code)
    lines.append("\n")
    return "".join(lines)


def extract_characters(project: Project) -> Set[str]:
    """Extract all characters from project"""
    characters = set(project.characters.keys())
    
    # Extract from blocks
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.SAY:
                if who := safe_get_str(block.params, "who"):
                    characters.add(who)
            elif block.type in (BlockType.SHOW, BlockType.HIDE):
                if char := safe_get_str(block.params, "character"):
                    characters.add(char)
            elif block.type == BlockType.CHARACTER:
                if name := safe_get_str(block.params, "name"):
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


def extract_background_images(project: Project) -> Dict[str, str]:
    """
    Извлекает изображения, используемые в SCENE блоках как background.
    Возвращает словарь {имя: путь} для изображений, которые нужно определить.
    """
    from renpy_node_editor.core.generator.blocks import safe_get_str
    from pathlib import Path
    
    backgrounds: Dict[str, str] = {}
    
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.SCENE:
                bg = safe_get_str(block.params, "background", "")
                if bg and bg not in ("black", "white"):
                    # Это не стандартный фон - может быть изображение
                    # Если это выглядит как имя изображения (содержит пробел или начинается с "bg"),
                    # но не определено, нужно попытаться найти путь
                    # Пока просто сохраняем имя, путь будет определен позже
                    if bg not in backgrounds:
                        # Пытаемся найти путь из IMAGE блоков
                        found_path = None
                        for scene2 in project.scenes:
                            for block2 in scene2.blocks:
                                if block2.type == BlockType.IMAGE:
                                    name = safe_get_str(block2.params, "name")
                                    if name == bg:
                                        found_path = safe_get_str(block2.params, "path")
                                        break
                            if found_path:
                                break
                        
                        if found_path:
                            backgrounds[bg] = found_path
                        # Если путь не найден, не добавляем - пользователь должен определить изображение сам
    
    return backgrounds


def generate_definitions(project: Project) -> str:
    """Generate global definitions (define, default, image)"""
    from renpy_node_editor.core.generator.blocks import safe_get_str
    from renpy_node_editor.core.model import BlockType
    
    lines: List[str] = []
    
    # Image definitions - собираем из всех IMAGE блоков в сценах
    images = extract_image_blocks(project)
    
    # Также добавляем изображения из project.images (если есть)
    if project.images:
        for name, path in sorted(project.images.items()):
            if name not in images:  # Не дублируем
                images[name] = path
    
    # Извлекаем изображения, используемые в SCENE блоках
    background_images = extract_background_images(project)
    for name, path in background_images.items():
        if name not in images:  # Не дублируем
            images[name] = path
    
    if images:
        lines.append("# Image Definitions\n")
        for name, path in sorted(images.items()):
            lines.append(f"image {name} = \"{path}\"\n")
        lines.append("\n")
    
    # Character definitions из project.characters
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
    
    # Character definitions из CHARACTER блоков (если не определены в project.characters)
    from renpy_node_editor.core.generator.blocks import generate_character
    character_blocks_processed = set()
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.CHARACTER:
                name = safe_get_str(block.params, "name")
                if name and name not in project.characters and name not in character_blocks_processed:
                    character_blocks_processed.add(name)
                    char_code = generate_character(block, "")
                    if char_code:
                        if not project.characters and not lines:  # Добавляем заголовок только если его еще нет
                            lines.append("# Character Definitions (from blocks)\n")
                        lines.append(char_code)
    
    if character_blocks_processed:
        lines.append("\n")
    
    # DEFINE и DEFAULT блоки - генерируем в секции определений
    from renpy_node_editor.core.generator.blocks import generate_define, generate_default
    define_blocks_processed = set()
    default_blocks_processed = set()
    
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.DEFINE:
                name = safe_get_str(block.params, "name")
                if name and name not in define_blocks_processed:
                    define_blocks_processed.add(name)
                    define_code = generate_define(block, "")
                    if define_code:
                        if not lines or (not any("#" in line and "define" in line.lower() for line in lines[-5:])):
                            lines.append("# Define Statements\n")
                        lines.append(define_code)
            elif block.type == BlockType.DEFAULT:
                name = safe_get_str(block.params, "name")
                if name and name not in default_blocks_processed:
                    default_blocks_processed.add(name)
                    default_code = generate_default(block, "")
                    if default_code:
                        if not lines or (not any("#" in line and "default" in line.lower() for line in lines[-5:])):
                            lines.append("# Default Statements\n")
                        lines.append(default_code)
    
    if define_blocks_processed or default_blocks_processed:
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
    
    # Собираем имена персонажей, которые уже определены в CHARACTER блоках
    # (чтобы не дублировать их в автодетекции)
    character_blocks_names = set()
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.CHARACTER:
                name = safe_get_str(block.params, "name")
                if name:
                    character_blocks_names.add(name)
    
    # Собираем display_name из CHARACTER блоков для автодетектированных персонажей
    character_display_names: Dict[str, str] = {}
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.CHARACTER:
                name = safe_get_str(block.params, "name")
                display_name = safe_get_str(block.params, "display_name")
                if name and display_name:
                    character_display_names[name] = display_name
    
    # Генерируем определения только для персонажей, которые:
    # 1. Не определены в project.characters
    # 2. Не определены в CHARACTER блоках (чтобы избежать дублирования)
    if characters:
        auto_detected = []
        for char in sorted(characters):
            # Пропускаем персонажей, которые уже определены
            if char not in project.characters and char not in character_blocks_names:
                char_name = normalize_variable_name(char)
                char_name_map[char] = char_name
                # Используем display_name из CHARACTER блока, если есть
                display_name = character_display_names.get(char, char)
                if display_name:
                    display_name = display_name.replace("'", "\\'")
                    auto_detected.append(f"define {char_name} = Character('{display_name}')\n")
                else:
                    auto_detected.append(f"define {char_name} = Character('{char}')\n")
        
        if auto_detected:
            lines.append("# Characters (auto-detected)\n")
            lines.extend(auto_detected)
            lines.append("\n")
    elif not project.characters and not character_blocks_names:
        lines.append("define narrator = Character('Narrator')\n\n")
    
    # Добавляем персонажей из project.characters в маппинг
    for name in project.characters.keys():
        normalized_name = normalize_variable_name(name)
        char_name_map[name] = normalized_name
    
    # Добавляем персонажей из CHARACTER блоков в маппинг (если еще не добавлены)
    for name in character_blocks_names:
        if name not in char_name_map:
            normalized_name = normalize_variable_name(name)
            char_name_map[name] = normalized_name
    
    # Собираем все метки, которые будут сгенерированы, чтобы избежать дубликатов
    generated_labels: Set[str] = set()
    
    # Собираем все возможные метки из START и LABEL блоков для проверки JUMP/CALL
    # НЕ добавляем их в generated_labels заранее - они будут добавлены при генерации
    all_possible_labels: Set[str] = set()
    # BlockType и safe_get_str уже импортированы в начале файла
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type == BlockType.START:
                start_label = safe_get_str(block.params, "label", "") or safe_get_str(block.params, "Имя метки (label):", "")
                if start_label:
                    all_possible_labels.add(start_label)
            elif block.type == BlockType.LABEL:
                label = safe_get_str(block.params, "label", "")
                if label:
                    all_possible_labels.add(label)
    
    
    # Всегда создаем label start: в начале (после определений, перед сценами)
    # Это стандартная практика Ren'Py - метка start обязательна как точка входа в игру
    # label start: создается ОДИН РАЗ в начале, return - ОДИН РАЗ в конце
    lines.append("\n# Игра начинается здесь:\n")
    lines.append("label start:\n")
    
    # Если есть START блоки, делаем jump к первому
    if all_possible_labels:
        # Находим первый START блок с label
        first_start_label = None
        for scene in project.scenes:
            for block in scene.blocks:
                if block.type == BlockType.START:
                    start_label = safe_get_str(block.params, "label", "") or safe_get_str(block.params, "Имя метки (label):", "")
                    if start_label:
                        first_start_label = start_label
                        break
            if first_start_label:
                break
        
        if first_start_label:
            lines.append(f"    jump {first_start_label}\n")
        else:
            lines.append("    return\n")
    else:
        # Нет START блоков - просто return
        lines.append("    return\n")
    
    generated_labels.add("start")
    
    # Generate scenes in the same order as they appear in the scenes list
    # Порядок генерации соответствует порядку сцен в списке
    # Передаем all_possible_labels для проверки JUMP/CALL
    for scene in project.scenes:
        scene_code = generate_scene(scene, char_name_map, project.scenes, generated_labels, all_possible_labels)
        lines.append(scene_code)
    
    return "".join(lines)
