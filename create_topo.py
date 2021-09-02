# -*- coding: utf-8 -*-

import json
import uuid
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.core import (
    QgsProject,
    QgsMapLayer,
    QgsVectorDataProvider,
    QgsWkbTypes,
    QgsPointXY,
    Qgis
)

# class Door():
#     def __init__(self, lid, layers, ) -> None:
#         self.lid = lid
#         self.layers = layers
#         self.id = id
#         self.room_a = room_a
#         self.room_b = room_b



class CreateTopo():
    
    #Конструктор
    def __init__(self, proj_name, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.proj_name = proj_name
    
    #--------------------------------------------------------------------------
    # Поиск элемента в массие bes в заданным beId
    # Если элемент находится, то возвращается,
    # иначе создается новый элмент
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
    # Переделал под возможности библиотеки GpCore, потому что она не пока умеет
    # рабоатать с большой вложенностью массивов, а при прямом сохранении 
    # геометрии получается 3 уровня вложенности.
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
    def makeTopo(self) -> None:
        #get Map Registry
        reg = QgsProject.instance()
        print("Number of Layers: " + str(reg.count()))

        #get list (HashMap) of all layers on the map { internal-id : layer }
        mls = reg.mapLayers()

        layerNames = []     #list of layer names
        layersHM = {}       #HashMap of layers by floors

        #Создадим свою поэтажную струткутру HashMap для удобства
        #{ floor : { type : internal-id }}  floor=01, 02, etc;   type=rooms, doors, stairs
        for lid in mls.keys():
            if mls[lid].type() == QgsMapLayer.RasterLayer:
                continue
            layerNames.append(mls[lid].name())  #добавим имя в список
            floor = layerNames[-1][-2:]         #вычленим последние ДВА символа у имени слоя
            elemType = layerNames[-1][:-2]      #тип слоя - имя без последних двух цифр
            #Если этаж уже заведен, то добавим elemType, иначе создадим этаж
            if floor in layersHM:
                layersHM[floor][elemType] = mls[lid].id()   #можно было просто присвоить lid))
            else:
                layersHM[floor] = {elemType : mls[lid].id()}
        print(layerNames)
        print(layersHM)

        #--------------------------------------------------------------------------
        # Для каждого уровня найдем пересечения дверей с другими слоями (комнатами, 
        # лест. клетками) и датчиков со всеми слоями
        #--------------------------------------------------------------------------
        for floor in layersHM.keys():
            ###print "Process floor " + floor
            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            # devicesLID = layersHM[floor]['devices']
            #Получим слои дверей, комнат и лест.клеток на данном этаже
            doors = reg.mapLayer(doorsLID)
            rooms = reg.mapLayer(roomsLID)
            stairs = reg.mapLayer(stairsLID)
            # devices = reg.mapLayer(devicesLID)
            #Получим индексы(позиции) интересующих полей в таблицах аттрибутов слоев
            doorsRoomAIdx   = doors.fields().indexOf('roomA')
            doorsRoomBIdx   = doors.fields().indexOf('roomB')
            doorsIdIdx      = doors.fields().indexOf('id')
            roomsIdIdx      = rooms.fields().indexOf('id')
            stairsIdIdx     = stairs.fields().indexOf('id')
            # devicesOwnerIdx = devices.fields().indexOf('owner')

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
                attrs = { doorsRoomAIdx : None, doorsRoomBIdx : None }
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
                        print("Room Intersects!!!")
                        roomId = of.attributes()[roomsIdIdx]    #получим id пересекаемой комнаты
                        print(roomId)
                        print("roomA: ", f.attributes()[doorsRoomAIdx])
                        print("roomB: ", f.attributes()[doorsRoomBIdx])
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { doorsRoomAIdx : roomId}
                                print("roomA: ", roomId)
                            elif intersectsCount == 2:
                                attrs = { doorsRoomBIdx : roomId}
                                print("roomB: ", roomId)
                            else:
                                print("!!! Triple Intersect !!!")
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
                            elif intersectsCount ==2:
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
            stairs = reg.mapLayer(stairsLID)
            caps = stairs.dataProvider().capabilities()
            stairsIdIdx = stairs.fields().indexOf('id')
            stairsS_idIdx = stairs.fields().indexOf('s_id')
            stairsUpIdx = stairs.fields().indexOf('up')
            stairsDownIdx = stairs.fields().indexOf('down')
            if i > 0: #Если это не самый нижний этаж, то вычислим этаж пониже
                floorUnder = sortedFloors[i-1]
                stairsUnder = reg.mapLayer(layersHM[floorUnder]['stairs'])
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
        
        #Генеграция идентификаторов для чтения json в c++ GpCore
        doorSignUUID = "39baaad1-3bea-4220-ac34-70e3021e4cc8"
        roomSignUUID = "9a9d5f7b-bd3d-433e-80ee-25403e857896"
        stairSignUUID = "ffef2dae-a46c-42b7-aa4f-86507d7f8acc"
                
        proj = QgsProject.instance()
        nameOfBuilding = proj.readEntry(self.proj_name, "nameBuilding", u'Здание номер 1')[0]
        streetOfAddress = proj.readEntry(self.proj_name, "streetAddress", u'Университетская улица, дом 1')[0]
        city = proj.readEntry(self.proj_name, "city", u'Ижевск')[0]
        
        bld = { "NameBuilding":nameOfBuilding, "Address":{}, "Level":[], "Devs":[]}

        bld["Address"]["City"] = city
        bld["Address"]["StreetAddress"] = streetOfAddress
        bld["Address"]["AddInfo"] = "Additional information"
        
        for floor in sorted(layersHM):
            bld["Level"].append({})
            bld["Level"][-1]["NameLevel"] = "Floor number " + floor
            bld["Level"][-1]["ZLevel"] = floor  #строка
            bld["Level"][-1]["BuildElement"] = []

            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            
            doors = reg.mapLayer(doorsLID)
            rooms = reg.mapLayer(roomsLID)
            stairs = reg.mapLayer(stairsLID)
            
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
                id = f.attributes()[doorsIdIdx][1:-1]       #[1:-1] - обрезам фигурные скобки
                roomA = f.attributes()[doorsRoomAIdx][1:-1]
                roomB = f.attributes()[doorsRoomBIdx]
                if (roomB != None): roomB = roomB[1:-1]
                doorSizeZ = f.attributes()[doorsSizeZIdx]
                doorWay = f.attributes()[doorsDoorWayIdx]
                #doorType = "DoorWayOut" if roomB == None else "DoorWayInt"
                
                geom = f.geometry()
                #print "----------\nArea: ", geom.area()
                
                #Добавим BuildElement для данной двери
                doorSerialNumber = doorSerialNumber + 1
                bld["Level"][-1]["BuildElement"].append({})
                
				#boris-code ---start
                bld["Level"][-1]["BuildElement"][-1]["@"] = doorSignUUID
				#boris-code end-----

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

                print(geom.type(), QgsWkbTypes.PolygonGeometry)
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
                id = f.attributes()[roomsIdIdx][1:-1]
                roomSizeZ = f.attributes()[roomsSizeZIdx]
                geom = f.geometry()
                roomSerialNumber = roomSerialNumber + 1
                #Поищем уже имеющиеся BuildElements с заданным id или создастся новый
                currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)
                #Заполним поля для комнаты
				
				#boris-code ---start
                currBE["@"] = roomSignUUID;
				#boris-code end-----

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
                id = f.attributes()[stairsIdIdx][1:-1]
                up = f.attributes()[stairsUpIdx]
                down = f.attributes()[stairsDownIdx]
                stairSizeZ = f.attributes()[stairsSizeZIdx]
                #Исправляем UUID - убираем фигурные скобки в начале и в конце
                if up != None: up = up[1:-1]
                if down != None: down = down[1:-1]
                
                geom = f.geometry()
                stairSerialNumber = stairSerialNumber + 1
                #Поищем уже имеющиеся BuildElements с заданным id или создастся новый
                currBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], id)
                #Заполним поля для Лестничных площадок

				#boris-code ---start
                currBE["@"] = stairSignUUID
				#boris-code end-----

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
                id = f.attributes()[stairsIdIdx][1:-1]
                up = f.attributes()[stairsUpIdx]
                down = f.attributes()[stairsDownIdx]
                geom = f.geometry()
                if up != None:
                    up = up[1:-1]

                    doorId = str(uuid.uuid4()) #сгенерим новый uuid для нового фиктивного проема
                    doorBE = self.findBuildElement(bld["Level"][-1]["BuildElement"], doorId)    #Создадим новый buildElement
					
					#boris-code ---start
                    doorBE["@"] = doorSignUUID
					#boris-code end-----

                    #doorBE["Name"] = "virtual DoorWay between stairs"
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
                    down = down[1:-1]
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
        
        #jsonStr = json.dumps(bld, ensure_ascii=False, cls=myJSONEncoder, indent=3)
        ###print jsonStrDev
        #print repr(dev)
        nameOfJsonFile = QFileDialog.getSaveFileName(None, u'Сохранить BuildingJson как...', proj.homePath(), "JSON file (*.json *.JSON)")[0]
        if nameOfJsonFile == "":
            return
        jsonFile = open(nameOfJsonFile, 'w')
        json.dump(bld, jsonFile, ensure_ascii=True, cls=myJSONEncoder, indent=3)
        jsonFile.close()
        self.iface.messageBar().pushMessage("Info", u'Файл JSON успешно создан.', level=Qgis.Info, duration=10)
        # mb = QMessageBox()
        # mb.setText(u'Файл JSON успешно создан.')
        # #mb.setInformativeText(u'Нажмите кнопку ПОКАЗАТЬ ПОДРОБНОСТИ')
        # mb.setStandardButtons(QMessageBox.Ok)
        # #mb.setDetailedText(jsonStr)
        # mb.exec_()

class myJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        # print(type(obj).__name__)
        if isinstance(obj, QgsPointXY):
            return [obj.x(), obj.y()]
        elif isinstance(obj, QVariant):
            # print(obj.isNull())
            return None
        return json.JSONEncoder.default(self, obj)