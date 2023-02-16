# -*- coding: utf-8 -*-

import json
import uuid
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsMapLayerType,
    QgsVectorLayer,
    QgsVectorDataProvider,
    QgsWkbTypes,
    QgsPointXY,
    Qgis
)

TRANSITS    = 'doors'
ZONES       = 'rooms'
STAIRS      = 'stairs'

class Transit():
    # fields
    __id_str__          = 'id'
    __room_a_str__      = 'roomA'
    __room_b_str__      = 'roomB'
    __size_z_str__      = 'sizeZ'
    __door_way_str__    = 'doorWay'
    __width_str__       = 'width'

    def __init__(self, layer:QgsVectorLayer):
        self.layer = layer

        self.idIdx     = None
        self.roomAIdx  = None
        self.roomBIdx  = None
        self.sizeZ     = None
        self.doorWay   = None
        self.width     = None
        self.get_indexes()

    def get_indexes(self):
        f_idx = lambda field_name: self.layer.fields().indexOf(field_name)

        self.idIdx     = f_idx(self.__id_str__)
        self.roomAIdx  = f_idx(self.__room_a_str__)
        self.roomBIdx  = f_idx(self.__room_b_str__)
        self.sizeZ     = f_idx(self.__size_z_str__)
        self.doorWay   = f_idx(self.__door_way_str__)
        self.width     = f_idx(self.__width_str__)


