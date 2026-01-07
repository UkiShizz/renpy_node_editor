"""Block code generators"""
from __future__ import annotations

from typing import Optional
from renpy_node_editor.core.model import Block, BlockType, Scene
from renpy_node_editor.core.generator.utils import INDENT, escape_text, format_value


def generate_label(scene: Scene) -> str:
    """Generate label statement"""
    return f"label {scene.label}:\n"


def generate_say(block: Block, indent: str) -> str:
    """Generate character dialogue"""
    who = block.params.get("who", "").strip()
    text = block.params.get("text", "").strip()
    
    if not text:
        return ""
    
    text = escape_text(text)
    
    attrs = []
    if who:
        expression = block.params.get("expression", "").strip()
        if expression:
            who = f"{who} {expression}"
        
        at_pos = block.params.get("at", "").strip()
        if at_pos:
            attrs.append(f"at {at_pos}")
        
        with_trans = block.params.get("with_transition", "").strip()
        if with_trans:
            attrs.append(f"with {with_trans}")
        
        result = f"{indent}{who} \"{text}\""
        if attrs:
            result += " " + " ".join(attrs)
        return result + "\n"
    
    return f"{indent}\"{text}\"\n"


def generate_narration(block: Block, indent: str) -> str:
    """Generate narration text"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = escape_text(text)
    with_trans = block.params.get("with_transition", "").strip()
    
    if with_trans:
        return f"{indent}\"{text}\" with {with_trans}\n"
    
    return f"{indent}\"{text}\"\n"


def generate_menu(block: Block, indent: str) -> str:
    """Generate menu with choices"""
    lines: list[str] = []
    question = block.params.get("question", "").strip()
    
    if question:
        question = escape_text(question)
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
    
    for choice in choices:
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
    condition = block.params.get("condition", "").strip()
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
    condition = block.params.get("condition", "").strip()
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
    var = block.params.get("variable", "").strip()
    iterable = block.params.get("iterable", "").strip()
    
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


def generate_jump(block: Block, indent: str) -> str:
    """Generate jump statement"""
    target = block.params.get("target", "").strip()
    if not target:
        return ""
    return f"{indent}jump {target}\n"


def generate_call(block: Block, indent: str) -> str:
    """Generate call statement"""
    label = block.params.get("label", "").strip()
    if not label:
        return ""
    return f"{indent}call {label}\n"


def generate_return(block: Block, indent: str) -> str:
    """Generate return statement"""
    return f"{indent}return\n"


def generate_scene(block: Block, indent: str) -> str:
    """Generate scene statement"""
    bg = block.params.get("background", "black").strip()
    if not bg:
        bg = "black"
    
    layer = block.params.get("layer", "").strip()
    if layer:
        bg = f"{bg} onlayer {layer}"
    
    trans = block.params.get("transition", "").strip()
    line = f"{indent}scene {bg}"
    if trans:
        line += f" with {trans}"
    return line + "\n"


def generate_show(block: Block, indent: str) -> str:
    """Generate show statement"""
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


def generate_hide(block: Block, indent: str) -> str:
    """Generate hide statement"""
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


def generate_image(block: Block, indent: str) -> str:
    """Generate image definition"""
    name = block.params.get("name", "").strip()
    path = block.params.get("path", "").strip()
    
    if not name or not path:
        return ""
    
    return f"{indent}image {name} = \"{path}\"\n"


def generate_pause(block: Block, indent: str) -> str:
    """Generate pause statement"""
    duration = block.params.get("duration", "1.0")
    try:
        float(duration)
        return f"{indent}$ renpy.pause({duration})\n"
    except ValueError:
        return f"{indent}$ renpy.pause(1.0)\n"


def generate_transition(block: Block, indent: str) -> str:
    """Generate transition statement"""
    trans = block.params.get("transition", "dissolve").strip()
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def generate_with(block: Block, indent: str) -> str:
    """Generate with statement"""
    trans = block.params.get("transition", "dissolve").strip()
    if not trans:
        trans = "dissolve"
    return f"{indent}with {trans}\n"


def generate_sound(block: Block, indent: str) -> str:
    """Generate play sound statement"""
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


def generate_music(block: Block, indent: str) -> str:
    """Generate play music statement"""
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


def generate_stop_music(block: Block, indent: str) -> str:
    """Generate stop music statement"""
    fadeout = block.params.get("fadeout", "").strip()
    if fadeout:
        return f"{indent}stop music fadeout {fadeout}\n"
    return f"{indent}stop music\n"


def generate_stop_sound(block: Block, indent: str) -> str:
    """Generate stop sound statement"""
    fadeout = block.params.get("fadeout", "").strip()
    if fadeout:
        return f"{indent}stop sound fadeout {fadeout}\n"
    return f"{indent}stop sound\n"


def generate_queue_music(block: Block, indent: str) -> str:
    """Generate queue music statement"""
    music_file = block.params.get("music_file", "").strip()
    if not music_file:
        return ""
    
    line = f"{indent}queue music \"{music_file}\""
    
    fadein = block.params.get("fadein", "").strip()
    loop = block.params.get("loop", "").strip().lower()
    
    if fadein:
        line += f" fadein {fadein}"
    if loop in ("true", "1", "yes"):
        line += " loop"
    
    return line + "\n"


def generate_queue_sound(block: Block, indent: str) -> str:
    """Generate queue sound statement"""
    sound_file = block.params.get("sound_file", "").strip()
    if not sound_file:
        return ""
    
    line = f"{indent}queue sound \"{sound_file}\""
    
    fadein = block.params.get("fadein", "").strip()
    if fadein:
        line += f" fadein {fadein}"
    
    return line + "\n"


def generate_set_var(block: Block, indent: str) -> str:
    """Generate variable assignment"""
    var = block.params.get("variable", "").strip()
    value = block.params.get("value", "").strip()
    
    if not var:
        return ""
    
    return f"{indent}$ {var} = {format_value(value)}\n"


def generate_default(block: Block, indent: str) -> str:
    """Generate default statement"""
    var = block.params.get("variable", "").strip()
    value = block.params.get("value", "").strip()
    
    if not var:
        return ""
    
    return f"{indent}default {var} = {format_value(value)}\n"


def generate_define(block: Block, indent: str) -> str:
    """Generate define statement"""
    name = block.params.get("name", "").strip()
    value = block.params.get("value", "").strip()
    
    if not name:
        return ""
    
    return f"{indent}define {name} = {format_value(value)}\n"


def generate_python(block: Block, indent: str) -> str:
    """Generate python code block"""
    code = block.params.get("code", "").strip()
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


def generate_character(block: Block, indent: str) -> str:
    """Generate character definition"""
    name = block.params.get("name", "").strip()
    display_name = block.params.get("display_name", "").strip()
    
    if not name:
        return ""
    
    if display_name:
        display_name = display_name.replace("'", "\\'")
        return f"{indent}define {name} = Character('{display_name}')\n"
    else:
        return f"{indent}define {name} = Character(None)\n"


def generate_voice(block: Block, indent: str) -> str:
    """Generate voice statement"""
    voice_file = block.params.get("voice_file", "").strip()
    if not voice_file:
        return ""
    
    return f"{indent}voice \"{voice_file}\"\n"


def generate_center(block: Block, indent: str) -> str:
    """Generate centered text"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = escape_text(text)
    return f"{indent}centered \"{text}\"\n"


def generate_text(block: Block, indent: str) -> str:
    """Generate text statement"""
    text = block.params.get("text", "").strip()
    if not text:
        return ""
    
    text = escape_text(text)
    
    xpos = block.params.get("xpos", "").strip()
    ypos = block.params.get("ypos", "").strip()
    
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
