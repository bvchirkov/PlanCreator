# -*- coding: utf-8 -*-
from qgis.core import *
from qgis.gui import *
#import PyQt4.QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import json
import uuid

class myJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QgsPoint):
            return [obj.x(), obj.y()]
        elif isinstance(obj, QPyNullVariant):
            return None
        return json.JSONEncoder.default(self, obj)


class CreateTopo():
    
    #Конструктор
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        pass
    
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
    def createXYTopo(self, polygon, elementField):
        elementField["XY"] = []                     # будущий массив колец
        for ring in polygon:                        # обходим кольца
            elementField["XY"].append({})           # обозначим объект, описывающий кольцо
            elementField["XY"][-1]["points"] = []   # массив координат (поле объекта колец)
            for points in ring:                                         # обходим массив точек
                elementField["XY"][-1]["points"].append({})
                elementField["XY"][-1]["points"][-1]["x"] = points[0]
                elementField["XY"][-1]["points"][-1]["y"] = points[1]
        pass
    
    #--------------------------------------------------------------------------
    # Создание топологии в уровнях
    # (Выполняется обход каждого уровня, а некоторых не поразу)
    #--------------------------------------------------------------------------
    def makeTopo(self):
        #get Map Registry
        reg = QgsMapLayerRegistry.instance()
        ###print "Number of Layers: " + str(reg.count())
        #get list (HashMap) of all layers on the map { internal-id : layer }
        mls = reg.mapLayers()
        layerNames = []     #list of layer names
        layersHM = {}        #HashMap of layers by floors
        #Создадим свою поэтажную струткутру HashMap для удобства
        #{ floor : { type : internal-id }}  floor=01, 02, etc;   type=rooms, doors, stairs
        for lid in mls.keys():
            if mls[lid].type() == QgsMapLayer.RasterLayer:
                continue
            layerNames.append(mls[lid].name())  #добавим имя в список
            floor = layerNames[-1][-2:]     #вычленим последние ДВА символа у имени слоя
            elemType = layerNames[-1][:-2]  #тип слоя - имя без последних двух цифр
            #Если этаж уже заведен, то добавим elemType, иначе создадим этаж
            if floor in layersHM:
                layersHM[floor][elemType] = mls[lid].id()   #можно было просто присвоить lid))
            else:
                layersHM[floor] = {elemType : mls[lid].id()}
        ###print layerNames
        ###print layersHM
        
        #--------------------------------------------------------------------------
        # Для каждого уровня найдем пересечения дверей с другими слоями (комнатами, 
        # лест. клетками) и датчиков со всеми слоями
        #--------------------------------------------------------------------------
        for floor in layersHM.keys():
            ###print "Process floor " + floor
            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            devicesLID = layersHM[floor]['devices']
            #Получим слои дверей, комнат и лест.клеток на данном этаже
            doors = reg.mapLayer(doorsLID)
            rooms = reg.mapLayer(roomsLID)
            stairs = reg.mapLayer(stairsLID)
            devices = reg.mapLayer(devicesLID)
            #Получим индексы(позиции) интересующих полей в таблицах аттрибутов слоев
            doorsRoomAIdx = doors.fieldNameIndex('roomA')
            doorsRoomBIdx = doors.fieldNameIndex('roomB')
            doorsIdIdx = doors.fieldNameIndex('id')
            roomsIdIdx = rooms.fieldNameIndex('id')
            stairsIdIdx = stairs.fieldNameIndex('id')
            devicesOwnerIdx = devices.fieldNameIndex('owner')
            
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
                attrs = { doorsRoomAIdx : NULL, doorsRoomBIdx : NULL }  #Было вместо NULL - ''
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
                        #print "Room Intersects!!!"
                        roomId = of.attributes()[roomsIdIdx]    #получим id пересекаемой комнаты
                        #print roomId
                        #print "roomA: ", f.attributes()[doorsRoomAIdx]
                        #print "roomB: ", f.attributes()[doorsRoomBIdx]
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { doorsRoomAIdx : roomId}
                                #print "roomA: ", roomId
                            elif intersectsCount == 2:
                                attrs = { doorsRoomBIdx : roomId}
                                #print "roomB: ", roomId
                            else:
                                ###print "!!! Triple Intersect !!!"
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
            
            #--------------------------------------------
            # For all devices on the same floor
            # features - список объектов слоя
            # Обход всех устройств на этаже и определение
            # родительского элемента.
            # Обход начинается с дверей, потому что слои
            # расположены в определенном порядке: двери,
            # лестницы, помещения.
            # Еслиу устройство было найдено на каком-либо
            # слое, то на других игнорируется.
            #--------------------------------------------
            features = devices.getFeatures()
            for f in features:
                geom = f.geometry()     #получим геометрию объекта (устройства)
                #Получим список возможностей данного типа векторного слоя (ESRI shape, например)
                caps = devices.dataProvider().capabilities()
                fid = f.id()    #feature id
                #Clear owner (Почистим информацию в поле owner)
                attrs = { devicesOwnerIdx : NULL }  #Было вместо NULL - ''
                #Надеемся на возможность прямой записи в таблицу аттрибутов слоя
                if caps & QgsVectorDataProvider.ChangeAttributeValues:
                    devices.dataProvider().changeAttributeValues({ fid : attrs })
                    devices.updateFields()    #Сразу же применяем изменения
                
                intersectsCount = 0     #счетчик пересечений. По идее их должно быть не более 1
                #Поищем пересечения данного Устройства со всеми Дверями
                otherFeatures = doors.getFeatures()
                for of in otherFeatures:
                    geomOther = of.geometry()   #получим геометрию объекта-двери
                    if geom.intersects(geomOther):
                        intersectsCount = intersectsCount + 1
                        doorId = of.attributes()[doorsIdIdx]    #получим id пересекаемой комнаты
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { devicesOwnerIdx : doorId}
                            else:
                                ###print "!!! Triple Intersect doors!!!", doorId
                                break
                            #Запишем в аттибуты дверей поля roomA или roomB
                            devices.dataProvider().changeAttributeValues({ fid : attrs })
                
                #Поищем пересечения данного Устройства со всеми Комнатами
                otherFeatures = rooms.getFeatures()
                for of in otherFeatures:
                    geomOther = of.geometry()   #получим геометрию объекта-комнаты
                    if geomOther.contains(geom):
                        intersectsCount = intersectsCount + 1
                        roomId = of.attributes()[roomsIdIdx]    #получим id пересекаемой комнаты
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { devicesOwnerIdx : roomId}
                            else:
                                ###print "!!! Triple Intersect rooms!!!"
                                break
                            #Запишем в аттибуты дверей поля roomA или roomB
                            devices.dataProvider().changeAttributeValues({ fid : attrs })
                
                #Поищем пересечения данного Устройства со всеми Комнатами
                otherFeatures = stairs.getFeatures()
                for of in otherFeatures:
                    geomOther = of.geometry()   #получим геометрию объекта-комнаты
                    if geomOther.contains(geom):
                        intersectsCount = intersectsCount + 1
                        stairId = of.attributes()[stairsIdIdx]    #получим id пересекаемой комнаты
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            if intersectsCount == 1:
                                attrs = { devicesOwnerIdx : stairId}
                            else:
                                ###print "!!! Triple Intersect stairs!!!"
                                break
                            #Запишем в аттибуты дверей поля roomA или roomB
                            devices.dataProvider().changeAttributeValues({ fid : attrs })
            #Применим изменения аттрибутов
            devices.updateFields()

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
            stairsIdIdx = stairs.fieldNameIndex('id')
            stairsS_idIdx = stairs.fieldNameIndex('s_id')
            stairsUpIdx = stairs.fieldNameIndex('up')
            stairsDownIdx = stairs.fieldNameIndex('down')
            if i > 0: #Если это не самый нижний этаж, то вычислим этаж пониже
                floorUnder = sortedFloors[i-1]
                stairsUnder = reg.mapLayer(layersHM[floorUnder]['stairs'])
                sUIdIdx = stairsUnder.fieldNameIndex('id')
                sUS_idIdx = stairsUnder.fieldNameIndex('s_id')
                sUUpIdx = stairsUnder.fieldNameIndex('up')
                sUDownIdx = stairsUnder.fieldNameIndex('down')
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
                    attrs = { stairsS_idIdx : stairId, stairsDownIdx : NULL, stairsUpIdx : NULL } #то присвоим s_id=id, up,down=NULL
                    if caps & QgsVectorDataProvider.ChangeAttributeValues:
                        stairs.dataProvider().changeAttributeValues({ fid : attrs })
                        #stairs.updateFields()
                        continue
                #иначе если это не самый первый этаж, то найдем пересечение с этажом ниже
                attrs = { stairsS_idIdx : stairId, stairsDownIdx : NULL, stairsUpIdx : NULL } #присвоим s_id=id, up,down=NULL на случай если не найдется пересечений
                attrsUnder = {}
                featuresUnder = stairsUnder.getFeatures()
                for fu in featuresUnder:
                    fuid = fu.id()
                    geomU = fu.geometry()
                    if geom.intersects(geomU):
                        stairUnderS_id = fu.attributes()[sUS_idIdx]
                        stairUnderId = fu.attributes()[sUIdIdx]
                        attrs = { stairsS_idIdx : stairUnderS_id, stairsDownIdx : stairUnderId, stairsUpIdx : NULL }  #s_id присвоим от s_id нижнего этажа, down=id(нижнего)
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
        deviceSignUUID = "12acd002-218e-4d15-b5b1-cf618fe007ff"
                
        proj = QgsProject.instance()
        nameOfBuilding = proj.readEntry("PlanCreator", "nameBuilding", u'Здание номер 1')[0]
        streetOfAddress = proj.readEntry("PlanCreator", "streetAddress", u'Университетская улица, дом 1')[0]
        city = proj.readEntry("PlanCreator", "city", u'Ижевск')[0]
        
        bld = { "NameBuilding":nameOfBuilding, "Address":{}, "Level":[], "Devs":[]}

        bld["Address"]["City"] = city
        bld["Address"]["StreetAddress"] = streetOfAddress
        bld["Address"]["AddInfo"] = "Additional information"
        
        # Список адресов, для отслеживания повторений
        # Это те адреса, которые присваиваются устройствам
        deviceAddrs = []

        for floor in sorted(layersHM):
            bld["Level"].append({})
            bld["Level"][-1]["NameLevel"] = "Floor number " + floor
            bld["Level"][-1]["ZLevel"] = floor  #строка
            bld["Level"][-1]["BuildElement"] = []

            doorsLID = layersHM[floor]['doors']
            roomsLID = layersHM[floor]['rooms']
            stairsLID = layersHM[floor]['stairs']
            devicesLID = layersHM[floor]['devices']
            
            doors = reg.mapLayer(doorsLID)
            rooms = reg.mapLayer(roomsLID)
            stairs = reg.mapLayer(stairsLID)
            devices = reg.mapLayer(devicesLID)
            
            bld["Level"][-1]["NameLevel"] = rooms.customProperty("nameLevel", bld["Level"][-1]["NameLevel"])
            bld["Level"][-1]["ZLevel"] = float(rooms.customProperty("zLevel", bld["Level"][-1]["ZLevel"]))
            
            doorsIdIdx = doors.fieldNameIndex('id')
            doorsRoomAIdx = doors.fieldNameIndex('roomA')
            doorsRoomBIdx = doors.fieldNameIndex('roomB')
            doorsDoorWayIdx = doors.fieldNameIndex('doorWay')
            doorsSizeZIdx = doors.fieldNameIndex('sizeZ')
            
            roomsIdIdx = rooms.fieldNameIndex('id')
            roomsNameIdx = rooms.fieldNameIndex('name')
            roomsPeopleIdx = rooms.fieldNameIndex('people')
            roomsTypeIdx = rooms.fieldNameIndex('type')
            roomsScenarioIdx = rooms.fieldNameIndex('scenario')
            roomsSizeZIdx = rooms.fieldNameIndex('sizeZ')
            
            stairsIdIdx = stairs.fieldNameIndex('id')
            stairsUpIdx = stairs.fieldNameIndex('up')
            stairsDownIdx = stairs.fieldNameIndex('down')
            stairsSizeZIdx = stairs.fieldNameIndex('sizeZ')
            
            #boris-code ---start
            devicesIdIdx = devices.fieldNameIndex('id')
            devicesAddrIdx = devices.fieldNameIndex('addr')
            devicesSignIdx = devices.fieldNameIndex('type')
            #boris-code end-----
           
            #Пробежим по всем ДВЕРЯМ этажа
            features = doors.getFeatures()
            doorSerialNumber = 0
            for f in features:
                id = f.attributes()[doorsIdIdx][1:-1]       #[1:-1] - обрезам фигурные скобки
                roomA = f.attributes()[doorsRoomAIdx][1:-1]
                roomB = f.attributes()[doorsRoomBIdx]
                if (roomB != NULL): roomB = roomB[1:-1]
                doorSizeZ = f.attributes()[doorsSizeZIdx]
                doorWay = f.attributes()[doorsDoorWayIdx]
                #doorType = "DoorWayOut" if roomB == NULL else "DoorWayInt"
                
                geom = f.geometry()
                #print "----------\nArea: ", geom.area()
                
                #Добавим BuildElement для данной двери
                doorSerialNumber = doorSerialNumber + 1
                bld["Level"][-1]["BuildElement"].append({})
                
				#boris-code ---start
                bld["Level"][-1]["BuildElement"][-1]["@"] = doorSignUUID
				#boris-code end-----

                #Определимся с типом двери
                if roomB == NULL:
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
                if doorSizeZ == NULL:
                    bld["Level"][-1]["BuildElement"][-1]["SizeZ"] = float(doors.customProperty("sizeZ", "2")) #Высота дверей
                else:
                    bld["Level"][-1]["BuildElement"][-1]["SizeZ"] = doorSizeZ

                #Определимся с соседними элментами двери
                if roomA != NULL:
                    bld["Level"][-1]["BuildElement"][-1]["Name"] = bld["Level"][-1]["BuildElement"][-1]["Name"] + " "+roomA[-5:]+"<->"
                    bld["Level"][-1]["BuildElement"][-1]["Output"] = [roomA]
                    if roomB != NULL:
                        bld["Level"][-1]["BuildElement"][-1]["Name"] = bld["Level"][-1]["BuildElement"][-1]["Name"] + roomB[-5:]
                        bld["Level"][-1]["BuildElement"][-1]["Output"].append(roomB)

                if geom.type() == QGis.Polygon:
                    self.createXYTopo(geom.asPolygon(), bld["Level"][-1]["BuildElement"][-1])
                         
                #Заведем BuildElement-ы для комнат roomA и roomB если еще не завелись от других дверей
                if roomA != NULL:
                    rABE = self.findBuildElement(bld["Level"][-1]["BuildElement"], roomA)
                    if not "Output" in rABE:
                        rABE["Output"] = []
                    rABE["Output"].append(id)
                if roomB != NULL:
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
                if roomSizeZ == NULL:
                    currBE["SizeZ"] = float(rooms.customProperty("sizeZ", "3"))
                else:
                    currBE["SizeZ"] = roomSizeZ
                currBE["Type"] = f.attributes()[roomsTypeIdx]
                currBE["NumPeople"] = f.attributes()[roomsPeopleIdx]
                currBE["SignScenario"] = f.attributes()[roomsScenarioIdx]
                if geom.type() == QGis.Polygon:
                    self.createXYTopo(geom.asPolygon(), currBE)

            #Пробежим по всем ЛЕСТНИЧНЫМ ПЛОЩАДКАМ этажа
            features = stairs.getFeatures()
            stairSerialNumber = 0
            for f in features:
                id = f.attributes()[stairsIdIdx][1:-1]
                up = f.attributes()[stairsUpIdx]
                down = f.attributes()[stairsDownIdx]
                stairSizeZ = f.attributes()[stairsSizeZIdx]
                #Исправляем UUID - убираем фигурные скобки в начале и в конце
                if up != NULL: up = up[1:-1]
                if down != NULL: down = down[1:-1]
                
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
                if stairSizeZ == NULL:
                    currBE["SizeZ"] = float(stairs.customProperty("sizeZ", "3"))
                else:
                    currBE["SizeZ"] = stairSizeZ
                currBE["Type"] = 7
                currBE["NumPeople"] = 0
                currBE["SignScenario"] = 0
                
                #Форимруем координаты полигона
                if geom.type() == QGis.Polygon:
                    self.createXYTopo(geom.asPolygon(), currBE)

                #Добавим соединения лестничных площадок с соседними этажами
                if up != NULL:
                    currBE["Up"] = up   #Дополнительное поле Up, которое потом можно удалить
                    if not "Output" in currBE:
                        currBE["Output"] = []
                    currBE["Output"].append(up)
                if down != NULL:
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
                if up != NULL:
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
                    if geom.type() == QGis.Polygon:
                        self.createXYTopo(geom.asPolygon(), doorBE)
                    
                #Здесь по-сложнее связь сделать с нижним фиктивным дверным пролетом
                if down != NULL:
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
        
            #Пробежим по всем УСТРОЙСТВАМ (devices) этажа
            features = devices.getFeatures()
            for f in features:
                id = f.attributes()[devicesIdIdx][1:-1]       #[1:-1] - обрезам фигурные скобки
                deviceSign = f.attributes()[devicesSignIdx]
                deviceAddr = f.attributes()[devicesAddrIdx]
                deviceOwner = f.attributes()[devicesOwnerIdx][1:-1]
                
                if deviceAddr not in deviceAddrs:
                    deviceAddrs.append(deviceAddr)
                else:
                    print 'Floor: {0}; DeviceAddr: {1}'.format(floor, deviceAddr)
                    self.iface.messageBar().pushMessage("Error", "There are devices with the same address", level=QgsMessageBar.CRITICAL)
                    break
                
                deviceType = "Type not defined"
                deviceName = "Name not defined"
                postfix = floor + " : "+ id[-5:]
                #Определимся с типом устройства
                if deviceSign == 1:
                    deviceType = "FireDetector"
                    deviceName = u'Извещатель пожарный (' + postfix + ")"
                elif deviceSign == 2:
                    deviceType = "FireDetectorManual"
                    deviceName = u'Извещатель пожарный ручной (' + postfix + ")"
                elif deviceSign == 3:
                    deviceType = "Speaker"
                    deviceName = u'Звуковой оповещатель (' + postfix + ")"
                elif deviceSign == 4:
                    deviceType = "DoorTrafficLight"
                    deviceName = u'Световой оповещатель двери (' + postfix + ")"
                elif deviceSign == 5:
                    deviceType = "DirectionIndicator"
                    deviceName = u'Световой указатель направления (' + postfix + ")"
                elif deviceSign == 6:
                    deviceType = "PeopleCountingDevice"
                    deviceName = u'Счетчик людей (' + postfix +")"
                else:
                    deviceType = "Type not defined"
                    deviceName = u'Неизветсное устройство (' + postfix +")"
                
                bld["Devs"].append({})
                jsonPrefix = bld["Devs"][-1]
                
                jsonPrefix["@"]       = deviceSignUUID
                jsonPrefix["Id"]      = id              #UUID
                jsonPrefix["Name"]    = deviceName
                jsonPrefix["Addr"]    = deviceAddr
                jsonPrefix["Sign"]    = deviceType
                jsonPrefix["Owner"]   = deviceOwner
                
                geom = f.geometry()
                if geom.type() == QGis.Point:
                    devicePosition = geom.asPoint()
                    jsonPrefix["Position"] = {}
                    jsonPrefix["Position"]["x"] = devicePosition[0]
                    jsonPrefix["Position"]["y"] = devicePosition[1]

        
        #jsonStr = json.dumps(bld, ensure_ascii=False, cls=myJSONEncoder, indent=3)
        ###print jsonStrDev
        #print repr(dev)
        nameOfJsonFile = QFileDialog.getSaveFileName(None, u'Сохранить BuildingJson как...', proj.homePath(), "JSON file (*.json *.JSON)")
        if nameOfJsonFile == "":
            return
        jsonFile = open(nameOfJsonFile, 'w')
        json.dump(bld, jsonFile, ensure_ascii=True, cls=myJSONEncoder, indent=3)
        jsonFile.close()
        self.iface.messageBar().pushMessage("Info", u'Файл JSON успешно создан.', level=QgsMessageBar.INFO, duration=10)
        mb = QMessageBox()
        mb.setText(u'Файл JSON успешно создан.')
        #mb.setInformativeText(u'Нажмите кнопку ПОКАЗАТЬ ПОДРОБНОСТИ')
        mb.setStandardButtons(QMessageBox.Ok)
        #mb.setDetailedText(jsonStr)
        mb.exec_()
        

