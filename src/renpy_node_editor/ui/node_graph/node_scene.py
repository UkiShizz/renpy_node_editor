from __future__ import annotations

from typing import Optional
import uuid

from PySide6.QtCore import QRectF, Qt, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsSceneDragDropEvent, QGraphicsSceneMouseEvent,
    QGraphicsSceneContextMenuEvent, QMenu, QMessageBox, QGraphicsItem
)

from renpy_node_editor.core.model import Project, Scene, Block, BlockType, Connection, Port, PortDirection
from renpy_node_editor.ui.block_palette import MIME_NODE_TYPE
from renpy_node_editor.ui.node_graph.node_item import NodeItem
from renpy_node_editor.ui.node_graph.port_item import PortItem
from renpy_node_editor.ui.node_graph.connection_item import ConnectionItem


GRID_SMALL = 20
GRID_BIG = 100


class NodeScene(QGraphicsScene):
    """
    Professional node editor scene:
    - modern grid design
    - better background
    - smooth visuals
    """
    
    # Signal emitted when a node is selected/deselected
    node_selection_changed = Signal(object)  # emits Block or None

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._project: Optional[Project] = None
        self._scene_model: Optional[Scene] = None

        # Современная темная тема с бесконечной областью
        self.setBackgroundBrush(QColor("#1E1E1E"))
        self.setItemIndexMethod(QGraphicsScene.NoIndex)
        # Бесконечная рабочая область (очень большой размер)
        self.setSceneRect(-100000, -100000, 200000, 200000)

        self._drag_connection: Optional[ConnectionItem] = None
        self._drag_src_port: Optional[PortItem] = None
        
        # Флаг для предотвращения одновременных вызовов set_project_and_scene
        self._is_loading = False
        
        # Connect selection changed signal
        self.selectionChanged.connect(self._on_selection_changed)

    # ---- binding to model ----

    def set_project_and_scene(self, project: Project, scene: Scene) -> None:
        """Установить проект и сцену, очистить и пересоздать визуальные элементы"""
        # Защита от одновременных вызовов
        if self._is_loading:
            return
        
        self._is_loading = True
        try:
            # Блокируем сигналы во время очистки (включая selectionChanged)
            self.blockSignals(True)
            
            # Отключаем обработчик selectionChanged временно
            try:
                self.selectionChanged.disconnect(self._on_selection_changed)
            except (TypeError, RuntimeError):
                pass
            
            # Очищаем выделение перед очисткой элементов
            try:
                self.clearSelection()
            except Exception:
                pass
            
            # Очищаем состояние перетаскивания
            if self._drag_connection:
                try:
                    if self._drag_connection.scene() == self:
                        self.removeItem(self._drag_connection)
                except Exception:
                    pass
                self._drag_connection = None
            self._drag_src_port = None
            
            # Безопасно очищаем все элементы
            try:
                # Сначала получаем список всех элементов
                items = list(self.items())
                
                # Отключаем геометрические обновления для всех элементов перед удалением
                for item in items:
                    if isinstance(item, NodeItem):
                        try:
                            # Отключаем флаги, которые вызывают itemChange
                            item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
                            # Отключаем обновление позиции для всех портов
                            for port in item.inputs + item.outputs:
                                if port:
                                    try:
                                        port.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, False)
                                    except Exception:
                                        pass
                                    if hasattr(port, 'connections'):
                                        # Очищаем список соединений без вызова методов обновления
                                        try:
                                            port.connections.clear()
                                        except Exception:
                                            pass
                        except Exception:
                            pass
                
                # Используем clear() для полной очистки - это безопаснее, чем ручное удаление
                # clear() удаляет все элементы сразу и предотвращает каскадные обновления
                self.clear()
            except Exception:
                # Если clear() не сработал, пытаемся удалить вручную
                try:
                    items = list(self.items())
                    for item in items:
                        try:
                            if item.scene() == self:
                                self.removeItem(item)
                        except (RuntimeError, AttributeError):
                            pass
                except Exception:
                    pass
            
            # Устанавливаем новую модель
            self._project = project
            self._scene_model = scene
            
            # Подключаем обработчик selectionChanged обратно
            try:
                self.selectionChanged.connect(self._on_selection_changed)
            except (TypeError, RuntimeError):
                pass
            
            # Создаем блоки
            for block in scene.blocks:
                try:
                    node_item = self._create_node_item_for_block(block)
                    # Включаем обратно флаги для новых элементов
                    if node_item:
                        node_item.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
                        for port in node_item.inputs + node_item.outputs:
                            if port:
                                try:
                                    port.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
                                except Exception:
                                    pass
                except Exception:
                    continue
            
            # Создаем связи
            try:
                self._create_connections()
            except Exception:
                pass
        except Exception:
            # Устанавливаем модель даже при ошибке
            try:
                self._project = project
                self._scene_model = scene
            except Exception:
                pass
        finally:
            # Разблокируем сигналы
            try:
                self.blockSignals(False)
            except Exception:
                pass
            self._is_loading = False

    def _create_node_item_for_block(self, block: Block) -> NodeItem:
        item = NodeItem(block)
        self.addItem(item)
        return item
    
    def _find_parent_node_item(self, item: QGraphicsItem) -> Optional[NodeItem]:
        """Найти родительский NodeItem для элемента (например, порта)"""
        if isinstance(item, NodeItem):
            return item
        
        parent = item.parentItem()
        while parent:
            if isinstance(parent, NodeItem):
                return parent
            parent = parent.parentItem()
        
        return None
    
    def _create_connections(self) -> None:
        """Создать визуальные связи из модели"""
        if not self._scene_model or self._is_loading:
            return
        
        # Создаем маппинг port_id -> PortItem
        port_items: dict[str, PortItem] = {}
        try:
            items = list(self.items())
            for item in items:
                if isinstance(item, NodeItem):
                    try:
                        # Проверяем, что элемент еще в сцене
                        if not item.scene() or not item.block:
                            continue
                        # Проверяем, что блок еще существует в модели
                        if not self._scene_model.find_block(item.block.id):
                            continue
                        
                        for port in item.inputs + item.outputs:
                            # Проверяем, что порт еще существует
                            if not port:
                                continue
                            try:
                                if not port.scene():
                                    continue
                            except (RuntimeError, AttributeError):
                                continue
                            
                            # Нужно найти port_id для этого порта
                            # Для этого создадим порты в модели если их нет
                            try:
                                port_id = self._get_or_create_port_id(item.block, port)
                                port_items[port_id] = port
                            except Exception:
                                continue
                    except (RuntimeError, AttributeError):
                        continue
            
            # Создаем связи
            for conn in self._scene_model.connections:
                try:
                    src_port_item = port_items.get(conn.from_port_id)
                    dst_port_item = port_items.get(conn.to_port_id)
                    
                    if src_port_item and dst_port_item:
                        # Проверяем, что порты еще в сцене
                        try:
                            if not src_port_item.scene() or not dst_port_item.scene():
                                continue
                        except (RuntimeError, AttributeError):
                            continue
                        
                        try:
                            connection_item = ConnectionItem(
                                src_port=src_port_item,
                                dst_port=dst_port_item,
                                connection_id=conn.id
                            )
                            self.addItem(connection_item)
                            src_port_item.add_connection(connection_item)
                            dst_port_item.add_connection(connection_item)
                        except Exception:
                            continue
                except (AttributeError, RuntimeError):
                    continue
        except Exception:
            pass
    
    def _get_or_create_port_id(self, block: Block, port_item: PortItem) -> str:
        """Получить или создать port_id для порта"""
        if not self._scene_model:
            import uuid
            return str(uuid.uuid4())
        
        if not block:
            import uuid
            return str(uuid.uuid4())
        
        # Ищем существующий порт по имени и направлению для этого блока
        is_output = port_item.is_output
        for port in self._scene_model.ports:
            if port.node_id == block.id and port.name == port_item.name:
                # Проверяем по направлению
                if (port.direction == PortDirection.OUTPUT and is_output) or \
                   (port.direction == PortDirection.INPUT and not is_output):
                    return port.id
        
        # Создаем новый порт
        import uuid
        port_id = str(uuid.uuid4())
        port = Port(
            id=port_id,
            node_id=block.id,
            name=port_item.name,
            direction=PortDirection.OUTPUT if port_item.is_output else PortDirection.INPUT
        )
        self._scene_model.add_port(port)
        return port_id

    # ---- grid ----

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:  # type: ignore[override]
        """Отрисовка фона и сетки"""
        # Рисуем базовый фон
        painter.fillRect(rect, QBrush(QColor("#1E1E1E")))
        
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)

        # Мелкая сетка - более контрастная
        self._draw_grid_lines(painter, rect, GRID_SMALL, QColor("#2D2D2D"), 1)
        
        # Крупная сетка - еще более заметная
        self._draw_grid_lines(painter, rect, GRID_BIG, QColor("#3D3D3D"), 2)
        
        # Центральные линии - самые заметные
        painter.setPen(QPen(QColor("#5A5A5A"), 3))
        if rect.left() <= 0 <= rect.right():
            painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))
        if rect.top() <= 0 <= rect.bottom():
            painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
    
    def _draw_grid_lines(self, painter: QPainter, rect: QRectF, step: int, color: QColor, width: int) -> None:
        """Вспомогательный метод для отрисовки линий сетки"""
        painter.setPen(QPen(color, width))
        
        # Вертикальные линии
        left = int(rect.left()) - (int(rect.left()) % step)
        x = left
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += step

        # Горизонтальные линии
        top = int(rect.top()) - (int(rect.top()) % step)
        y = top
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += step

    # ---- drag&drop from palette ----

    def dragEnterEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasFormat(MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if mime.hasFormat(MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QGraphicsSceneDragDropEvent) -> None:  # type: ignore[override]
        mime = event.mimeData()
        if not mime.hasFormat(MIME_NODE_TYPE):
            event.ignore()
            return

        if not self._scene_model:
            event.ignore()
            return

        data = mime.data(MIME_NODE_TYPE)
        if not data:
            event.ignore()
            return

        block_type_name = bytes(data).decode("utf-8")

        try:
            block_type = BlockType[block_type_name]
        except KeyError:
            event.ignore()
            return

        pos: QPointF = event.scenePos()

        block = Block(
            id=str(uuid.uuid4()),
            type=block_type,
            params={},
            x=pos.x(),
            y=pos.y(),
        )
        self._scene_model.add_block(block)

        self._create_node_item_for_block(block)

        event.acceptProposedAction()

    # ---- connections with mouse ----

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        view = self.views()[0] if self.views() else None
        item = self.itemAt(event.scenePos(), view.transform()) if view else None

        if event.button() == Qt.LeftButton and isinstance(item, PortItem) and item.is_output:
            self._drag_src_port = item
            self._drag_connection = ConnectionItem(src_port=item)
            self.addItem(self._drag_connection)
            self._drag_connection.set_tmp_end(event.scenePos())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        if self._drag_connection is not None:
            self._drag_connection.set_tmp_end(event.scenePos())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:  # type: ignore[override]
        if self._drag_connection is not None and self._drag_src_port is not None:
            view = self.views()[0] if self.views() else None
            item = self.itemAt(event.scenePos(), view.transform()) if view else None

            if isinstance(item, PortItem) and not item.is_output:
                # Создаем связь в модели
                if self._scene_model:
                    # Получаем блоки из портов
                    src_node = self._find_parent_node_item(self._drag_src_port)
                    dst_node = self._find_parent_node_item(item)
                    
                    from_port_id = self._get_or_create_port_id(
                        src_node.block if src_node else None,
                        self._drag_src_port
                    )
                    to_port_id = self._get_or_create_port_id(
                        dst_node.block if dst_node else None,
                        item
                    )
                    
                    connection_id = str(id(self._drag_connection))
                    connection = Connection(
                        id=connection_id,
                        from_port_id=from_port_id,
                        to_port_id=to_port_id
                    )
                    self._scene_model.add_connection(connection)
                    self._drag_connection.connection_id = connection_id
                
                self._drag_connection.set_dst_port(item)
                self._drag_src_port.add_connection(self._drag_connection)
                item.add_connection(self._drag_connection)
            else:
                self.removeItem(self._drag_connection)
                del self._drag_connection

            self._drag_connection = None
            self._drag_src_port = None
            event.accept()
            return

        super().mouseReleaseEvent(event)
    
    # ---- selection handling ----
    
    def _on_selection_changed(self) -> None:
        """Handle selection changes and emit signal with selected block"""
        # Игнорируем изменения выделения во время загрузки
        if self._is_loading:
            return
        
        try:
            # Проверяем, что сцена еще существует
            if not self._scene_model:
                try:
                    self.node_selection_changed.emit(None)
                except (RuntimeError, AttributeError):
                    pass
                return
            
            try:
                selected_items = self.selectedItems()
            except (RuntimeError, AttributeError):
                try:
                    self.node_selection_changed.emit(None)
                except (RuntimeError, AttributeError):
                    pass
                return
            
            if selected_items:
                # Get the first selected item
                item = selected_items[0]
                try:
                    # Проверяем, что элемент еще в сцене
                    if not item or not item.scene():
                        try:
                            self.node_selection_changed.emit(None)
                        except (RuntimeError, AttributeError):
                            pass
                        return
                    
                    if isinstance(item, NodeItem):
                        try:
                            # Проверяем, что блок еще существует в модели
                            if item.block and self._scene_model.find_block(item.block.id):
                                self.node_selection_changed.emit(item.block)
                            else:
                                self.node_selection_changed.emit(None)
                        except (AttributeError, RuntimeError):
                            try:
                                self.node_selection_changed.emit(None)
                            except (RuntimeError, AttributeError):
                                pass
                    else:
                        try:
                            self.node_selection_changed.emit(None)
                        except (RuntimeError, AttributeError):
                            pass
                except (AttributeError, RuntimeError):
                    try:
                        self.node_selection_changed.emit(None)
                    except (RuntimeError, AttributeError):
                        pass
            else:
                try:
                    self.node_selection_changed.emit(None)
                except (RuntimeError, AttributeError):
                    pass
        except Exception:
            # В случае ошибки просто эмитим None
            try:
                self.node_selection_changed.emit(None)
            except (RuntimeError, AttributeError):
                pass
    
    # ---- deletion ----
    
    def delete_selected_blocks(self) -> None:
        """Удалить выбранные блоки"""
        selected_items = [item for item in self.selectedItems() if isinstance(item, NodeItem)]
        if not selected_items:
            return
        
        if not self._scene_model:
            return
        
        # Подтверждение удаления
        count = len(selected_items)
        if count == 1:
            block_name = selected_items[0].block.type.name
            message = f"Вы уверены, что хотите удалить блок '{block_name}'?"
        else:
            message = f"Вы уверены, что хотите удалить {count} блоков?"
        
        reply = QMessageBox.question(
            None,  # Используем None чтобы диалог был модальным
            "Удаление блоков",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                # Сначала очищаем все связи от портов
                for port in item.inputs + item.outputs:
                    # Создаем копию списка connections
                    connections_copy = list(port.connections)
                    for conn in connections_copy:
                        # Удаляем связь из модели
                        if conn.connection_id and self._scene_model:
                            self._scene_model.remove_connection(conn.connection_id)
                        # Отсоединяем от портов
                        if conn.src_port and conn in conn.src_port.connections:
                            conn.src_port.remove_connection(conn)
                        if conn.dst_port and conn in conn.dst_port.connections:
                            conn.dst_port.remove_connection(conn)
                        # Удаляем визуально
                        if conn in self.items():
                            self.removeItem(conn)
                
                # Удаляем из модели (это также удалит порты)
                self._scene_model.remove_block(item.block.id)
                # Удаляем визуально
                self.removeItem(item)
    
    def delete_connection(self, connection_item: ConnectionItem) -> None:
        """Удалить связь"""
        if not self._scene_model or not connection_item.connection_id:
            return
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            None,
            "Удаление связи",
            "Вы уверены, что хотите удалить эту связь?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Удаляем из модели
            self._scene_model.remove_connection(connection_item.connection_id)
            
            # Отсоединяем от портов
            if connection_item.src_port:
                connection_item.src_port.remove_connection(connection_item)
            if connection_item.dst_port:
                connection_item.dst_port.remove_connection(connection_item)
            
            # Удаляем визуально
            self.removeItem(connection_item)
    
    # ---- context menu ----
    
    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:  # type: ignore[override]
        """Обработка контекстного меню (ПКМ)"""
        view = self.views()[0] if self.views() else None
        item = self.itemAt(event.scenePos(), view.transform()) if view else None
        
        # Если клик был на порте или другом дочернем элементе, находим родительский NodeItem
        if item and not isinstance(item, NodeItem) and not isinstance(item, ConnectionItem):
            parent = item.parentItem()
            while parent:
                if isinstance(parent, NodeItem):
                    item = parent
                    break
                parent = parent.parentItem()
        
        if isinstance(item, NodeItem):
            # Выбираем блок если он не выбран
            if not item.isSelected():
                self.clearSelection()
                item.setSelected(True)
            
            # Контекстное меню для блока
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2A2A2A;
                    border: 2px solid #3A3A3A;
                    border-radius: 6px;
                    color: #E0E0E0;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 24px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #4A90E2;
                    color: #FFFFFF;
                }
            """)
            delete_action = menu.addAction("🗑️ Удалить блок")
            delete_action.setToolTip("Удалить выбранный блок из сцены")
            delete_action.triggered.connect(lambda: self.delete_selected_blocks())
            menu.exec(event.screenPos())
        elif isinstance(item, ConnectionItem):
            # Контекстное меню для связи
            menu = QMenu()
            menu.setStyleSheet("""
                QMenu {
                    background-color: #2A2A2A;
                    border: 2px solid #3A3A3A;
                    border-radius: 6px;
                    color: #E0E0E0;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 8px 24px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #4A90E2;
                    color: #FFFFFF;
                }
            """)
            delete_action = menu.addAction("🗑️ Удалить связь")
            delete_action.setToolTip("Удалить связь между блоками")
            delete_action.triggered.connect(lambda: self.delete_connection(item))
            menu.exec(event.screenPos())