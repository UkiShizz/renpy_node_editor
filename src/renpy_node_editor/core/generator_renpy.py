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
    has_input: Set[str] = set()
    for targets in connections_map.values():
        has_input.update(targets)
    
    start_blocks = [b for b in scene.blocks if b.id not in has_input]
    
    if not connections_map:
        return sorted(scene.blocks, key=lambda b: (b.y, b.x))
    
    return start_blocks


def _gen_label(scene: Scene) -> str:
    return f"label {scene.label}:\n"


def _gen_say(block: Block, indent: str) -> str:
    """Генерация диалога персонажа"""
    who = block.params.get("who", "").strip()
    text = block.params.get("text", "").strip()
    
    if not text:
        return ""
    
    text = text.replace('"', '\\"')
    
    # Поддержка дополнительных параметров
    attrs = []
    
    if who:
        # Поддержка выражений и атрибутов
        expression = block.params.get("expression", "").strip()
        if expression:
            who = f"{who} {expression}"
        
        # Поддержка at (позиция)
        at_pos = block.params.get("at", "").strip()
        if at_pos:
            attrs.append(f"at {at_pos}")
        
        # Поддержка with (переход)
        with_trans = block.params.get("with_transition", "").strip()
        if with_trans:
            attrs.append(f"with {with_trans}")
        
        result = f"{indent}{who} \"{text}\""
        if attrs:
            result += " " + " ".join(attrs)
        return result + "\n"
    
    return f"{indent}\"{text}\"\n"


