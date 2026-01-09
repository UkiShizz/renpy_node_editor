"""Block code generators"""
from __future__ import annotations

import json
from typing import Optional, Any
from renpy_node_editor.core.model import Block, BlockType, Scene
from renpy_node_editor.core.generator.utils import INDENT, escape_text, format_value


def safe_get_str(params: dict[str, Any], key: str, default: str = "") -> str:
    """Safely get string parameter, handling None values"""
    value = params.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def generate_label(scene: Scene) -> str:
    """Generate label statement"""
    return f"label {scene.label}:\n"


def generate_say(block: Block, indent: str) -> str:
    """Generate character dialogue"""
    who = safe_get_str(block.params, "who")
    text = safe_get_str(block.params, "text")
    
    print(f"DEBUG generate_say: Блок {block.id}, who='{who}', text='{text}', params keys: {list(block.params.keys())}")
    
    if not text:
        print(f"DEBUG generate_say: Текст пустой, возвращаем пустую строку")
        return ""
    
    text = escape_text(text)
    
    attrs = []
    if who:
        expression = safe_get_str(block.params, "expression")
        if expression:
            who = f"{who} {expression}"
        
        at_pos = safe_get_str(block.params, "at")
        if at_pos:
            attrs.append(f"at {at_pos}")
        
        with_trans = safe_get_str(block.params, "with_transition")
        if with_trans:
            attrs.append(f"with {with_trans}")
        
        result = f"{indent}{who} \"{text}\""
        if attrs:
            result += " " + " ".join(attrs)
        return result + "\n"
    
    return f"{indent}\"{text}\"\n"


def generate_narration(block: Block, indent: str) -> str:
    """Generate narration text"""
    text = safe_get_str(block.params, "text")
    if not text:
        return ""
    
    text = escape_text(text)
    with_trans = safe_get_str(block.params, "with_transition")
    
    if with_trans:
        return f"{indent}\"{text}\" with {with_trans}\n"
    
    return f"{indent}\"{text}\"\n"


def generate_menu(block: Block, indent: str) -> str:
    """Generate menu with choices"""
    lines: list[str] = []
    question = safe_get_str(block.params, "question")
    
    if question:
        question = escape_text(question)
        lines.append(f"{indent}\"{question}\"\n")
    
    lines.append(f"{indent}menu:\n")
    
    choices = block.params.get("choices", [])
    if isinstance(choices, str):
        try:
            choices = json.loads(choices)
        except (json.JSONDecodeError, ValueError):
            choices = [{"text": c.strip(), "jump": ""} for c in choices.split(",") if c.strip()]
    elif not isinstance(choices, list):
        choices = []
    
    for choice in choices:
        if isinstance(choice, dict):
            text = safe_get_str(choice, "text")
            jump = safe_get_str(choice, "jump")
            condition = safe_get_str(choice, "condition")
        else:
            text = str(choice).strip() if choice is not None else ""
            jump = ""
            condition = ""
        
        if not text:
            continue
        
        text = escape_text(text)
        
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


def generate_if(block: Block, indent: str, true_branch: Optional[str] = None, false_branch: Optional[str] = None) -> str:
    """Generate if statement"""
    condition = safe_get_str(block.params, "condition")
    if not condition:
        return ""
    
    lines: list[str] = []
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


def generate_while(block: Block, indent: str, loop_body: Optional[str] = None) -> str:
    """Generate while loop"""
    condition = safe_get_str(block.params, "condition")
    if not condition:
        return ""
    
    lines: list[str] = []
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


def generate_for(block: Block, indent: str, loop_body: Optional[str] = None) -> str:
    """Generate for loop"""
    var = safe_get_str(block.params, "variable")
    iterable = safe_get_str(block.params, "iterable")
    
    if not var or not iterable:
        return ""
    
    lines: list[str] = []
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


def generate_jump(block: Block, indent: str, generated_labels: Optional[set] = None) -> str:
    """Generate jump statement only if target label exists"""
    target = safe_get_str(block.params, "target")
    if not target:
        return ""
    
    # Проверяем, существует ли целевой label
    if generated_labels is not None:
        if target not in generated_labels:
            # Label не существует - не генерируем jump
            print(f"DEBUG generate_jump: target '{target}' не найден в generated_labels. Доступные: {sorted(generated_labels)}")
            return ""
        else:
            print(f"DEBUG generate_jump: target '{target}' найден в generated_labels, генерируем jump")
    
    return f"{indent}jump {target}\n"


def generate_call(block: Block, indent: str, generated_labels: Optional[set] = None) -> str:
    """Generate call statement only if target label exists"""
    label = safe_get_str(block.params, "label")
    if not label:
        return ""
    
    # Проверяем, существует ли целевой label
    if generated_labels is not None:
        if label not in generated_labels:
            # Label не существует - не генерируем call
            print(f"DEBUG generate_call: label '{label}' не найден в generated_labels. Доступные: {sorted(generated_labels)}")
            return ""
        else:
            print(f"DEBUG generate_call: label '{label}' найден в generated_labels, генерируем call")
    
    return f"{indent}call {label}\n"