class CreateCfast():

    #Конструктор
    def __init__(self, proj_name, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.proj_name = proj_name
    
    #--------------------------------------------------------------------------
    # Поиск элемента в массие bes в заданным beId
    # Если элемент находится, то возвращается, иначе создается новый элмент
    #--------------------------------------------------------------------------
    def findBuildElement(self, bes, beId):
        #Поищем уже имеющиеся BuildElements в массиве bes с заданным id
        for x in bes:
            if x["Id"] == beId:
                findedBE = x  #ссылка на найденный BuildElement
                break
        else:   #иначе создадим новый BuildElement
            bes.append({})
            bes[-1]["Id"] = beId
            findedBE = bes[-1]
        return findedBE
    
    #--------------------------------------------------------------------------
    # Формирование подструктуры, хранящей координаты элемента
    #--------------------------------------------------------------------------
    def createXYTopo(self, polygon, elementField) -> None:
        elementField["XY"] = []                     # будущий массив колец
        for ring in polygon:                        # обходим кольца
            elementField["XY"].append({})           # обозначим объект, описывающий кольцо
            elementField["XY"][-1]["points"] = []   # массив координат (поле объекта колец)
            for point in ring[0]:                   # обходим массив точек первого кольца (предполагаем, что оно одно)
                elementField["XY"][-1]["points"].append({})
                elementField["XY"][-1]["points"][-1]["x"] = point[0]
                elementField["XY"][-1]["points"][-1]["y"] = point[1]

    #--------------------------------------------------------------------------
    # Создание топологии в уровнях
    # (Выполняется обход каждого уровня, а некоторых не поразу)
    #--------------------------------------------------------------------------
    def make_topo(self) -> None:
        #get Map Registry
        proj = QgsProject.instance()
        # print("Number of Layers: " + str(reg.count()))

        #get list (HashMap) of all layers on the map { internal-id : layer }
        mls = proj.mapLayers()

        layerNames = []     #list of layer names
        layersHM = {}       #HashMap of layers by floors

        #Создадим свою поэтажную струткутру HashMap для удобства
        #{ floor : { type : internal-id }}  floor=01, 02, etc;   type=rooms, doors, stairs
        for lid in mls.keys():
            if mls[lid].type() == QgsMapLayerType.RasterLayer:
                continue
            layerNames.append(mls[lid].name())  #добавим имя в список
            floor = layerNames[-1][-2:]         #вычленим последние ДВА символа у имени слоя
            elemType = layerNames[-1][:-2]      #тип слоя - имя без последних двух цифр
            #Если этаж уже заведен, то добавим elemType, иначе создадим этаж
            if floor in layersHM:
                layersHM[floor][elemType] = mls[lid].id()   #можно было просто присвоить lid))
            else:
                layersHM[floor] = {elemType : mls[lid].id()}
        # print(layerNames)
        # print(layersHM)

        #--------------------------------------------------------------------------
        # Для каждого уровня найдем пересечения дверей с другими слоями (комнатами, 
        # лест. клетками) и датчиков со всеми слоями
        #--------------------------------------------------------------------------
        for floor in layersHM.keys():
            ###print "Process floor " + floor
            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            #Получим слои дверей, комнат и лест.клеток на данном этаже
            doors = proj.mapLayer(doorsLID)
            rooms = proj.mapLayer(roomsLID)
            stairs = proj.mapLayer(stairsLID)
            #Получим индексы(позиции) интересующих полей в таблицах аттрибутов слоев
            doorsRoomAIdx   = self.get_field_index(doors, 'roomA')
            doorsRoomBIdx   = self.get_field_index(doors, 'roomB')
            doorsIdIdx      = self.get_field_index(doors, 'id')
            roomsIdIdx      = self.get_field_index(rooms, 'id')
            stairsIdIdx     = self.get_field_index(stairs, 'id')

            tr = Transit(doors)

            #For all doors on the same floor
            #features - список объектов слоя
            features = doors.getFeatures()
            for f in features:
                geom = f.geometry()     #получим геометрию объекта (двери)
                #print "----------\nArea: ", geom.area()
                #Получим список возможностей данного типа векторного слоя (ESRI shape, например)
                caps = doors.dataProvider().capabilities()
                fid = f.id()    #feature id
                #Clear roomA & roomB (Почистим информацию в полях roomA & roomB)
                attrs = { tr.roomAIdx : None, tr.roomBIdx : None }
                #Надеемся на возможность прямой записи в таблицу аттрибутов слоя
                if caps & QgsVectorDataProvider.ChangeAttributeValues:
                    doors.dataProvider().changeAttributeValues({ fid : attrs })
                    doors.updateFields()    #Сразу же применяем изменения
                
                intersectsCount = 0     #счетчик пересечений. По идее их должно быть не более 2
                #Поищем пересечения данной Двери со всеми Комнатами
                otherFeatures = rooms.getFeatures()
                for of in otherFeatures:
                    geomOther = of.geometry()   #получим геометрию объекта-комнаты
                    if geom.intersects(geomOther):
                        intersectsCount = intersectsCount + 1
                        # print("Room Intersects!!!")
                        roomId = of.attributes()[roomsIdIdx]    #получим id пересекаемой комнаты
                        # print(roomId)
                        # print("roomA: ", f.attributes()[doorsRoomAIdx])
                        # print("roomB: ", f.attributes()[doorsRoomBIdx])
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { doorsRoomAIdx : roomId}
                                # print("roomA: ", roomId)
                            elif intersectsCount == 2:
                                attrs = { doorsRoomBIdx : roomId}
                                # print("roomB: ", roomId)
                            else:
                                # print("!!! Triple Intersect !!!")
                                break
                            #Запишем в аттибуты дверей поля roomA или roomB
                            doors.dataProvider().changeAttributeValues({ fid : attrs })
                #Now for stairs (Теперь ищем пересечение данной ДВЕРИ с ЛЕСТН. Клетками на данном этаже)
                otherFeatures = stairs.getFeatures()
                for of in otherFeatures:
                    geomOther = of.geometry()
                    if geom.intersects(geomOther):
                        intersectsCount = intersectsCount + 1
                        #print "Stairs Intersects!!!"
                        stairId = of.attributes()[stairsIdIdx]
                        #print stairId
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { doorsRoomAIdx : stairId}
                                #print "roomA: ", stairId
                            elif intersectsCount == 2:
                                attrs = { doorsRoomBIdx : stairId}
                                #print "roomB: ", stairId
                            else:
                                ###print "!!! Triple Intersect !!!"
                                break
                            doors.dataProvider().changeAttributeValues({ fid : attrs })
            #Применим изменения аттрибутов
            doors.updateFields()

        #---------------------------------------
        #Finding linked stairs
        #Поиск связанных лестничных клеток, расположенных друг над другом
        #---------------------------------------
        #for sorted floor number
        #Здесь важно, что высотность растет в алфавитном порядке
        ###print "Process stairs links"
        sortedFloors = sorted(layersHM)
        for i in range(len(sortedFloors)):  #i=[0,...,ЧислоЭтажей-1]
            floor = sortedFloors[i]
            stairsLID = layersHM[floor]['stairs']
            stairs = proj.mapLayer(stairsLID)
            caps = stairs.dataProvider().capabilities()
            stairsIdIdx = stairs.fields().indexOf('id')
            stairsS_idIdx = stairs.fields().indexOf('s_id')
            stairsUpIdx = stairs.fields().indexOf('up')
            stairsDownIdx = stairs.fields().indexOf('down')
            if i > 0: #Если это не самый нижний этаж, то вычислим этаж пониже
                floorUnder = sortedFloors[i-1]
                stairsUnder = proj.mapLayer(layersHM[floorUnder]['stairs'])
                sUIdIdx = stairsUnder.fields().indexOf('id')
                sUS_idIdx = stairsUnder.fields().indexOf('s_id')
                sUUpIdx = stairsUnder.fields().indexOf('up')
                sUDownIdx = stairsUnder.fields().indexOf('down')
                capsUnder = stairsUnder.dataProvider().capabilities()
            #For all stairs on the same floor
            features = stairs.getFeatures()
            for f in features:
                geom = f.geometry()
                fid = f.id()
                stairId = f.attributes()[stairsIdIdx]
                stairS_id = f.attributes()[stairsS_idIdx]
                #find intersects with stairs on the lower floor
                if i == 0:    #if i==0 если это самый низший этаж
                    attrs = { stairsS_idIdx : stairId, stairsDownIdx : None, stairsUpIdx : None } #то присвоим s_id=id, up,down=None
                    if caps & QgsVectorDataProvider.ChangeAttributeValues:
                        stairs.dataProvider().changeAttributeValues({ fid : attrs })
                        #stairs.updateFields()
                        continue
                #иначе если это не самый первый этаж, то найдем пересечение с этажом ниже
                attrs = { stairsS_idIdx : stairId, stairsDownIdx : None, stairsUpIdx : None } #присвоим s_id=id, up,down=None на случай если не найдется пересечений
                attrsUnder = {}
                featuresUnder = stairsUnder.getFeatures()
                for fu in featuresUnder:
                    fuid = fu.id()
                    geomU = fu.geometry()
                    if geom.intersects(geomU):
                        stairUnderS_id = fu.attributes()[sUS_idIdx]
                        stairUnderId = fu.attributes()[sUIdIdx]
                        attrs = { stairsS_idIdx : stairUnderS_id, stairsDownIdx : stairUnderId, stairsUpIdx : None }  #s_id присвоим от s_id нижнего этажа, down=id(нижнего)
                        attrsUnder = { sUUpIdx : stairId }
                        if capsUnder & QgsVectorDataProvider.ChangeAttributeValues:
                            stairsUnder.dataProvider().changeAttributeValues({ fuid : attrsUnder })
                if caps & QgsVectorDataProvider.ChangeAttributeValues:
                    stairs.dataProvider().changeAttributeValues({ fid : attrs })
                
            stairs.updateFields()
            if i > 0:
                stairsUnder.updateFields()


        #--------------------------------------
        # Creating Buillding structure for future export to VMjson
        #--------------------------------------
        nameOfBuilding = proj.readEntry(self.proj_name, "nameBuilding", u'Здание номер 1')[0]
        streetOfAddress = proj.readEntry(self.proj_name, "streetAddress", u'Университетская улица, дом 1')[0]
        city = proj.readEntry(self.proj_name, "city", u'Ижевск')[0]
        additionalInfo = proj.readEntry(self.proj_name, "additionalInfo", u'Дополнительная информация')[0]
        
        bld = { "NameBuilding":nameOfBuilding, "Address":{}, "Level":[], "Devs":[]}

        bld_address = bld["Address"]
        bld_address["City"] = city
        bld_address["StreetAddress"] = streetOfAddress
        bld_address["AddInfo"] = additionalInfo
        
        for floor in sorted(layersHM):
            bld["Level"].append({})
            bld["Level"][-1]["NameLevel"] = "Floor number " + floor
            bld["Level"][-1]["ZLevel"] = floor  #строка
            bld["Level"][-1]["BuildElement"] = []

            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            
            doors = proj.mapLayer(doorsLID)
            rooms = proj.mapLayer(roomsLID)
            stairs = proj.mapLayer(stairsLID)
            
            bld["Level"][-1]["NameLevel"] = rooms.customProperty("nameLevel", bld["Level"][-1]["NameLevel"])
            bld["Level"][-1]["ZLevel"] = float(rooms.customProperty("zLevel", bld["Level"][-1]["ZLevel"]))
            
            doorsIdIdx = doors.fields().indexOf('id')
            doorsRoomAIdx = doors.fields().indexOf('roomA')
            doorsRoomBIdx = doors.fields().indexOf('roomB')
            doorsDoorWayIdx = doors.fields().indexOf('doorWay')
            doorsSizeZIdx = doors.fields().indexOf('sizeZ')
            
            roomsIdIdx = rooms.fields().indexOf('id')
            roomsNameIdx = rooms.fields().indexOf('name')
            roomsPeopleIdx = rooms.fields().indexOf('people')
            roomsTypeIdx = rooms.fields().indexOf('type')
            roomsScenarioIdx = rooms.fields().indexOf('scenario')
            roomsSizeZIdx = rooms.fields().indexOf('sizeZ')
            
            stairsIdIdx = stairs.fields().indexOf('id')
            stairsUpIdx = stairs.fields().indexOf('up')
            stairsDownIdx = stairs.fields().indexOf('down')
            stairsSizeZIdx = stairs.fields().indexOf('sizeZ')
            
            #Пробежим по всем ДВЕРЯМ этажа
            features = doors.getFeatures()
            doorSerialNumber = 0
            for f in features:
                id = self.cut_brackets(f.attributes()[doorsIdIdx])
                roomA = self.cut_brackets(f.attributes()[doorsRoomAIdx])
                roomB = f.attributes()[doorsRoomBIdx]
                if (roomB != None): roomB = self.cut_brackets(roomB)
                doorSizeZ = f.attributes()[doorsSizeZIdx]
                doorWay = f.attributes()[doorsDoorWayIdx]
                #doorType = "DoorWayOut" if roomB == None else "DoorWayInt"
                
                geom = f.geometry()
                #print "----------\nArea: ", geom.area()
                
                #Добавим BuildElement для данной двери
                doorSerialNumber = doorSerialNumber + 1
                bld["Level"][-1]["BuildElement"].append({})

                #Определимся с типом двери
                if roomB == None:
                    doorType = "DoorWayOut"
                    bld["Level"][-1]["BuildElement"][-1]["Name"] = u'Выход (' + floor + " : "+ id[-5:]+")"
                elif doorWay == 1:
                    doorType = "DoorWay"
                    bld["Level"][-1]["BuildElement"][-1]["Name"] = u'Проем (' + floor + " : "+ id[-5:]+")"
                else:
                    doorType = "DoorWayInt"
                    bld["Level"][-1]["BuildElement"][-1]["Name"] = u'Дверь (' + floor + " : "+ id[-5:]+")"
                #bld["Level"][-1]["BuildElement"][-1]["Name"] = u'Дверь (' + floor + " : "+ id[-5:-1]+")"
                bld["Level"][-1]["BuildElement"][-1]["Id"] = id     #UUID
                bld["Level"][-1]["BuildElement"][-1]["Sign"] = doorType
                
                # Определимся с высотой дверей
                if doorSizeZ == None:
                    bld["Level"][-1]["BuildElement"][-1]["SizeZ"] = float(doors.customProperty("sizeZ", "2")) #Высота дверей
                else:
                    bld["Level"][-1]["BuildElement"][-1]["SizeZ"] = doorSizeZ

                #Определимся с соседними элментами двери
                if roomA != None:
                    bld["Level"][-1]["BuildElement"][-1]["Name"] = bld["Level"][-1]["BuildElement"][-1]["Name"] + " "+roomA[-5:]+"<->"
                    bld["Level"][-1]["BuildElement"][-1]["Output"] = [roomA]
                    if roomB != None:
                        bld["Level"][-1]["BuildElement"][-1]["Name"] = bld["Level"][-1]["BuildElement"][-1]["Name"] + roomB[-5:]
                        bld["Level"][-1]["BuildElement"][-1]["Output"].append(roomB)

                if geom.type() == QgsWkbTypes.PolygonGeometry:
                    self.createXYTopo(geom.asMultiPolygon(), bld["Level"][-1]["BuildElement"][-1])
                         
                #Заведем BuildElement-ы для комнат roomA и roomB если еще не завелись от других дверей
                if roomA != None:
                    rABE = self.findBuildElement(bld["Level"][-1]["BuildElement"], roomA)
                    if not "Output" in rABE:
                        rABE["Output"] = []
                    rABE["Output"].append(id)
                if roomB != None:
                    rBBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], roomB)
                    if not "Output" in rBBE:
                        rBBE["Output"] = []
                    rBBE["Output"].append(id)

            #Пробежим по всем КОМНАТАМ (rooms) этажа
            features = rooms.getFeatures()
            roomSerialNumber = 0
            for f in features:
                id = self.cut_brackets(f.attributes()[roomsIdIdx])
                roomSizeZ = f.attributes()[roomsSizeZIdx]
                geom = f.geometry()
                roomSerialNumber = roomSerialNumber + 1
                #Поищем уже имеющиеся BuildElements с заданным id или создастся новый
                currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)

                #Заполним поля для комнаты
                currBE["Name"] = f.attributes()[roomsNameIdx] + " (" + floor + " : "+ id[-5:]+")"
                currBE["Sign"] = "Room"
                if roomSizeZ == None:
                    currBE["SizeZ"] = float(rooms.customProperty("sizeZ", "3"))
                else:
                    currBE["SizeZ"] = roomSizeZ
                currBE["Type"] = f.attributes()[roomsTypeIdx]
                currBE["NumPeople"] = f.attributes()[roomsPeopleIdx]
                currBE["SignScenario"] = f.attributes()[roomsScenarioIdx]
                if geom.type() == QgsWkbTypes.PolygonGeometry:
                    self.createXYTopo(geom.asMultiPolygon(), currBE)

            #Пробежим по всем ЛЕСТНИЧНЫМ ПЛОЩАДКАМ этажа
            features = stairs.getFeatures()
            stairSerialNumber = 0
            for f in features:
                id = self.cut_brackets(f.attributes()[stairsIdIdx])
                up = f.attributes()[stairsUpIdx]
                down = f.attributes()[stairsDownIdx]
                stairSizeZ = f.attributes()[stairsSizeZIdx]
                #Исправляем UUID - убираем фигурные скобки в начале и в конце
                if up != None: up = self.cut_brackets(up)
                if down != None: down = self.cut_brackets(down)
                
                geom = f.geometry()
                stairSerialNumber = stairSerialNumber + 1
                #Поищем уже имеющиеся BuildElements с заданным id или создастся новый
                currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)

                #Заполним поля для Лестничных площадок
                currBE["Name"] = u'Лестничная площадка (' + floor + " : "+ id[-5:]+")"
                currBE["Sign"] = "Staircase"
                if stairSizeZ == None:
                    currBE["SizeZ"] = float(stairs.customProperty("sizeZ", "3"))
                else:
                    currBE["SizeZ"] = stairSizeZ
                currBE["Type"] = 7
                currBE["NumPeople"] = 0
                currBE["SignScenario"] = 0
                
                #Форимруем координаты полигона
                if geom.type() == QgsWkbTypes.PolygonGeometry:
                    self.createXYTopo(geom.asMultiPolygon(), currBE)

                #Добавим соединения лестничных площадок с соседними этажами
                if up != None:
                    currBE["Up"] = up   #Дополнительное поле Up, которое потом можно удалить
                    if not "Output" in currBE:
                        currBE["Output"] = []
                    currBE["Output"].append(up)
                if down != None:
                    currBE["Down"] = down   #Дополнительное поле "Down", которое потом можно удалить
                    if not "Output" in currBE:
                        currBE["Output"] = []
                    currBE["Output"].append(down)
                
            #Пробежимся по лестничным площадкам еще раз, чтобы вставить фиктивные межэтажные дверные проемы
            features = stairs.getFeatures()
            for f in features:
                id = self.cut_brackets(f.attributes()[stairsIdIdx])
                up = f.attributes()[stairsUpIdx]
                down = f.attributes()[stairsDownIdx]
                geom = f.geometry()
                if up != None:
                    up = self.cut_brackets(up)

                    doorId = str(uuid.uuid4()) #сгенерим новый uuid для нового фиктивного проема
                    doorBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], doorId)    #Создадим новый buildElement
					
                    doorBE["Sign"] = "DoorWay"  #тип помещения - Дверной проем
                    #сделаем ссылки от нового дверного проема
                    doorBE["Output"] = [id]         #ссылка вниз
                    doorBE["Output"].append(up)     #ссылка вверх
                    #Доп. поля, которые потом удалим
                    doorBE["Up"] = up
                    doorBE["Down"] = id
                    doorBE["Name"] = u'Межэтажный проем (' + floor + " : "+ doorId[-5:]+") "+ doorBE["Down"][-5:]+"<->"+doorBE["Up"][-5:]
                    currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)
                    #сделаем ссылки на новый дверной проем
                    currBE["Up"] = doorId
                    for oi in range(len(currBE["Output"])):
                        if currBE["Output"][oi] == up:
                            currBE["Output"][oi] = doorId
                    #сделаем геометрию
                    if geom.type() == QgsWkbTypes.PolygonGeometry:
                        self.createXYTopo(geom.asMultiPolygon(), doorBE)
                    
                #Здесь по-сложнее связь сделать с нижним фиктивным дверным пролетом
                if down != None:
                    down = self.cut_brackets(down)
                    currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)
                    #--------------------------------------------ToDo-----------
                    #предыдущий этаж скорее всего bld["Level"][-2]["BuildElement"]
                    downStairBE = self.findBuildElement(bld["Level"][-2]["BuildElement"], currBE["Down"])
                    #downDoorBE = self.findBuildElement(bld["Level"][-2]["BuildElement"], downStairBE["Up"])
                    #меняем output ссылку вниз на виртуальную дверь снизу
                    currBE["Down"] = downStairBE["Up"]
                    for oi in range(len(currBE["Output"])):
                        if currBE["Output"][oi] == down:
                            currBE["Output"][oi] = downStairBE["Up"]        
        
        # ---------
        nameOfJsonFile = list(QFileDialog.getSaveFileName(None, u'Сохранить BuildingJson как...', proj.homePath(), "JSON file (*.json *.JSON)"))[0]
        if nameOfJsonFile == "":
            return

        if not nameOfJsonFile.endswith('.json'):
            nameOfJsonFile = '{}{}'.format(nameOfJsonFile, '.json')
            
        jsonFile = open(nameOfJsonFile, 'w')
        json.dump(bld, jsonFile, ensure_ascii=True, cls=myJSONEncoder, indent=3)
        jsonFile.close()
        self.iface.messageBar().pushMessage("Info", u'Файл JSON успешно создан.', level=Qgis.Info, duration=10)
    
    def get_field_index(self, layer:QgsVectorLayer, field_name:str) -> int:
        return layer.fields().indexOf(field_name)

    def cut_brackets(self, id:str) -> str:
        return id[1:-1] if id.startswith('{') and id.endswith('}') else id
    
    def fill_ids(self):
        '''
        Формирование уникальных идентификаторов для всех объектов всех слоев перед выгрузкой
        '''
        #get Map Registry
        proj = QgsProject.instance()
        mls = proj.mapLayers()

        for lid in mls.keys():
            layer:QgsMapLayer = mls[lid]
            if layer.type() == QgsMapLayerType.RasterLayer:
                continue
            if layer.isModified():
                # Сохранение всех изменений перед выгрузкой, чтобы обновились индексы объектов слоя
                layer.commitChanges(stopEditing=False)

            feature_idx_id:int = self.get_field_index(layer, 'id')
            for feature in layer.getFeatures():
                layer.dataProvider().changeAttributeValues({ feature.id() : {feature_idx_id: '{}'.format(str(uuid.uuid4()))} })
            layer.updateFields()


class myJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QgsPointXY):
            return [obj.x(), obj.y()]
        elif isinstance(obj, QVariant):
            return None
        return json.JSONEncoder.default(self, obj)