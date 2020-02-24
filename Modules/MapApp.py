from Modules.General import *
from PyQt5.QtWidgets import QMainWindow
from UI.UI_MapAppMainWindow import Ui_MapAppMainWindow
from PyQt5.Qt import QPixmap, QImage, Qt
# from Modules.EasyThreadsQt import queue_thread_qt


START_SCALE = 13
START_DISPLAY_AREA = [90, 45]
START_POS = [37.588392, 55.734036]


MAP_DEGREE_WIDTH = 360
MAP_DEGREE_HEIGHT = 180

MIN_DISPLAY_AREA = 0.000009
MAX_DISPLAY_AREA = 180

MAP_TYPES = ['map', 'sat']
GO_NAMES_TYPE = 'skl'  # GO - geographic objects
TRAFFIC_JAMS_TYPE = 'trf'

ERROR_STYLESHEET = '*{color:red;}'
INFO_LABEL_STYLESHEET = '*{color:black;}'

TOPONYM_NOT_FOUND_ERROR_MSG = 'Объект не найден'
BAD_RESPONSE_ERROR = 'Ошибка при запросе'


class MapApp(Ui_MapAppMainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.map_label.set_map_app(self)

        # Назначаем функции на элементы UI
        self.map_type_box.currentIndexChanged.connect(self.update_map_type)
        self.go_names_btn.clicked.connect(self.update_map_type)
        self.traffic_jams_btn.clicked.connect(self.update_map_type)
        self.find_obj_btn.clicked.connect(self.get_object)
        self.reset_result_btn.clicked.connect(self.reset_result)

        # Пусть карта позиционируется на Москве, дабы было понятно что
        # программа работает
        self.map_pos = START_POS  # Параметр ll
        self.map_type = 'map'     # Параметр l
        self.scale = START_SCALE  # Параметр z
        self.display_area = START_DISPLAY_AREA
        self.tags = []            # Параметр pt
        
        self.display_area_scale = START_SCALE
        self.view_box = []

        self.address = None
        self.toponym = None
        # self.post_address = None

        self.pix_maps = {}  # Словарь с уже загруженными ранее картинками

        self.override_map_params()

    def get_view_box(self, map_pos=None):
        """Функция для получения параметра bbox в картах через map_pos"""
        # Не используется
        if map_pos is None:
            map_pos = self.map_pos
        half_w = (MAP_DEGREE_WIDTH / 2 ** self.display_area_scale) / 2
        half_h = (MAP_DEGREE_HEIGHT / 2 ** self.display_area_scale) / 2
        x1 = map_pos[0] + half_w / 2
        y1 = map_pos[1] + half_h / 2
        x2 = map_pos[0] - half_w / 2
        y2 = map_pos[1] - half_h / 2
        if x1 < -MAP_DEGREE_WIDTH / 2:
            x1 = -MAP_DEGREE_WIDTH / 2
        elif x1 > MAP_DEGREE_WIDTH / 2:
            x1 = MAP_DEGREE_WIDTH / 2
        if y1 < -MAP_DEGREE_HEIGHT / 2:
            y1 = -MAP_DEGREE_HEIGHT / 2
        elif y1 > MAP_DEGREE_HEIGHT / 2:
            y1 = MAP_DEGREE_HEIGHT / 2
        if x2 < -MAP_DEGREE_WIDTH / 2:
            x2 = -MAP_DEGREE_WIDTH / 2
        elif x2 > MAP_DEGREE_WIDTH / 2:
            x2 = MAP_DEGREE_WIDTH / 2
        if y2 < -MAP_DEGREE_HEIGHT / 2:
            y2 = -MAP_DEGREE_HEIGHT / 2
        elif y2 > MAP_DEGREE_HEIGHT / 2:
            y2 = MAP_DEGREE_HEIGHT / 2
        return [[x1, y1], [x2, y2]]

    def get_object_by_click(self, relative_pos):
        """Метод принимает на вход относительную позицию точки на карте
        (относительные координаты показывают, какую часть от области показа
        составляет реальная координата)"""
        mouse_x, mouse_y = relative_pos
        if not (0 <= mouse_x <= 1 and 0 <= mouse_y <= 1):
            return
        x = self.map_pos[0] + (2 * mouse_x - 1) * self.display_area[0]
        y = self.map_pos[1] - (2 * mouse_y - 1) * self.display_area[1]
        if len(toponyms := get_toponyms(x, y)) != 0:
            found_toponym = toponyms[0]
            pos = get_pos_by_toponym(found_toponym)

            left = self.map_pos[0] + self.display_area[0]
            right = self.map_pos[0] - self.display_area[0]
            top = self.map_pos[1] + self.display_area[0]
            bottom = self.map_pos[1] - self.display_area[1]

            if right <= pos[0] <= left and bottom <= pos[1] <= top:
                self.toponym = found_toponym
                self.clear_tags()
                self.add_tag(pos)
                self.address = get_address_by_toponym(self.toponym)
                self.set_address_label()
                self.clear_info_label()
                # self.post_address = get_post_address_by_toponym(self.toponym)
                self.override_map_params()
                return 
        self.print_error(TOPONYM_NOT_FOUND_ERROR_MSG)

    def reset_result(self):
        self.map_pos = START_POS
        self.tags = []
        self.address = None
        self.address_label.setText('')
        self.toponym = None
        self.override_map_params()

    def get_pix_map(self, map_type=None, map_pos=None, scale=None, tags=None,
                    display_area=None):
        """Получение изображения карты."""

        # Если в метод не переданы какие-либо параметры, используем текущие
        # параметры карты
        if map_type is None:
            map_type = self.map_type
        if map_pos is None:
            map_pos = self.map_pos
        if scale is None:
            scale = self.scale
        if tags is None:
            tags = self.tags
        if display_area is None:
            display_area = self.display_area

        display_area = [MAP_DEGREE_WIDTH / 2 ** self.display_area_scale / 2,
                        MAP_DEGREE_HEIGHT / 2 ** self.display_area_scale / 2]
        self.display_area = display_area

        map_params = {
            "l": map_type,
            'll': ','.join(map(str, map_pos)),
            # 'z': str(scale),
            'spn': ','.join(map(str, display_area)),
            # 'bbox': format_map_view_box(self.view_box),
            'pt': '~'.join(map(str, tags))
        }
        key = tuple(map_params.values())
        pix_map = self.pix_maps.get(key)
        if pix_map is None:
            try:
                response = perform_request(MAP_API_SERVER, params=map_params)
                image = QImage().fromData(response.content)
                pix_map = QPixmap().fromImage(image)
                self.pix_maps[key] = pix_map
            except RequestError:
                pass
        return pix_map

    def override_map_params(self):
        self.view_box = self.get_view_box()
        """Изменение параметров карты."""
        pix_map = self.get_pix_map()
        if pix_map:
            self.map_label.setPixmap(pix_map)
            self.clear_info_label()
        else:
            self.print_error(BAD_RESPONSE_ERROR)

    def keyPressEvent(self, *args, **kwargs):
        key = args[0].key()
        if key == Qt.Key_PageUp:
            if self.display_area_scale < 17:
                self.display_area_scale += 1
                self.override_map_params()
            # new_display_area = [coord / 2 for coord in self.display_area]
            # if min(new_display_area) >= MIN_DISPLAY_AREA:
            #     self.display_area = new_display_area
            #     self.override_map_params()
        elif key == Qt.Key_PageDown:
            if self.display_area_scale > 0:
                self.display_area_scale -= 1
                self.override_map_params()
            # new_display_area = [coord * 2 for coord in self.display_area]
            # if max(new_display_area) <= MAX_DISPLAY_AREA:
            #     self.display_area = new_display_area
            #     self.override_map_params()

    def update_map_type(self):
        map_type = [MAP_TYPES[self.map_type_box.currentIndex()]]
        if self.go_names_btn.isChecked():
            map_type += [GO_NAMES_TYPE]
        if self.traffic_jams_btn.isChecked():
            map_type += [TRAFFIC_JAMS_TYPE]
        self.map_type = ','.join(map_type)
        self.override_map_params()

    def add_tag(self, pos):
        self.tags.append(f'{",".join(map(str, pos))},comma')

    def get_object(self):
        try:
            toponyms = get_toponyms(self.object_input.text())
            if len(toponyms) == 0:
                self.print_error(TOPONYM_NOT_FOUND_ERROR_MSG)
            else:
                self.toponym = toponyms[0]
                self.map_pos = get_pos_by_toponym(self.toponym)
                self.add_tag(self.map_pos)
                self.address = get_address_by_toponym(self.toponym)
                self.set_address_label()
                self.clear_info_label()
                self.override_map_params()
        except RequestError:
            self.print_error(BAD_RESPONSE_ERROR)

    def print_error(self, msg):
        self.info_label.setStyleSheet(ERROR_STYLESHEET)
        self.info_label.setText(msg)

    def clear_info_label(self):
        self.info_label.setStyleSheet(INFO_LABEL_STYLESHEET)
        self.info_label.setText('')

    def set_address_label(self):
        self.address_label.setText(self.address)
    
    def clear_tags(self):
        self.tags = []