def generate_return(block: Block, indent: str) -> str:
    """Generate return statement"""
    return f"{indent}return\n"


def generate_start(block: Block, indent: str, project_scenes: Optional[list] = None) -> str:
    """Generate start block with its own label"""
    # Пробуем разные варианты ключей для label
    label = safe_get_str(block.params, "label", "")
    if not label:
        label = safe_get_str(block.params, "Имя метки (label):", "")
    
    # Если лейбл не указан, не генерируем код
    if not label:
        return ""
    
    # Генерируем label для START блока
    return f"{indent}label {label}:\n"


def generate_scene(block: Block, indent: str) -> str:
    """Generate scene statement"""
    bg = safe_get_str(block.params, "background", "")
    # Если background не указан, используем "black" по умолчанию
    if not bg:
        bg = "black"
    
    layer = safe_get_str(block.params, "layer")
    if layer:
        bg = f"{bg} onlayer {layer}"
    
    trans = safe_get_str(block.params, "transition")
    line = f"{indent}scene {bg}"
    if trans:
        line += f" with {trans}"
    return line + "\n"


def generate_show(block: Block, indent: str) -> str:
    """Generate show statement"""
    char = safe_get_str(block.params, "character")
    if not char:
        return ""
    
    expr = safe_get_str(block.params, "expression")
    at = safe_get_str(block.params, "at")
    behind = safe_get_str(block.params, "behind")
    zorder = safe_get_str(block.params, "zorder")
    layer = safe_get_str(block.params, "layer")
    
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
    
    trans = safe_get_str(block.params, "transition")
    if trans:
        line += f" with {trans}"
    
    return line + "\n"


def generate_hide(block: Block, indent: str) -> str:
    """Generate hide statement"""
    char = safe_get_str(block.params, "character")
    if not char:
        return ""
    
    line = f"{indent}hide {char}"
    
    layer = safe_get_str(block.params, "layer")
    if layer:
        line += f" onlayer {layer}"
    
    trans = safe_get_str(block.params, "transition")
    if trans:
        line += f" with {trans}"
    
    return line + "\n"


def generate_image(block: Block, indent: str) -> str:
    """Generate image definition"""
    from renpy_node_editor.core.generator.main import normalize_variable_name
    
    name = safe_get_str(block.params, "name")
    path = safe_get_str(block.params, "path")
    
    if not name or not path:
        return ""
    
    # Нормализуем имя изображения (не может начинаться с цифры)
    normalized_name = normalize_variable_name(name)
    
    return f"{indent}image {normalized_name} = \"{path}\"\n"


def generate_pause(block: Block, indent: str) -> str:
    """Generate pause statement"""
    duration = safe_get_str(block.params, "duration", "1.0")
    try:
        float(duration)
        return f"{indent}$ renpy.pause({duration})\n"
    except ValueError:
        return f"{indent}$ renpy.pause(1.0)\n"


def generate_transition(block: Block, indent: str) -> str:
    """Generate transition statement"""
    trans = safe_get_str(block.params, "transition", "dissolve")
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def generate_with(block: Block, indent: str) -> str:
    """Generate with statement"""
    trans = safe_get_str(block.params, "transition", "dissolve")
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def generate_sound(block: Block, indent: str) -> str:
    """Generate play sound statement"""
    sound_file = safe_get_str(block.params, "sound_file")
    if not sound_file:
        return ""
    
    line = f"{indent}play sound \"{sound_file}\""
    
    fadein = safe_get_str(block.params, "fadein")
    fadeout = safe_get_str(block.params, "fadeout")
    loop = safe_get_str(block.params, "loop").lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if fadeout:
        line += f" fadeout {fadeout}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    
    return line + "\n"


def generate_music(block: Block, indent: str) -> str:
    """Generate play music statement"""
    music_file = safe_get_str(block.params, "music_file")
    if not music_file:
        return ""
    
    line = f"{indent}play music \"{music_file}\""
    
    fadein = safe_get_str(block.params, "fadein")
    fadeout = safe_get_str(block.params, "fadeout")
    loop = safe_get_str(block.params, "loop", "True").lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if fadeout:
        line += f" fadeout {fadeout}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    else:
        line += " noloop"
    
    return line + "\n"


def generate_stop_music(block: Block, indent: str) -> str:
    """Generate stop music statement"""
    fadeout = safe_get_str(block.params, "fadeout")
    if fadeout:
        return f"{indent}stop music fadeout {fadeout}\n"
    return f"{indent}stop music\n"


def generate_stop_sound(block: Block, indent: str) -> str:
    """Generate stop sound statement"""
    fadeout = safe_get_str(block.params, "fadeout")
    if fadeout:
        return f"{indent}stop sound fadeout {fadeout}\n"
    return f"{indent}stop sound\n"


