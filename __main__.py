import sys
import keyboard
from Modules.General import *
from PyQt5.QtWidgets import QApplication, QMainWindow
from UI.UI_MapAppMainWindow import Ui_MapAppMainWindow
from PyQt5.Qt import QPixmap, QImage
from io import BytesIO


class MapApp(Ui_MapAppMainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.spn = '0.0003'
        self.l = 'map'
        self.ll = '37.588392,55.734036'
        self.map_api_server = "http://static-maps.yandex.ru/1.x/"
        keyboard.hook(self.keyboard_events)
        self.override_map_params()

    def keyboard_events(self, e):
        if e.name == 'page up' and e.event_type == 'down':
            temp = float(self.spn)
            if temp >= 0.001:
                temp *= 0.1
            self.spn = str(temp)
            self.override_map_params()
        elif e.name == 'page down' and e.event_type == 'down':
            temp = float(self.spn)
            if temp % 100 < 10:
                temp *= 10
            self.spn = str(temp)
            self.override_map_params()

    def override_map_params(self):
        map_params = {
            "l": self.l,
            'll': self.ll,
            'spn': ",".join([self.spn, self.spn])
        }
        response = perform_request(self.map_api_server, params=map_params)
        image = QImage().fromData(response.content)
        pix_map = QPixmap().fromImage(image)
        self.map_label.setPixmap(pix_map)


app = QApplication(sys.argv)
map_app = MapApp()
map_app.show()
sys.exit(app.exec_())