def _gen_narration(block: Block, indent: str) -> str:
    """Генерация повествования"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = text.replace('"', '\\"')
    
    # Поддержка переходов
    with_trans = block.params.get("with_transition", "").strip()
    if with_trans:
        return f"{indent}\"{text}\" with {with_trans}\n"
    
    return f"{indent}\"{text}\"\n"


def _gen_menu(block: Block, indent: str) -> str:
    """Генерация меню с вариантами выбора"""
    lines: List[str] = []
    question = block.params.get("question", "").strip()
    
    if question:
        question = question.replace('"', '\\"')
        lines.append(f"{indent}\"{question}\"\n")
    
    lines.append(f"{indent}menu:\n")
    
    choices = block.params.get("choices", [])
    if isinstance(choices, str):
        try:
            import json
            choices = json.loads(choices)
        except:
            choices = [{"text": c.strip(), "jump": ""} for c in choices.split(",") if c.strip()]
    elif not isinstance(choices, list):
        choices = []
    
    for i, choice in enumerate(choices):
        if isinstance(choice, dict):
            text = choice.get("text", "").strip()
            jump = choice.get("jump", "").strip()
            condition = choice.get("condition", "").strip()
        else:
            text = str(choice).strip()
            jump = ""
            condition = ""
        
        if not text:
            continue
        
        text = text.replace('"', '\\"')
        
        # Поддержка условий для вариантов
        if condition:
            lines.append(f"{indent}{INDENT}if {condition}:\n")
            lines.append(f"{indent}{INDENT*2}\"{text}\":\n")
        else:
            lines.append(f"{indent}{INDENT}\"{text}\":\n")
        
        if jump:
            lines.append(f"{indent}{INDENT*2}jump {jump}\n")
        else:
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


def _gen_while(block: Block, indent: str, loop_body: Optional[str] = None) -> str:
    """Генерация цикла while"""
    condition = block.params.get("condition", "").strip()
    if not condition:
        return ""
    
    lines: List[str] = []
    lines.append(f"{indent}while {condition}:\n")
    
    if loop_body:
        for line in loop_body.split('\n'):
            if line.strip():
                lines.append(f"{indent}{INDENT}{line}\n")
            else:
                lines.append("\n")
    else:
        lines.append(f"{indent}{INDENT}pass\n")
    
    return "".join(lines)


def _gen_for(block: Block, indent: str, loop_body: Optional[str] = None) -> str:
    """Генерация цикла for"""
    var = block.params.get("variable", "").strip()
    iterable = block.params.get("iterable", "").strip()
    
    if not var or not iterable:
        return ""
    
    lines: List[str] = []
    lines.append(f"{indent}for {var} in {iterable}:\n")
    
    if loop_body:
        for line in loop_body.split('\n'):
            if line.strip():
                lines.append(f"{indent}{INDENT}{line}\n")
            else:
                lines.append("\n")
    else:
        lines.append(f"{indent}{INDENT}pass\n")
    
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
    """Генерация scene с поддержкой всех параметров"""
    bg = block.params.get("background", "black").strip()
    if not bg:
        bg = "black"
    
    # Поддержка слоев
    layer = block.params.get("layer", "").strip()
    if layer:
        bg = f"{bg} onlayer {layer}"
    
    trans = block.params.get("transition", "").strip()
    line = f"{indent}scene {bg}"
    if trans:
        line += f" with {trans}"
    return line + "\n"


def _gen_show(block: Block, indent: str) -> str:
    """Генерация show с поддержкой всех параметров"""
    char = block.params.get("character", "").strip()
    if not char:
        return ""
    
    expr = block.params.get("expression", "").strip()
    at = block.params.get("at", "").strip()
    behind = block.params.get("behind", "").strip()
    zorder = block.params.get("zorder", "").strip()
    layer = block.params.get("layer", "").strip()
    
    parts = [char]
    if expr:
        parts.append(expr)
    
    line = f"{indent}show {' '.join(parts)}"
    
    if at:
        line += f" at {at}"
    if behind:
        line += f" behind {behind}"
    if zorder:
        line += f" zorder {zorder}"
    if layer:
        line += f" onlayer {layer}"
    
    trans = block.params.get("transition", "").strip()
    if trans:
        line += f" with {trans}"
    
    return line + "\n"


def _gen_hide(block: Block, indent: str) -> str:
    """Генерация hide с поддержкой всех параметров"""
    char = block.params.get("character", "").strip()
    if not char:
        return ""
    
    line = f"{indent}hide {char}"
    
    layer = block.params.get("layer", "").strip()
    if layer:
        line += f" onlayer {layer}"
    
    trans = block.params.get("transition", "").strip()
    if trans:
        line += f" with {trans}"
    
    return line + "\n"


def _gen_image(block: Block, indent: str) -> str:
    """Генерация определения изображения"""
    name = block.params.get("name", "").strip()
    path = block.params.get("path", "").strip()
    
    if not name or not path:
        return ""
    
    return f"{indent}image {name} = \"{path}\"\n"


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


def _gen_with(block: Block, indent: str) -> str:
    """Генерация with statement"""
    trans = block.params.get("transition", "dissolve").strip()
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def _gen_sound(block: Block, indent: str) -> str:
    """Генерация play sound с поддержкой всех параметров"""
    sound_file = block.params.get("sound_file", "").strip()
    if not sound_file:
        return ""
    
    line = f"{indent}play sound \"{sound_file}\""
    
    fadein = block.params.get("fadein", "").strip()
    fadeout = block.params.get("fadeout", "").strip()
    loop = block.params.get("loop", "").strip().lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if fadeout:
        line += f" fadeout {fadeout}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    
    return line + "\n"


def _gen_music(block: Block, indent: str) -> str:
    """Генерация play music с поддержкой всех параметров"""
    music_file = block.params.get("music_file", "").strip()
    if not music_file:
        return ""
    
    line = f"{indent}play music \"{music_file}\""
    
    fadein = block.params.get("fadein", "").strip()
    fadeout = block.params.get("fadeout", "").strip()
    loop = block.params.get("loop", "True").strip().lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if fadeout:
        line += f" fadeout {fadeout}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    else:
        line += " noloop"
    
    return line + "\n"


def _gen_stop_music(block: Block, indent: str) -> str:
    """Остановка музыки"""
    fadeout = block.params.get("fadeout", "").strip()
    if fadeout:
        return f"{indent}stop music fadeout {fadeout}\n"
    return f"{indent}stop music\n"


def _gen_stop_sound(block: Block, indent: str) -> str:
    """Остановка звука"""
    fadeout = block.params.get("fadeout", "").strip()
    if fadeout:
        return f"{indent}stop sound fadeout {fadeout}\n"
    return f"{indent}stop sound\n"


def _gen_queue_music(block: Block, indent: str) -> str:
    """Очередь музыки"""
    music_file = block.params.get("music_file", "").strip()
    if not music_file:
        return ""
    
    fadein = block.params.get("fadein", "").strip()
    loop = block.params.get("loop", "").strip().lower()
    
    line = f"{indent}queue music \"{music_file}\""
    if fadein:
        line += f" fadein {fadein}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    
    return line + "\n"


def _gen_queue_sound(block: Block, indent: str) -> str:
    """Очередь звука"""
    sound_file = block.params.get("sound_file", "").strip()
    if not sound_file:
        return ""
    
    fadein = block.params.get("fadein", "").strip()
    
    line = f"{indent}queue sound \"{sound_file}\""
    if fadein:
        line += f" fadein {fadein}"
    
    return line + "\n"


def _gen_set_var(block: Block, indent: str) -> str:
    """Генерация установки переменной"""
    var = block.params.get("variable", "").strip()
    value = block.params.get("value", "").strip()
    
    if not var:
        return ""
    
    # Пытаемся определить тип значения
    try:
        float(value)
        return f"{indent}$ {var} = {value}\n"
    except ValueError:
        if value.startswith('"') and value.endswith('"'):
            return f"{indent}$ {var} = {value}\n"
        elif value.startswith('[') or value.startswith('{'):
            # Список или словарь
            return f"{indent}$ {var} = {value}\n"
        else:
            return f"{indent}$ {var} = \"{value}\"\n"


def _gen_default(block: Block, indent: str) -> str:
    """Генерация default statement"""
    var = block.params.get("variable", "").strip()
    value = block.params.get("value", "").strip()
    
    if not var:
        return ""
    
    try:
        float(value)
        return f"{indent}default {var} = {value}\n"
    except ValueError:
        if value.startswith('"') and value.endswith('"'):
            return f"{indent}default {var} = {value}\n"
        elif value.startswith('[') or value.startswith('{'):
            return f"{indent}default {var} = {value}\n"
        else:
            return f"{indent}default {var} = \"{value}\"\n"


def _gen_define(block: Block, indent: str) -> str:
    """Генерация define statement"""
    name = block.params.get("name", "").strip()
    value = block.params.get("value", "").strip()
    
    if not name:
        return ""
    
    try:
        float(value)
        return f"{indent}define {name} = {value}\n"
    except ValueError:
        if value.startswith('"') and value.endswith('"'):
            return f"{indent}define {name} = {value}\n"
        elif value.startswith('[') or value.startswith('{'):
            return f"{indent}define {name} = {value}\n"
        else:
            return f"{indent}define {name} = \"{value}\"\n"


def _gen_python(block: Block, indent: str) -> str:
    """Генерация Python кода"""
    code = block.params.get("code", "").strip()
    if not code:
        return ""
    
    lines: List[str] = []
    lines.append(f"{indent}python:\n")
    
    # Разбиваем код на строки и добавляем отступ
    for line in code.split('\n'):
        if line.strip():
            lines.append(f"{indent}{INDENT}{line}\n")
        else:
            lines.append("\n")
    
    return "".join(lines)


def _gen_character(block: Block, indent: str) -> str:
    """Генерация определения персонажа"""
    name = block.params.get("name", "").strip()
    display_name = block.params.get("display_name", "").strip()
    
    if not name:
        return ""
    
    if display_name:
        display_name = display_name.replace("'", "\\'")
        return f"{indent}define {name} = Character('{display_name}')\n"
    else:
        return f"{indent}define {name} = Character(None)\n"


def _gen_voice(block: Block, indent: str) -> str:
    """Генерация voice statement"""
    voice_file = block.params.get("voice_file", "").strip()
    if not voice_file:
        return ""
    
    return f"{indent}voice \"{voice_file}\"\n"


def _gen_center(block: Block, indent: str) -> str:
    """Генерация center statement"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = text.replace('"', '\\"')
    return f"{indent}centered \"{text}\"\n"


