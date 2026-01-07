from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, List, Optional


class BlockType(Enum):
    """
    Типы нод для Ren'Py.
    Пока базовый набор, дальше допилим IF, CALL, RETURN и прочую поебень.
    """
    LABEL = auto()
    SAY = auto()
    MENU = auto()
    JUMP = auto()
    SCENE = auto()
    SHOW = auto()


class PortDirection(Enum):
    INPUT = auto()
    OUTPUT = auto()


@dataclass
class Port:
    """
    Логический порт ноды (вход/выход).
    Для визуала это будет кружочек на ноде.
    """
    id: str
    node_id: str
    name: str
    direction: PortDirection
    # На будущее можно сюда сунуть тип данных, цвет, иконку и т.п.
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """
    Соединение между портами — тот самый "провод".
    """
    id: str
    from_port_id: str
    to_port_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Block:
    """
    Одна нода (блок) в графе сцены.
    """
    id: str
    type: BlockType
    # Параметры блока — текст, персонаж, список вариантов меню и т.п.
    params: Dict[str, Any] = field(default_factory=dict)

    # Позиция на рабочем поле (для UI, но хранится тут, чтобы сериализовать проект).
    x: float = 0.0
    y: float = 0.0

    # Порты ноды (входы/выходы).
    port_ids: List[str] = field(default_factory=list)


@dataclass
class Scene:
    """
    Сцена — отдельный граф нод (блоков).
    Например, один label в Ren'Py.
    """
    id: str
    name: str
    label: str

    # Ноды и связи
    blocks: List[Block] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)
    connections: List[Connection] = field(default_factory=list)

    def find_block(self, block_id: str) -> Optional[Block]:
        for b in self.blocks:
            if b.id == block_id:
                return b
        return None

    def find_port(self, port_id: str) -> Optional[Port]:
        for p in self.ports:
            if p.id == port_id:
                return p
        return None

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)

    def remove_block(self, block_id: str) -> None:
        self.blocks = [b for b in self.blocks if b.id != block_id]
        # Заодно удаляем порты и коннекты, связанные с нодой
        removed_ports = {p.id for p in self.ports if p.node_id == block_id}
        self.ports = [p for p in self.ports if p.node_id != block_id]
        self.connections = [
            c for c in self.connections
            if c.from_port_id not in removed_ports and c.to_port_id not in removed_ports
        ]

    def add_port(self, port: Port) -> None:
        self.ports.append(port)
        block = self.find_block(port.node_id)
        if block and port.id not in block.port_ids:
            block.port_ids.append(port.id)

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)

    def remove_connection(self, connection_id: str) -> None:
        self.connections = [c for c in self.connections if c.id != connection_id]


@dataclass
class Project:
    """
    Весь проект визуальной новеллы.
    """
    name: str
    scenes: List[Scene] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)

    def find_scene(self, scene_id: str) -> Optional[Scene]:
        for s in self.scenes:
            if s.id == scene_id:
                return s
        return None

    def add_scene(self, scene: Scene) -> None:
        self.scenes.append(scene)

    def remove_scene(self, scene_id: str) -> None:
        self.scenes = [s for s in self.scenes if s.id != scene_id]
