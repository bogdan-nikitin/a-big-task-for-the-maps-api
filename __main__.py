import sys
from Modules.General import *
from PyQt5.QtWidgets import QApplication, QMainWindow
from UI.UI_MapAppMainWindow import Ui_MapAppMainWindow
from PyQt5.Qt import QPixmap, QImage, Qt
# from Modules.EasyThreadsQt import queue_thread_qt


START_SCALE = 13
MAP_TYPES = ['map', 'sat']
GO_NAMES_TYPE = 'skl'  # GO - geographic objects
TRAFFIC_JAMS_TYPE = 'trf'


class MapApp(Ui_MapAppMainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.map_type_box.currentIndexChanged.connect(self.update_map_type)
        self.go_names_btn.clicked.connect(self.update_map_type)
        self.traffic_jams_btn.clicked.connect(self.update_map_type)
        self.find_obj_btn.clicked.connect(self.get_object)

        self.map_api_server = MAP_API_SERVER
        self.map_type = 'map'                  # Параметр l
        self.scale = START_SCALE               # Параметр z
        self.map_pos = [1, 1]  # Параметр ll
        self.pix_maps = {}  # Словарь с уже загруженными ранее картинками

        self.override_map_params()

    def get_pix_map(self, map_type=None, map_pos=None, scale=None):
        """Получение изображения карты."""

        # Если в метод не переданы какие-либо параметры, используем текущие
        # параметры карты
        if map_type is None:
            map_type = self.map_type
        if map_pos is None:
            map_pos = self.map_pos
        if scale is None:
            scale = self.scale

        map_params = {
            "l": map_type,
            'll': ','.join(map(str, map_pos)),
            'z': str(scale)
        }
        key = tuple(map_params.values())
        pix_map = self.pix_maps.get(key)
        if pix_map is None:
            response = perform_request(self.map_api_server, params=map_params)
            image = QImage().fromData(response.content)
            pix_map = QPixmap().fromImage(image)
            self.pix_maps[key] = pix_map
        return pix_map

    def override_map_params(self):
        """Изменение параметров карты."""
        self.map_label.setPixmap(self.get_pix_map())

    def keyPressEvent(self, *args, **kwargs):
        key = args[0].key()
        if key == Qt.Key_PageUp:
            if self.scale < 17:
                self.scale += 1
            self.override_map_params()
        elif key == Qt.Key_PageDown:
            if self.scale > 0:
                self.scale -= 1
            self.override_map_params()

    def update_map_type(self):
        map_type = [MAP_TYPES[self.map_type_box.currentIndex()]]
        if self.go_names_btn.isChecked():
            map_type += [GO_NAMES_TYPE]
        if self.traffic_jams_btn.isChecked():
            map_type += [TRAFFIC_JAMS_TYPE]
        self.map_type = ','.join(map_type)
        self.override_map_params()

    def get_object(self):
        self.map_pos = get_pos(self.object_input.text())
        self.override_map_params()


app = QApplication(sys.argv)
map_app = MapApp()
map_app.show()
sys.exit(app.exec_())