def generate_queue_music(block: Block, indent: str) -> str:
    """Generate queue music statement"""
    music_file = safe_get_str(block.params, "music_file")
    if not music_file:
        return ""
    
    line = f"{indent}queue music \"{music_file}\""
    
    fadein = safe_get_str(block.params, "fadein")
    loop = safe_get_str(block.params, "loop").lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    
    return line + "\n"


def generate_queue_sound(block: Block, indent: str) -> str:
    """Generate queue sound statement"""
    sound_file = safe_get_str(block.params, "sound_file")
    if not sound_file:
        return ""
    
    line = f"{indent}queue sound \"{sound_file}\""
    
    fadein = safe_get_str(block.params, "fadein")
    if fadein:
        line += f" fadein {fadein}"
    
    return line + "\n"


def generate_set_var(block: Block, indent: str) -> str:
    """Generate variable assignment"""
    var = safe_get_str(block.params, "variable")
    value = safe_get_str(block.params, "value")
    
    if not var:
        return ""
    
    return f"{indent}$ {var} = {format_value(value)}\n"


def generate_default(block: Block, indent: str) -> str:
    """Generate default statement"""
    var = safe_get_str(block.params, "variable")
    value = safe_get_str(block.params, "value")
    
    if not var:
        return ""
    
    return f"{indent}default {var} = {format_value(value)}\n"


def generate_define(block: Block, indent: str) -> str:
    """Generate define statement"""
    name = safe_get_str(block.params, "name")
    value = safe_get_str(block.params, "value")
    
    if not name:
        return ""
    
    return f"{indent}define {name} = {format_value(value)}\n"


def generate_python(block: Block, indent: str) -> str:
    """Generate python code block"""
    code = safe_get_str(block.params, "code")
    if not code:
        return ""
    
    lines: list[str] = []
    lines.append(f"{indent}python:\n")
    
    for line in code.split('\n'):
        if line.strip():
            lines.append(f"{indent}{INDENT}{line}\n")
        else:
            lines.append("\n")
    
    return "".join(lines)


def normalize_variable_name(name: str) -> str:
    """
    Нормализует имя переменной для Ren'Py.
    Имена должны начинаться с буквы или подчеркивания, не с цифры.
    Поддерживает кириллицу и другие Unicode символы.
    """
    import re
    
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


def generate_character(block: Block, indent: str) -> str:
    """Generate character definition"""
    name = safe_get_str(block.params, "name")
    display_name = safe_get_str(block.params, "display_name")
    
    if not name:
        return ""
    
    # Нормализуем имя переменной (не может начинаться с цифры)
    normalized_name = normalize_variable_name(name)
    
    if display_name:
        display_name = display_name.replace("'", "\\'")
        return f"{indent}define {normalized_name} = Character('{display_name}')\n"
    else:
        return f"{indent}define {normalized_name} = Character(None)\n"


def generate_voice(block: Block, indent: str) -> str:
    """Generate voice statement"""
    voice_file = safe_get_str(block.params, "voice_file")
    if not voice_file:
        return ""
    
    return f"{indent}voice \"{voice_file}\"\n"


def generate_center(block: Block, indent: str) -> str:
    """Generate centered text"""
    text = safe_get_str(block.params, "text")
    if not text:
        return ""
    
    text = escape_text(text)
    return f"{indent}centered \"{text}\"\n"


def generate_text(block: Block, indent: str) -> str:
    """Generate text statement"""
    text = safe_get_str(block.params, "text")
    if not text:
        return ""
    
    text = escape_text(text)
    
    xpos = safe_get_str(block.params, "xpos")
    ypos = safe_get_str(block.params, "ypos")
    
    line = f"{indent}text \"{text}\""
    if xpos:
        line += f" xpos {xpos}"
    if ypos:
        line += f" ypos {ypos}"
    
    return line + "\n"


# Mapping BlockType to generator function
BLOCK_GENERATORS = {
    BlockType.SAY: generate_say,
    BlockType.NARRATION: generate_narration,
    BlockType.MENU: generate_menu,
    BlockType.JUMP: generate_jump,
    BlockType.CALL: generate_call,
    BlockType.RETURN: generate_return,
    BlockType.SCENE: generate_scene,
    BlockType.SHOW: generate_show,
    BlockType.HIDE: generate_hide,
    BlockType.IMAGE: generate_image,
    BlockType.PAUSE: generate_pause,
    BlockType.TRANSITION: generate_transition,
    BlockType.WITH: generate_with,
    BlockType.SOUND: generate_sound,
    BlockType.MUSIC: generate_music,
    BlockType.STOP_MUSIC: generate_stop_music,
    BlockType.STOP_SOUND: generate_stop_sound,
    BlockType.QUEUE_MUSIC: generate_queue_music,
    BlockType.QUEUE_SOUND: generate_queue_sound,
    BlockType.SET_VAR: generate_set_var,
    BlockType.DEFAULT: generate_default,
    BlockType.DEFINE: generate_define,
    BlockType.PYTHON: generate_python,
    BlockType.CHARACTER: generate_character,
    BlockType.VOICE: generate_voice,
    BlockType.CENTER: generate_center,
    BlockType.TEXT: generate_text,
}
