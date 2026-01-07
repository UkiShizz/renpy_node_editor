from __future__ import annotations

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from renpy_node_editor.core.model import Project, Scene, Block, BlockType, Connection, Port

INDENT = "    "


def _get_block_connections(scene: Scene) -> Dict[str, List[str]]:
    """Создать словарь: block_id -> список следующих block_id по связям"""
    connections_map: Dict[str, List[str]] = defaultdict(list)
    
    # Создаем маппинг port_id -> block_id
    port_to_block: Dict[str, str] = {}
    for port in scene.ports:
        port_to_block[port.id] = port.node_id
    
    # Проходим по всем связям
    for conn in scene.connections:
        from_block = port_to_block.get(conn.from_port_id)
        to_block = port_to_block.get(conn.to_port_id)
        if from_block and to_block:
            connections_map[from_block].append(to_block)
    
    return connections_map


def _find_start_blocks(scene: Scene, connections_map: Dict[str, List[str]]) -> List[Block]:
    """Найти начальные блоки (те, на которые ничего не указывает)"""
    # Находим все блоки, на которые что-то указывает
    has_input: Set[str] = set()
    for targets in connections_map.values():
        has_input.update(targets)
    
    # Начальные блоки - те, на которые ничего не указывает
    start_blocks = [b for b in scene.blocks if b.id not in has_input]
    
    # Если нет связей, возвращаем все блоки в порядке их позиции
    if not connections_map:
        return sorted(scene.blocks, key=lambda b: (b.y, b.x))
    
    return start_blocks


def _gen_label(scene: Scene) -> str:
    return f"label {scene.label}:\n"


def _gen_say(block: Block, indent: str) -> str:
    who = block.params.get("who", "").strip()
    text = block.params.get("text", "").strip()
    
    if not text:
        return ""
    
    # Экранируем кавычки в тексте
    text = text.replace('"', '\\"')
    
    if who:
        return f"{indent}{who} \"{text}\"\n"
    return f"{indent}\"{text}\"\n"


def _gen_narration(block: Block, indent: str) -> str:
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = text.replace('"', '\\"')
    return f"{indent}\"{text}\"\n"


def _gen_menu(block: Block, indent: str) -> str:
    """Генерация меню с вариантами выбора"""
    lines: List[str] = []
    question = block.params.get("question", "").strip()
    
    if question:
        question = question.replace('"', '\\"')
        lines.append(f"{indent}\"{question}\"\n")
    
    lines.append(f"{indent}menu:\n")
    
    # Получаем варианты из params
    choices = block.params.get("choices", [])
    if isinstance(choices, str):
        # Если choices - строка, пытаемся распарсить
        try:
            import json
            choices = json.loads(choices)
        except:
            # Если не JSON, разбиваем по запятым
            choices = [{"text": c.strip(), "jump": ""} for c in choices.split(",") if c.strip()]
    elif not isinstance(choices, list):
        choices = []
    
    for i, choice in enumerate(choices):
        if isinstance(choice, dict):
            text = choice.get("text", "").strip()
            jump = choice.get("jump", "").strip()
        else:
            text = str(choice).strip()
            jump = ""
        
        if not text:
            continue
        
        text = text.replace('"', '\\"')
        lines.append(f"{indent}{INDENT}\"{text}\":\n")
        if jump:
            lines.append(f"{indent}{INDENT*2}jump {jump}\n")
        else:
            # Если нет jump, просто продолжаем выполнение
            lines.append(f"{indent}{INDENT*2}pass\n")
    
    return "".join(lines)


def _gen_if(block: Block, indent: str, true_branch: Optional[str] = None, false_branch: Optional[str] = None) -> str:
    """Генерация условного блока"""
    condition = block.params.get("condition", "").strip()
    if not condition:
        return ""
    
    lines: List[str] = []
    lines.append(f"{indent}if {condition}:\n")
    
    if true_branch:
        # Добавляем содержимое ветки True с дополнительным отступом
        for line in true_branch.split('\n'):
            if line.strip():
                lines.append(f"{indent}{INDENT}{line}\n")
            else:
                lines.append("\n")
    else:
        lines.append(f"{indent}{INDENT}pass\n")
    
    if false_branch:
        lines.append(f"{indent}else:\n")
        for line in false_branch.split('\n'):
            if line.strip():
                lines.append(f"{indent}{INDENT}{line}\n")
            else:
                lines.append("\n")
    
    return "".join(lines)


