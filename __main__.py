import sys
from PyQt5.QtWidgets import QApplication
from Modules.MapApp import MapApp


app = QApplication(sys.argv)
map_app = MapApp()
map_app.show()
sys.exit(app.exec_())
