from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List

from renpy_node_editor.core.model import (
    Project,
    Scene,
    Block,
    BlockType,
    Port,
    PortDirection,
    Connection,
)

PROJECT_FILE = "project.json"


# ---- helpers: to_dict ----

def _block_to_dict(block: Block) -> Dict[str, Any]:
    return {
        "id": block.id,
        "type": block.type.name,
        "params": block.params,
        "x": block.x,
        "y": block.y,
        "port_ids": block.port_ids,
    }


def _port_to_dict(port: Port) -> Dict[str, Any]:
    return {
        "id": port.id,
        "node_id": port.node_id,
        "name": port.name,
        "direction": port.direction.name,
        "metadata": port.metadata,
    }


def _connection_to_dict(conn: Connection) -> Dict[str, Any]:
    return {
        "id": conn.id,
        "from_port_id": conn.from_port_id,
        "to_port_id": conn.to_port_id,
        "metadata": conn.metadata,
    }


def _scene_to_dict(scene: Scene) -> Dict[str, Any]:
    return {
        "id": scene.id,
        "name": scene.name,
        "label": scene.label,
        "blocks": [_block_to_dict(b) for b in scene.blocks],
        "ports": [_port_to_dict(p) for p in scene.ports],
        "connections": [_connection_to_dict(c) for c in scene.connections],
    }


def project_to_dict(project: Project) -> Dict[str, Any]:
    """
    Сохранить проект в словарь.
    Порядок сцен сохраняется (JSON сохраняет порядок списков).
    """
    return {
        "name": project.name,
        "variables": project.variables,
        "scenes": [_scene_to_dict(s) for s in project.scenes],  # Порядок сохраняется
    }


# ---- helpers: from_dict ----

def _block_from_dict(payload: Dict[str, Any]) -> Block:
    return Block(
        id=payload["id"],
        type=BlockType[payload["type"]],
        params=payload.get("params", {}),
        x=payload.get("x", 0.0),
        y=payload.get("y", 0.0),
        port_ids=list(payload.get("port_ids", [])),
    )


def _port_from_dict(payload: Dict[str, Any]) -> Port:
    return Port(
        id=payload["id"],
        node_id=payload["node_id"],
        name=payload.get("name", ""),
        direction=PortDirection[payload["direction"]],
        metadata=payload.get("metadata", {}),
    )


def _connection_from_dict(payload: Dict[str, Any]) -> Connection:
    return Connection(
        id=payload["id"],
        from_port_id=payload["from_port_id"],
        to_port_id=payload["to_port_id"],
        metadata=payload.get("metadata", {}),
    )


def _scene_from_dict(payload: Dict[str, Any]) -> Scene:
    blocks = [_block_from_dict(b) for b in payload.get("blocks", [])]
    ports = [_port_from_dict(p) for p in payload.get("ports", [])]
    connections = [
        _connection_from_dict(c) for c in payload.get("connections", [])
    ]
    
    # ВАЖНО: восстанавливаем связь портов с блоками через port_ids
    # Это нужно, так как при загрузке блоки и порты создаются отдельно
    block_map = {block.id: block for block in blocks}
    for port in ports:
        block = block_map.get(port.node_id)
        if block and port.id not in block.port_ids:
            block.port_ids.append(port.id)
    
    return Scene(
        id=payload["id"],
        name=payload.get("name", ""),
        label=payload.get("label", ""),
        blocks=blocks,
        ports=ports,
        connections=connections,
    )


def project_from_dict(payload: Dict[str, Any]) -> Project:
    """
    Загрузить проект из словаря.
    Порядок сцен сохраняется из JSON (списки в JSON сохраняют порядок).
    """
    scenes = [_scene_from_dict(s) for s in payload.get("scenes", [])]  # Порядок сохраняется
    return Project(
        name=payload.get("name", "Unnamed"),
        scenes=scenes,
        variables=payload.get("variables", {}),
    )


# ---- file IO ----

def save_project(project: Project, directory: Path) -> None:
    """
    Сохранить проект в JSON в указанной папке.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / PROJECT_FILE

    data = project_to_dict(project)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_project(directory: Path) -> Project:
    """
    Загрузить проект из project.json в указанной папке.
    """
    path = directory / PROJECT_FILE
    if not path.exists():
        raise FileNotFoundError(f"Проект не найден: {path}")

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    return project_from_dict(payload)