def _gen_jump(block: Block, indent: str) -> str:
    target = block.params.get("target", "").strip()
    if not target:
        return ""
    return f"{indent}jump {target}\n"


def _gen_call(block: Block, indent: str) -> str:
    label = block.params.get("label", "").strip()
    if not label:
        return ""
    return f"{indent}call {label}\n"


def _gen_return(block: Block, indent: str) -> str:
    return f"{indent}return\n"


def _gen_scene(block: Block, indent: str) -> str:
    bg = block.params.get("background", "black").strip()
    if not bg:
        bg = "black"
    
    trans = block.params.get("transition", "").strip()
    line = f"{indent}scene {bg}"
    if trans:
        line += f" with {trans}"
    return line + "\n"


def _gen_show(block: Block, indent: str) -> str:
    char = block.params.get("character", "").strip()
    if not char:
        return ""
    
    expr = block.params.get("expression", "").strip()
    at = block.params.get("at", "").strip()
    
    parts = [char]
    if expr:
        parts.append(expr)
    
    line = f"{indent}show {' '.join(parts)}"
    if at:
        line += f" at {at}"
    return line + "\n"


def _gen_hide(block: Block, indent: str) -> str:
    char = block.params.get("character", "").strip()
    if not char:
        return ""
    return f"{indent}hide {char}\n"


def _gen_pause(block: Block, indent: str) -> str:
    duration = block.params.get("duration", "1.0")
    try:
        float(duration)
        return f"{indent}$ renpy.pause({duration})\n"
    except ValueError:
        return f"{indent}$ renpy.pause(1.0)\n"


def _gen_transition(block: Block, indent: str) -> str:
    trans = block.params.get("transition", "dissolve").strip()
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def _gen_sound(block: Block, indent: str) -> str:
    sound_file = block.params.get("sound_file", "").strip()
    if not sound_file:
        return ""
    return f"{indent}play sound \"{sound_file}\"\n"


def _gen_music(block: Block, indent: str) -> str:
    music_file = block.params.get("music_file", "").strip()
    if not music_file:
        return ""
    
    loop = block.params.get("loop", "True").strip().lower()
    loop_str = "loop" if loop in ("true", "1", "yes") else "noloop"
    return f"{indent}play music \"{music_file}\" {loop_str}\n"


def _gen_set_var(block: Block, indent: str) -> str:
    var = block.params.get("variable", "").strip()
    value = block.params.get("value", "").strip()
    
    if not var:
        return ""
    
    # Пытаемся определить тип значения
    try:
        # Пробуем как число
        float(value)
        return f"{indent}$ {var} = {value}\n"
    except ValueError:
        # Если не число, то строка
        if value.startswith('"') and value.endswith('"'):
            return f"{indent}$ {var} = {value}\n"
        else:
            return f"{indent}$ {var} = \"{value}\"\n"


def _generate_block(block: Block, indent: str) -> str:
    """Генерация кода для одного блока"""
    if block.type is BlockType.SAY:
        return _gen_say(block, indent)
    elif block.type is BlockType.NARRATION:
        return _gen_narration(block, indent)
    elif block.type is BlockType.MENU:
        return _gen_menu(block, indent)
    elif block.type is BlockType.IF:
        # IF обрабатывается отдельно в _generate_scene
        return ""
    elif block.type is BlockType.JUMP:
        return _gen_jump(block, indent)
    elif block.type is BlockType.CALL:
        return _gen_call(block, indent)
    elif block.type is BlockType.RETURN:
        return _gen_return(block, indent)
    elif block.type is BlockType.SCENE:
        return _gen_scene(block, indent)
    elif block.type is BlockType.SHOW:
        return _gen_show(block, indent)
    elif block.type is BlockType.HIDE:
        return _gen_hide(block, indent)
    elif block.type is BlockType.PAUSE:
        return _gen_pause(block, indent)
    elif block.type is BlockType.TRANSITION:
        return _gen_transition(block, indent)
    elif block.type is BlockType.SOUND:
        return _gen_sound(block, indent)
    elif block.type is BlockType.MUSIC:
        return _gen_music(block, indent)
    elif block.type is BlockType.SET_VAR:
        return _gen_set_var(block, indent)
    elif block.type is BlockType.LABEL:
        label = block.params.get("label", "").strip()
        if label:
            return f"label {label}:\n"
    return ""


