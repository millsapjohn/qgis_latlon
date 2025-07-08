from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsGeometry,
    QgsPoint,
    QgsLineString,
    QgsApplication,
)
from qgis.gui import (
    QgsMapToolEmitPoint,
    QgsRubberBand,
    QgsMapToolPan,
)
from qgis.utils import iface
try:
    from qgis.PyQt.QtWidgets import QAction
except ImportError:
    from qgis.PyQt.QtGui import QAction
from qgis.PyQt.QtWidgets import (
    QLineEdit,
)
from qgis.PyQt.QtGui import QCursor, QIcon, QColor
from qgis.PyQt.QtCore import Qt, QPoint
import math

launch_icon = QIcon(':/images/themes/default/mActionFindReplace.svg')


class LatLonPlugin:
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.launch_action = None
        self.project = QgsProject.instance()
        self.initGui()

    def initGui(self):
        self.launch_action = QAction(launch_icon, "Launch 4326 Viewer")
        self.launch_action.triggered.connect(self.launch)
        self.iface.addToolBarIcon(self.launch_action)
        self.LatLonTool = LatLonMapTool(self.iface.mapCanvas(), self.iface)

    def unload(self):
        self.iface.removeToolBarIcon(self.launch_action)
        self.LatLonTool = None

    def launch(self):
        if isinstance(self.iface.mapCanvas().mapTool(), LatLonMapTool):
            self.iface.messageBar().clearWidgets()
            self.panTool = QgsMapToolPan(self.iface.mapCanvas())
            self.iface.mapCanvas().setMapTool(self.panTool)
        else:
            self.iface.mapCanvas().setMapTool(self.LatLonTool)


class LatLonMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, iface):
        self.canvas = canvas
        self.target_crs = QgsCoordinateReferenceSystem(
            'EPSG:4326'
        )
        self.iface = iface
        self.project = QgsProject.instance()
        self.project.readProject.connect(self.getCrs)
        self.project.crsChanged.connect(self.getCrs)
        self.crs = QgsCoordinateReferenceSystem(
            self.project.crs().authid()
        )
        self.transform = QgsCoordinateTransform(
            self.crs,
            self.target_crs,
            self.project
        )
        self.iface = iface
        self.instance = QgsApplication.instance()
        super().__init__(self.canvas)

    def activate(self):
        self.cursor = QCursor()
        self.cursor.setShape(Qt.BlankCursor)
        self.setCursor(self.cursor)
        self.icon = QgsRubberBand(self.canvas)
        self.icon.setColor(QColor(0, 0, 0))
        self.init_x = self.canvas.mouseLastXY().x()
        self.init_y = self.canvas.mouseLastXY().y()
        self.drawCursor(self.canvas, self.icon, self.init_x, self.init_y)
        self.cursor_bar_1 = QLineEdit(self.canvas)
        self.cursor_bar_1.resize(180, 20)
        self.cursor_bar_2 = QLineEdit(self.canvas)
        self.cursor_bar_2.resize(180, 20)
        self.cursor_bar_3 = QLineEdit(self.canvas)
        self.cursor_bar_3.resize(180, 20)
        self.cursor_bar_4 = QLineEdit(self.canvas)
        self.cursor_bar_4.resize(180, 20)
        self.cursor_bar_1.move(
            QPoint(
                (self.canvas.mouseLastXY().x() + 10),
                (self.canvas.mouseLastXY().y() + 10)
            )
        )
        self.cursor_bar_2.move(
            QPoint(
                (self.canvas.mouseLastXY().x() + 190),
                (self.canvas.mouseLastXY().y() + 10)
            )
        )
        self.cursor_bar_3.move(
            QPoint(
                (self.canvas.mouseLastXY().x() + 10),
                (self.canvas.mouseLastXY().y() + 30)
            )
        )
        self.cursor_bar_4.move(
            QPoint(
                (self.canvas.mouseLastXY().x() + 190),
                (self.canvas.mouseLastXY().y() + 30)
            )
        )
        self.cursor_bar_1.show()
        self.cursor_bar_2.show()
        self.cursor_bar_3.show()
        self.cursor_bar_4.show()

    def deactivate(self):
        self.cursor_bar_1.hide()
        self.cursor_bar_2.hide()
        self.cursor_bar_3.hide()
        self.cursor_bar_4.hide()
        self.icon.reset()
        super().deactivate()
        self.deactivated.emit()

    def canvasPressEvent(self, e):
        self.iface.messageBar().clearWidgets()
        final_str = self.y_str_1 + " " + self.x_str_1 + " " + self.y_str_2 + " " + self.x_str_2
        self.iface.messageBar().pushMessage(final_str, duration=0)
        self.instance.clipboard().setText(final_str)

    def canvasMoveEvent(self, e):
        self.drawCursor(self.canvas, self.icon, e.pixelPoint().x(), e.pixelPoint().y())
        self.cursor_bar_1.move(
            QPoint(
                (e.pixelPoint().x() + 10),
                (e.pixelPoint().y() + 10),
            )
        )
        self.cursor_bar_2.move(
            QPoint(
                (e.pixelPoint().x() + 190),
                (e.pixelPoint().y() + 10),
            )
        )
        self.cursor_bar_3.move(
            QPoint(
                (e.pixelPoint().x() + 10),
                (e.pixelPoint().y() + 30)
            )
        )
        self.cursor_bar_4.move(
            QPoint(
                (e.pixelPoint().x() + 190),
                (e.pixelPoint().y() + 30)
            )
        )
        raw_pt = QgsPoint(e.mapPoint().x(), e.mapPoint().y())
        raw_geom = QgsGeometry.fromPoint(raw_pt)
        raw_geom.transform(self.transform)
        new_pt = raw_geom.asPoint()
        
        self.cursor_bar_1.setText(str(new_pt.y()) + ' Lat')
        self.cursor_bar_2.setText(str(new_pt.x()) + ' Lon')
        
        y_part_1 = math.modf(new_pt.y())[1]
        y_parts_23 = abs(math.modf(new_pt.y())[0] * 60)
        y_part_2 = math.modf(y_parts_23)[1]
        y_part_3 = math.modf(y_parts_23)[0] * 60
        x_part_1 = math.modf(new_pt.x())[1]
        x_parts_23 = abs(math.modf(new_pt.x())[0] * 60)
        x_part_2 = math.modf(x_parts_23)[1]
        x_part_3 = math.modf(x_parts_23)[0] * 60
        
        self.y_str_1 = str(new_pt.y()) + ' Lat'
        self.x_str_1 = str(new_pt.x()) + ' Lon'
        self.y_str_2 = f'{int(y_part_1)}° {int(y_part_2)}\' {round(y_part_3, 4)}\" Lat'
        self.x_str_2 = f'{int(x_part_1)}° {int(x_part_2)}\' {round(x_part_3, 4)}\" Lon'

        self.cursor_bar_3.setText(self.y_str_2)
        self.cursor_bar_4.setText(self.x_str_2)

    def getCrs(self):
        self.project = QgsProject.instance()
        self.crs = QgsCoordinateReferenceSystem(
            self.project.crs().authid()
        )
        self.transform = QgsCoordinateTransform(
            self.crs,
            self.target_crs,
            self.project
        )    
    
    def drawCursor(self, canvas, icon, pixelx, pixely):
        icon.reset()
        xmax = canvas.extent().xMaximum()
        xmin = canvas.extent().xMinimum()
        ymax = canvas.extent().yMaximum()
        ymin = canvas.extent().yMinimum()
        factor = canvas.mapUnitsPerPixel()
        box_size = factor * 2
        crosshair_size = factor * 100
        mapx = (pixelx * factor) + xmin
        mapy = ymax - (pixely * factor)
        pos = QgsPoint(mapx, mapy)
        box_left = QgsGeometry(
            QgsLineString(
                QgsPoint((mapx - box_size), (mapy - box_size)),
                QgsPoint((mapx - box_size), (mapy + box_size)),
            )
        )
        box_right = QgsGeometry(
            QgsLineString(
                QgsPoint((mapx + box_size), (mapy - box_size)),
                QgsPoint((mapx + box_size), (mapy + box_size)),
            )
        )
        box_top = QgsGeometry(
            QgsLineString(
                QgsPoint((mapx - box_size), (mapy - box_size)),
                QgsPoint((mapx + box_size), (mapy - box_size)),
            )
        )
        box_bot = QgsGeometry(
            QgsLineString(
                QgsPoint((mapx - box_size), (mapy + box_size)),
                QgsPoint((mapx + box_size), (mapy + box_size)),
            )
        )
        if pos.x() - box_size - crosshair_size > xmin:
            left_len = crosshair_size
        else:
            left_len = pos.x() - box_size - xmin
        if pos.x() + box_size + crosshair_size < xmax:
            right_len = crosshair_size
        else:
            right_len = xmax - box_size - pos.x()
        if pos.y() - box_size - crosshair_size > ymin:
            down_len = crosshair_size
        else:
            down_len = pos.y() - box_size - ymin
        if pos.y() + box_size + crosshair_size < ymax:
            up_len = crosshair_size
        else:
            up_len = ymax - box_size - pos.y()
        left_start = QgsPoint(
            (pos.x() - box_size), pos.y()
        )
        left_end = QgsPoint(
            (pos.x() - box_size - left_len), pos.y()
        )
        left_line = QgsGeometry(QgsLineString(left_end, left_start))
        right_start = QgsPoint(
            (pos.x() + box_size), pos.y()
        )
        right_end = QgsPoint(
            (pos.x() + box_size + right_len), pos.y()
        )
        right_line = QgsGeometry(QgsLineString(right_start, right_end))
        up_start = QgsPoint(
            pos.x(), (pos.y() + box_size)
        )
        up_end = QgsPoint(
            pos.x(), (pos.y() + box_size + up_len)
        )
        up_line = QgsGeometry(QgsLineString(up_start, up_end))
        down_start = QgsPoint(
            pos.x(), (pos.y() - box_size)
        )
        down_end = QgsPoint(
            pos.x(), (pos.y() - box_size - down_len)
        )
        down_line = QgsGeometry(QgsLineString(down_start, down_end))
        icon.addGeometry(box_left, doUpdate=False)
        icon.addGeometry(box_right, doUpdate=False)
        icon.addGeometry(box_top, doUpdate=False)
        icon.addGeometry(box_bot, doUpdate=False)
        icon.addGeometry(left_line, doUpdate=False)
        icon.addGeometry(right_line, doUpdate=False)
        icon.addGeometry(up_line, doUpdate=False)
        icon.addGeometry(down_line)