def _gen_text(block: Block, indent: str) -> str:
    """Генерация text statement"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = text.replace('"', '\\"')
    
    xpos = block.params.get("xpos", "").strip()
    ypos = block.params.get("ypos", "").strip()
    
    line = f"{indent}text \"{text}\""
    if xpos:
        line += f" xpos {xpos}"
    if ypos:
        line += f" ypos {ypos}"
    
    return line + "\n"


def _generate_block(block: Block, indent: str) -> str:
    """Генерация кода для одного блока"""
    if block.type is BlockType.SAY:
        return _gen_say(block, indent)
    elif block.type is BlockType.NARRATION:
        return _gen_narration(block, indent)
    elif block.type is BlockType.MENU:
        return _gen_menu(block, indent)
    elif block.type is BlockType.IF:
        # IF обрабатывается отдельно
        return ""
    elif block.type is BlockType.WHILE:
        # WHILE обрабатывается отдельно
        return ""
    elif block.type is BlockType.FOR:
        # FOR обрабатывается отдельно
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
    elif block.type is BlockType.IMAGE:
        return _gen_image(block, indent)
    elif block.type is BlockType.PAUSE:
        return _gen_pause(block, indent)
    elif block.type is BlockType.TRANSITION:
        return _gen_transition(block, indent)
    elif block.type is BlockType.WITH:
        return _gen_with(block, indent)
    elif block.type is BlockType.SOUND:
        return _gen_sound(block, indent)
    elif block.type is BlockType.MUSIC:
        return _gen_music(block, indent)
    elif block.type is BlockType.STOP_MUSIC:
        return _gen_stop_music(block, indent)
    elif block.type is BlockType.STOP_SOUND:
        return _gen_stop_sound(block, indent)
    elif block.type is BlockType.QUEUE_MUSIC:
        return _gen_queue_music(block, indent)
    elif block.type is BlockType.QUEUE_SOUND:
        return _gen_queue_sound(block, indent)
    elif block.type is BlockType.SET_VAR:
        return _gen_set_var(block, indent)
    elif block.type is BlockType.DEFAULT:
        return _gen_default(block, indent)
    elif block.type is BlockType.DEFINE:
        return _gen_define(block, indent)
    elif block.type is BlockType.PYTHON:
        return _gen_python(block, indent)
    elif block.type is BlockType.CHARACTER:
        return _gen_character(block, indent)
    elif block.type is BlockType.VOICE:
        return _gen_voice(block, indent)
    elif block.type is BlockType.CENTER:
        return _gen_center(block, indent)
    elif block.type is BlockType.TEXT:
        return _gen_text(block, indent)
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
        condition = block.params.get("condition", "").strip()
        if condition:
            next_blocks = connections_map.get(block.id, [])
            
            true_branch = ""
            false_branch = ""
            
            if len(next_blocks) >= 1:
                true_branch = _generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            if len(next_blocks) >= 2:
                false_branch = _generate_block_chain(
                    scene, next_blocks[1], connections_map, visited.copy(), indent + INDENT
                )
            
            lines.append(_gen_if(block, indent, true_branch, false_branch))
    elif block.type is BlockType.WHILE:
        condition = block.params.get("condition", "").strip()
        if condition:
            next_blocks = connections_map.get(block.id, [])
            loop_body = ""
            
            if next_blocks:
                loop_body = _generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            lines.append(_gen_while(block, indent, loop_body))
    elif block.type is BlockType.FOR:
        var = block.params.get("variable", "").strip()
        iterable = block.params.get("iterable", "").strip()
        if var and iterable:
            next_blocks = connections_map.get(block.id, [])
            loop_body = ""
            
            if next_blocks:
                loop_body = _generate_block_chain(
                    scene, next_blocks[0], connections_map, visited.copy(), indent + INDENT
                )
            
            lines.append(_gen_for(block, indent, loop_body))
    else:
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
    
    lines.append(_gen_label(scene))
    
    if not scene.blocks:
        lines.append(f"{INDENT}pass\n\n")
        return "".join(lines)
    
    connections_map = _get_block_connections(scene)
    start_blocks = _find_start_blocks(scene, connections_map)
    
    if not start_blocks:
        indent = INDENT
        for block in sorted(scene.blocks, key=lambda b: (b.y, b.x)):
            code = _generate_block(block, indent)
            if code:
                lines.append(code)
    else:
        visited: Set[str] = set()
        for start_block in start_blocks:
            code = _generate_block_chain(
                scene, start_block.id, connections_map, visited.copy(), INDENT
            )
            if code:
                lines.append(code)
        
        # Добавляем блоки, которые не были обработаны
        processed = set()
        for start_block in start_blocks:
            processed.add(start_block.id)
            stack = [start_block.id]
            while stack:
                current_id = stack.pop()
                for next_id in connections_map.get(current_id, []):
                    if next_id not in processed:
                        processed.add(next_id)
                        stack.append(next_id)
        
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
    
    # Добавляем персонажей из глобальных определений
    for char_name in project.characters.keys():
        characters.add(char_name)
    
    # Извлекаем из блоков
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
            elif block.type is BlockType.CHARACTER:
                name = block.params.get("name", "").strip()
                if name:
                    characters.add(name)
    
    return characters


def _generate_definitions(project: Project) -> str:
    """Генерация глобальных определений (define, default, image)"""
    lines: List[str] = []
    
    # Определения изображений
    if project.images:
        lines.append("# Image Definitions\n")
        for name, path in sorted(project.images.items()):
            lines.append(f"image {name} = \"{path}\"\n")
        lines.append("\n")
    
    # Определения персонажей
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
    """
    Сгенерировать полный текст Ren'Py-скрипта для проекта.
    """
    lines: List[str] = []
    
    # Заголовок
    lines.append("# Generated by RenPy Node Editor\n")
    lines.append("# This file is auto-generated. Do not edit manually.\n\n")
    
    # Глобальные определения
    def_lines = _generate_definitions(project)
    if def_lines:
        lines.append(def_lines)
    
    # Извлекаем персонажей из блоков и создаем define
    characters = _extract_characters(project)
    if characters:
        lines.append("# Characters (auto-detected)\n")
        for char in sorted(characters):
            # Проверяем, не определен ли уже в project.characters
            if char not in project.characters:
                char_name = char.replace(" ", "_").replace("-", "_")
                lines.append(f"define {char_name} = Character('{char}')\n")
        lines.append("\n")
    elif not project.characters:
        # Дефолтный narrator
        lines.append("define narrator = Character('Narrator')\n\n")
    
    # Генерируем сцены
    for scene in project.scenes:
        lines.append(_generate_scene(scene))
    
    return "".join(lines)