def _generate_block_chain(
    scene: Scene,
    start_block_id: str,
    connections_map: Dict[str, List[str]],
    visited: Set[str],
    indent: str
) -> str:
    """Рекурсивная генерация цепочки блоков"""
    if start_block_id in visited:
        return ""  # Предотвращаем циклы
    
    visited.add(start_block_id)
    block = scene.find_block(start_block_id)
    if not block:
        return ""
    
    lines: List[str] = []
    
    # Генерируем код для текущего блока
    if block.type is BlockType.IF:
        # Специальная обработка IF блока
        condition = block.params.get("condition", "").strip()
        if condition:
            # Находим следующие блоки
            next_blocks = connections_map.get(block.id, [])
            
            true_branch = ""
            false_branch = ""
            
            if len(next_blocks) >= 1:
                # Первый выход - ветка True
                true_branch = _generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            if len(next_blocks) >= 2:
                # Второй выход - ветка False
                false_branch = _generate_block_chain(
                    scene, next_blocks[1], connections_map, visited.copy(), indent + INDENT
                )
            
            lines.append(_gen_if(block, indent, true_branch, false_branch))
    else:
        # Обычный блок
        code = _generate_block(block, indent)
        if code:
            lines.append(code)
        
        # Продолжаем по связям
        next_blocks = connections_map.get(block.id, [])
        for next_id in next_blocks:
            if next_id not in visited:
                next_code = _generate_block_chain(
                    scene, next_id, connections_map, visited.copy(), indent
                )
                if next_code:
                    lines.append(next_code)
    
    return "".join(lines)


def _generate_scene(scene: Scene) -> str:
    """Генерация кода для сцены с учетом связей между блоками"""
    lines: List[str] = []
    
    # Заголовок сцены
    lines.append(_gen_label(scene))
    
    if not scene.blocks:
        lines.append(f"{INDENT}pass\n\n")
        return "".join(lines)
    
    # Создаем карту связей
    connections_map = _get_block_connections(scene)
    
    # Находим начальные блоки
    start_blocks = _find_start_blocks(scene, connections_map)
    
    if not start_blocks:
        # Если нет начальных блоков, генерируем все блоки по порядку
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            code = _generate_block(block, indent)
            if code:
                lines.append(code)
    else:
        # Генерируем от начальных блоков
        visited: Set[str] = set()
        for start_block in start_blocks:
            code = _generate_block_chain(
                scene, start_block.id, connections_map, visited.copy(), INDENT
            )
            if code:
                lines.append(code)
        
        # Добавляем блоки, которые не были обработаны (без связей)
        processed = set()
        for start_block in start_blocks:
            processed.add(start_block.id)
            # Добавляем все связанные блоки
            stack = [start_block.id]
            while stack:
                current_id = stack.pop()
                for next_id in connections_map.get(current_id, []):
                    if next_id not in processed:
                        processed.add(next_id)
                        stack.append(next_id)
        
        # Добавляем непрошедшие блоки
        for block in scene.blocks:
            if block.id not in processed:
                code = _generate_block(block, INDENT)
                if code:
                    lines.append(code)
    
    lines.append("\n")
    return "".join(lines)


def _extract_characters(project: Project) -> Set[str]:
    """Извлечь всех персонажей из проекта"""
    characters: Set[str] = set()
    
    for scene in project.scenes:
        for block in scene.blocks:
            if block.type is BlockType.SAY:
                who = block.params.get("who", "").strip()
                if who:
                    characters.add(who)
            elif block.type is BlockType.SHOW or block.type is BlockType.HIDE:
                char = block.params.get("character", "").strip()
                if char:
                    characters.add(char)
    
    return characters


def generate_renpy_script(project: Project) -> str:
    """
    Сгенерировать полный текст Ren'Py-скрипта для проекта.
    """
    lines: List[str] = []
    
    # Заголовок
    lines.append("# Generated by RenPy Node Editor\n")
    lines.append("# This file is auto-generated. Do not edit manually.\n\n")
    
    # Извлекаем персонажей и создаем define
    characters = _extract_characters(project)
    if characters:
        lines.append("# Characters\n")
        for char in sorted(characters):
            # Простое имя персонажа
            char_name = char.replace(" ", "_").replace("-", "_")
            lines.append(f"define {char_name} = Character('{char}')\n")
        lines.append("\n")
    else:
        # Дефолтный narrator
        lines.append("define narrator = Character('Narrator')\n\n")
    
    # Генерируем сцены
    for scene in project.scenes:
        lines.append(_generate_scene(scene))
    
    return "".join(lines)
