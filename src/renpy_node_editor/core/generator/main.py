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
    
    print(f"DEBUG generate_say_with_mapping: Блок {block.id}, who='{who}', text='{text}', params keys: {list(block.params.keys())}")
    
    if not text:
        print(f"DEBUG generate_say_with_mapping: Текст пустой, возвращаем пустую строку")
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
        print(f"DEBUG generate_block_chain: Блок {start_block_id} уже в visited, пропускаем")
        return ""  # Prevent cycles
    
    # Проверяем, все ли входы блока обработаны (для точек слияния)
    if reverse_connections:
        input_blocks = reverse_connections.get(start_block_id, set())
        if input_blocks:
            # Проверяем, все ли входные блоки обработаны
            if not all(inp_id in visited for inp_id in input_blocks):
                # Не все входы обработаны - пропускаем этот блок пока
                print(f"DEBUG generate_block_chain: Блок {start_block_id} имеет необработанные входы: {input_blocks - visited}")
                return ""
    
    visited.add(start_block_id)
    block = scene.find_block(start_block_id)
    if not block:
        print(f"DEBUG generate_block_chain: Блок {start_block_id} не найден в сцене")
        return ""
    
    print(f"DEBUG generate_block_chain: Обработка блока {start_block_id} типа {block.type}")
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
        # IMAGE и CHARACTER блоки не генерируются в цепочке - они в секции определений
        if block.type in (BlockType.IMAGE, BlockType.CHARACTER):
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
            print(f"DEBUG generate_block_chain: Сгенерированный код для блока {start_block_id} типа {block.type}: {repr(code[:100]) if code else 'пусто'}")
            if code:
                lines.append(code)
        
        # Continue through connections only if recursive mode is enabled
        if recursive:
            print(f"DEBUG generate_block_chain: Рекурсивный режим включен, обрабатываем связи блока {start_block_id}")
            # Continue through connections (already sorted by distance)
            # Обрабатываем все выходы в порядке расстояния (ближайшие первыми)
            # Это правильно для параллельных веток - они выполняются последовательно в коде
            next_blocks_with_dist = connections_map.get(block.id, [])
            
            # Обрабатываем все выходы последовательно (в порядке расстояния)
            for next_id, dist in next_blocks_with_dist:
                if next_id not in visited:
                    # Проверяем, все ли входы этого блока обработаны (для точек слияния)
                    if reverse_connections:
                        input_blocks = reverse_connections.get(next_id, set())
                        # Если есть несколько входов, проверяем, все ли обработаны
                        if len(input_blocks) > 1:
                            if not all(inp_id in visited for inp_id in input_blocks):
                                # Не все входы обработаны - пропускаем пока
                                # Этот блок будет обработан позже, когда все его входы будут готовы
                                print(f"DEBUG generate_block_chain: Блок {next_id} имеет необработанные входы: {input_blocks - visited}, пропускаем")
                                continue
                    
                    print(f"DEBUG generate_block_chain: Обрабатываем выход блока {start_block_id}: {next_id} (расстояние: {dist})")
                    next_code = generate_block_chain(
                        scene, next_id, connections_map, visited, indent, char_name_map, reverse_connections, recursive, project_scenes=project_scenes, generated_labels=generated_labels, all_possible_labels=all_possible_labels
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
    
    # Отладочный вывод
    print(f"DEBUG generate_scene: Сцена {scene.name}")
    print(f"  Всего блоков в сцене: {len(scene.blocks)}")
    print(f"  START блоков найдено: {len(start_blocks)}")
    for sb in start_blocks:
        from renpy_node_editor.core.generator.blocks import safe_get_str
        label = safe_get_str(sb.params, "label", "") or safe_get_str(sb.params, "Имя метки (label):", "")
        print(f"  START блок {sb.id}: label='{label}', params keys: {list(sb.params.keys())}, params={sb.params}")
    
    # Проверяем все блоки типа START в сцене
    from renpy_node_editor.core.model import BlockType
    all_start_blocks = [b for b in scene.blocks if b.type == BlockType.START]
    print(f"  Всего START блоков в сцене (прямой поиск): {len(all_start_blocks)}")
    for sb in all_start_blocks:
        from renpy_node_editor.core.generator.blocks import safe_get_str
        label = safe_get_str(sb.params, "label", "") or safe_get_str(sb.params, "Имя метки (label):", "")
        print(f"    START блок {sb.id}: label='{label}', params keys: {list(sb.params.keys())}")
    
    # Проверяем, есть ли START блоки с label
    has_start_blocks_with_labels = False
    if start_blocks:
        from renpy_node_editor.core.generator.blocks import safe_get_str
        for start_block in start_blocks:
            start_label = safe_get_str(start_block.params, "label", "") or safe_get_str(start_block.params, "Имя метки (label):", "")
            if start_label:
                has_start_blocks_with_labels = True
                break
    
    # Метки сцен НЕ генерируются - только START блоки генерируют метки
    # Поэтому не добавляем generate_label(scene) нигде
    
    if not start_blocks:
        # Нет START блоков - генерируем все блоки с отступом
        # Но если это первая сцена и нет label start, нужно создать его
        print(f"DEBUG: Нет START блоков в сцене {scene.name}, генерируем все блоки")
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            # Пропускаем IMAGE и CHARACTER блоки - они в секции определений
            if block.type in (BlockType.IMAGE, BlockType.CHARACTER):
                continue
            print(f"DEBUG: Генерация блока {block.id} типа {block.type}")
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
                if block.id not in visited_for_numbering and block.type not in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START):
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
        
        # Генерируем START блоки и их цепочки
        print(f"DEBUG: Генерация START блоков. Найдено: {len(start_blocks)}, visited: {len(visited)}")
        for start_block in start_blocks:
            print(f"DEBUG: Обработка START блока {start_block.id}, visited: {start_block.id in visited}")
            if start_block.id in visited:
                continue
            
            # Пробуем разные варианты ключей для label
            from renpy_node_editor.core.generator.blocks import safe_get_str
            start_label = safe_get_str(start_block.params, "label", "") or safe_get_str(start_block.params, "Имя метки (label):", "")
            print(f"DEBUG: START блок {start_block.id}, label='{start_label}', params keys: {list(start_block.params.keys())}")
            # Если у START блока нет label'а, пропускаем его, но все равно обрабатываем связанные блоки
            if not start_label:
                print(f"DEBUG: START блок {start_block.id} без label, пропускаем генерацию label")
                # START блок без label - генерируем только связанные блоки
                visited.add(start_block.id)
                visited_for_chain = set()
                visited_for_chain.add(start_block.id)
                next_blocks_with_dist = connections_map.get(start_block.id, [])
                for next_id, _ in next_blocks_with_dist:
                    if next_id not in visited_for_chain:
                        chain_code = generate_block_chain(
                            scene, next_id, connections_map, visited_for_chain, INDENT, 
                            char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes,
                            generated_labels=generated_labels, all_possible_labels=all_possible_labels
                        )
                        if chain_code:
                            lines.append(chain_code)
                visited.update(visited_for_chain)
                continue
            
            # Генерируем label для START блока (всегда, если label есть)
            # НЕ проверяем generated_labels - label должен генерироваться в каждой сцене, где он есть
            print(f"DEBUG: Генерация label для START блока {start_block.id} с label '{start_label}'")
            code = generate_block(start_block, "", char_name_map, project_scenes, generated_labels, all_possible_labels)
            print(f"DEBUG: Сгенерированный код для START блока: {repr(code)}")
            if code:
                lines.append(code)
                generated_labels.add(start_label)
                print(f"DEBUG: Label '{start_label}' добавлен в generated_labels и в lines")
            else:
                print(f"DEBUG: generate_block вернул пустую строку для START блока {start_block.id}")
            
            visited.add(start_block.id)
            
            # Генерируем цепочку блоков после START блока
            visited_for_chain = set()
            visited_for_chain.add(start_block.id)
            
            # Получаем блоки, связанные с START блоком
            # Обрабатываем все связанные блоки в порядке расстояния (ближайшие первыми)
            next_blocks_with_dist = connections_map.get(start_block.id, [])
            print(f"DEBUG: START блок {start_block.id} имеет {len(next_blocks_with_dist)} связанных блоков")
            for next_id, dist in next_blocks_with_dist:
                print(f"  Связанный блок: {next_id}, расстояние: {dist}")
            
            # Обрабатываем все выходы последовательно (в порядке расстояния)
            for next_id, dist in next_blocks_with_dist:
                if next_id not in visited_for_chain:
                    print(f"DEBUG: Генерация цепочки для блока {next_id} после START блока {start_block.id} (расстояние: {dist})")
                    chain_code = generate_block_chain(
                        scene, next_id, connections_map, visited_for_chain, INDENT, 
                        char_name_map, reverse_connections, recursive=True, project_scenes=project_scenes,
                        generated_labels=generated_labels, all_possible_labels=all_possible_labels
                    )
                    print(f"DEBUG: Сгенерированный код цепочки для блока {next_id}: {repr(chain_code[:100]) if chain_code else 'пусто'}")
                    if chain_code:
                        lines.append(chain_code)
                else:
                    print(f"DEBUG: Блок {next_id} уже в visited_for_chain, пропускаем")
            
            # Отмечаем все обработанные блоки как visited
            print(f"DEBUG: Обработано блоков в цепочке после START {start_block.id}: {len(visited_for_chain)}")
            visited.update(visited_for_chain)
            
            # НЕ добавляем return автоматически в конце label'ов
            # return должен быть только один раз в конце label start:
            # Пользователь может добавить return через RETURN блок, если нужно
        
        # Генерируем оставшиеся блоки (не связанные с START блоками)
        for block_id, _, _ in blocks_to_generate:
            if block_id in visited:
                continue
            
            block = scene.find_block(block_id)
            if not block:
                continue
            
            # START блоки, IMAGE, CHARACTER блоки уже обработаны
            if block.type in (BlockType.IMAGE, BlockType.CHARACTER, BlockType.START):
                visited.add(block_id)
                continue
            
            # Генерируем блок с отступом
            code = generate_block(block, INDENT, char_name_map, project_scenes, generated_labels, all_possible_labels)
            if code:
                lines.append(code)
            visited.add(block_id)
        
        # Обрабатываем блоки без соединений
        print(f"DEBUG: Обработка блоков без соединений в сцене {scene.name}")
        print(f"  Всего блоков в сцене: {len(scene.blocks)}")
        print(f"  Обработано блоков (visited): {len(visited)}")
        unvisited_blocks = [b for b in scene.blocks if b.id not in visited and b.type not in (BlockType.IMAGE, BlockType.CHARACTER)]
        print(f"  Необработанных блоков (кроме IMAGE/CHARACTER): {len(unvisited_blocks)}")
        for block in unvisited_blocks:
            print(f"    Блок {block.id} типа {block.type}")
        
        for block in scene.blocks:
            if block.id not in visited and block.type not in (BlockType.IMAGE, BlockType.CHARACTER):
                # START блоки генерируются на верхнем уровне (без отступа)
                if block.type == BlockType.START:
                    from renpy_node_editor.core.generator.blocks import safe_get_str
                    start_label = safe_get_str(block.params, "label", "") or safe_get_str(block.params, "Имя метки (label):", "")
                    # Генерируем label всегда, если он есть (даже если уже был сгенерирован в другой сцене)
                    if start_label:
                        print(f"DEBUG: Генерация START блока {block.id} с label '{start_label}' (блок без соединений)")
                        code = generate_block(block, "", char_name_map, project_scenes, generated_labels, all_possible_labels)
                        if code:
                            lines.append(code)
                            # Добавляем в generated_labels только если еще не было
                            if start_label not in generated_labels:
                                generated_labels.add(start_label)
                else:
                    print(f"DEBUG: Генерация блока {block.id} типа {block.type} (блок без соединений)")
                    code = generate_block(block, INDENT, char_name_map, project_scenes, generated_labels, all_possible_labels)
                    if code:
                        lines.append(code)
    
    print(f"DEBUG: Итого сгенерировано строк для сцены {scene.name}: {len(lines)}")
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
    
    # Собираем все метки, которые будут сгенерированы, чтобы избежать дубликатов
    generated_labels: Set[str] = set()
    
    # Собираем все возможные метки из START и LABEL блоков для проверки JUMP/CALL
    # НЕ добавляем их в generated_labels заранее - они будут добавлены при генерации
    all_possible_labels: Set[str] = set()
    from renpy_node_editor.core.model import BlockType
    from renpy_node_editor.core.generator.blocks import safe_get_str
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
    
    print(f"DEBUG: Всего возможных label'ов для проверки JUMP/CALL: {sorted(all_possible_labels)}")
    
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
