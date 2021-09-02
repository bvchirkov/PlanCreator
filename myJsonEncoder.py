import json
import PyQt4.QtCore
import qgis.core

class myJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, qgis.core.QgsPoint):
            return [obj.x(), obj.y()]
        elif isinstance(obj, PyQt4.QtCore.QPyNullVariant):
            return None
        return json.JSONEncoder.default(self, obj)
