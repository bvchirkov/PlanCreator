# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name			 	 : PlanCreator plugin
Description          : Allows input building's floor plans and export them into json
Date                 : 23/Apr/14 
copyright            : (C) 2014 by M G
email                : m.a.galiullin@gmail.com 
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from PlanCreatorDialog import PlanCreatorDialog
import os
import shutil
import uuid
#import myJsonEncoder
from CreateTopo import CreateTopo

class PlanCreator: 

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface

  def initGui(self):  
    # Create action that will start plugin configuration
    self.action = QAction(QIcon(":/plugins/PlanCreator/PlanCreatorNewLayer.png"), u'Добавить новый уровень', self.iface.mainWindow())
    self.action.setWhatsThis(u'Добавить новый уровень')
    self.action.setStatusTip(u'Добавить новый уровень')
    
    self.action1 = QAction(QIcon(":/plugins/PlanCreator/PlanCreatorJson.png"), u'Создать JSON', self.iface.mainWindow())
    self.action1.setWhatsThis(u'Создать JSON')
    self.action1.setStatusTip(u'Создать JSON')
    
    self.action0 = QAction(QIcon(":/plugins/PlanCreator/PlanCreatorNewProject.png"), u'Начать новый проект BuildingJSON', self.iface.mainWindow())
    self.action0.setWhatsThis(u'Начать новый проект BuildingJSON')
    self.action0.setStatusTip(u'Начать новый проект BuildingJSON')
    
    # connect the action to the run method
    QObject.connect(self.action0, SIGNAL("activated()"), self.run0) 
    QObject.connect(self.action, SIGNAL("activated()"), self.run) 
    QObject.connect(self.action1, SIGNAL("activated()"), self.run1) 
    #QObject.connect(self.iface.mapCanvas(), SIGNAL("renderComplete(QPainter *)"), self.renderTest) 
    
    # Add toolbar button and menu item
    self.iface.addToolBarIcon(self.action0)
    self.iface.addPluginToMenu("&Plan Creator", self.action0)
    
    self.iface.addToolBarIcon(self.action)
    self.iface.addPluginToMenu("&Plan Creator", self.action)
    
    self.iface.addToolBarIcon(self.action1)
    self.iface.addPluginToMenu("&Plan Creator", self.action1)
    

  def unload(self):
    # Remove the plugin menu item and icon
    self.iface.removePluginMenu("&Plan Creator",self.action0)
    self.iface.removeToolBarIcon(self.action0)
    self.iface.removePluginMenu("&Plan Creator",self.action)
    self.iface.removeToolBarIcon(self.action)
    self.iface.removePluginMenu("&Plan Creator",self.action1)
    self.iface.removeToolBarIcon(self.action1)

  # run method that performs creation new floor layers
  # здесь создается новый набор уровней для очередного этажа
  def run(self): 
    ###print "Pressed Create new floor"
    myProject = QgsProject.instance()
    #Проверим, что проект создан правильно (что это наш проект)
    if myProject.readEntry("PlanCreator", "projectkey", "noname")[0] != "PlanCreator v.0.1":
        self.printCrit(u'Сначала необходимо создать проект для PlanCreator!')
        return
    #Введем номер следующего этажа
    floorNextNumber = QInputDialog.getInt(None, u'Ввод номера уровня', u'Номер уровня (0-99)', 0, 0, 99, 1)
    if floorNextNumber[1] == False:
        return
    ###print floorNextNumber[0]
    newNumber = "%2.2d" % floorNextNumber[0]
    ###print newNumber
    
    #Проверка на наличие номера уровня
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
    if newNumber in layersHM:
        self.printCrit(u'Уровень с таким номером уже существует! Выберите другой номер.')
        return


    #Введем Имя уровня, высоту уроня и высоту потолков
    nameLevel = QInputDialog.getText(None, u'Ввод имени уровня', u'Название уровня:', QLineEdit.Normal, u'Этаж 1')
    if nameLevel[1] == False:
        return
    ###print nameLevel[0]
    zLevel = QInputDialog.getDouble(None, u'Ввод высоты уровня', u'Высота уровня над землей в метрах', 0, 0, 500, 2)
    if zLevel[1] == False:
        return
    ###print zLevel[0]
    sizeZ = QInputDialog.getDouble(None, u'Ввод высоты потолков', u'Высота потолков в метрах', 0, 3, 100, 2)
    if sizeZ[1] == False:
        return
    ###print sizeZ[0]
    sizeZD = QInputDialog.getDouble(None, u'Ввод высоты дверей', u'Высота дверей в метрах', 0, 2, 100, 2)
    if sizeZD[1] == False:
        return
    ###print sizeZD[0]
    
    #Скопируем шаблон уровня shp в папку проекта с переименовкой
    #print os.getcwd()
    newSUUID = str(uuid.uuid4()).split('-')[0]
    ###print newSUUID
    dstRooms = myProject.homePath() + "/rooms-" + newSUUID + ".shp"
    dstDoors = myProject.homePath() + "/doors-" + newSUUID + ".shp"
    dstStairs = myProject.homePath() + "/stairs-" + newSUUID + ".shp"
    dstDevices = myProject.homePath() + "/devices-" + newSUUID + ".shp"
    srcRooms = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/PlanCreator2" + "/layers/spaces"
    srcDoors = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/PlanCreator2" + "/layers/doors"
    srcStairs = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/PlanCreator2" + "/layers/stairs"
    srcDevices = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/PlanCreator2" + "/layers/devices"
    #chdir
    os.chdir(myProject.homePath())
    #copy & rename
    shutil.copy(srcRooms+".shp", "rooms-"+newSUUID+".shp")
    shutil.copy(srcRooms+".shx", "rooms-"+newSUUID+".shx")
    shutil.copy(srcRooms+".qpj", "rooms-"+newSUUID+".qpj")
    shutil.copy(srcRooms+".prj", "rooms-"+newSUUID+".prj")
    shutil.copy(srcRooms+".dbf", "rooms-"+newSUUID+".dbf")
    shutil.copy(srcRooms+".qml", "rooms-"+newSUUID+".qml")
    
    shutil.copy(srcDoors+".shp", "doors-"+newSUUID+".shp")
    shutil.copy(srcDoors+".shx", "doors-"+newSUUID+".shx")
    shutil.copy(srcDoors+".qpj", "doors-"+newSUUID+".qpj")
    shutil.copy(srcDoors+".prj", "doors-"+newSUUID+".prj")
    shutil.copy(srcDoors+".dbf", "doors-"+newSUUID+".dbf")
    shutil.copy(srcDoors+".qml", "doors-"+newSUUID+".qml")
    
    shutil.copy(srcStairs+".shp", "stairs-"+newSUUID+".shp")
    shutil.copy(srcStairs+".shx", "stairs-"+newSUUID+".shx")
    shutil.copy(srcStairs+".qpj", "stairs-"+newSUUID+".qpj")
    shutil.copy(srcStairs+".prj", "stairs-"+newSUUID+".prj")
    shutil.copy(srcStairs+".dbf", "stairs-"+newSUUID+".dbf")
    shutil.copy(srcStairs+".qml", "stairs-"+newSUUID+".qml")
    
    shutil.copy(srcDevices+".shp", "devices-"+newSUUID+".shp")
    shutil.copy(srcDevices+".shx", "devices-"+newSUUID+".shx")
    shutil.copy(srcDevices+".qpj", "devices-"+newSUUID+".qpj")
    shutil.copy(srcDevices+".prj", "devices-"+newSUUID+".prj")
    shutil.copy(srcDevices+".dbf", "devices-"+newSUUID+".dbf")
    shutil.copy(srcDevices+".qml", "devices-"+newSUUID+".qml")
    
    #myPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/PlanCreator"
    
    #Добавляем слои в проект
    # Rooms
    newRoomsLayer = QgsVectorLayer(dstRooms, "rooms"+newNumber, "ogr")
    #newRoomsLayer.loadDefaultStyle()
    
    if newRoomsLayer.isValid():
        QgsMapLayerRegistry.instance().addMapLayer(newRoomsLayer)
        ###print "Successfull loaded ROOMS and added"
    else:
        self.printCrit("Can't load layer")
        return
    #Save layer's parameters
    newRoomsLayer.setCustomProperty("nameLevel", nameLevel[0])
    newRoomsLayer.setCustomProperty("zLevel", zLevel[0])
    newRoomsLayer.setCustomProperty("sizeZ", sizeZ[0])
    #newRoomsLayer.loadNamedStyle("rooms-"+newSUUID+".qml")
    newRoomsLayer.loadDefaultStyle()
    
    # Stairs
    newStairsLayer = QgsVectorLayer(dstStairs, "stairs"+newNumber, "ogr")
    if newStairsLayer.isValid():
        QgsMapLayerRegistry.instance().addMapLayer(newStairsLayer)
        ###print "Successfull loaded STAIRS and added"
    else:
        self.printCrit("Can't load layer")
        return
    #Save layer's parameters
    newStairsLayer.setCustomProperty("nameLevel", nameLevel[0])
    newStairsLayer.setCustomProperty("zLevel", zLevel[0])
    newStairsLayer.setCustomProperty("sizeZ", sizeZ[0])
    newStairsLayer.loadDefaultStyle()
    
    # Doors
    newDoorsLayer = QgsVectorLayer(dstDoors, "doors"+newNumber, "ogr")
    if newDoorsLayer.isValid():
        QgsMapLayerRegistry.instance().addMapLayer(newDoorsLayer)
        ###print "Successfull loaded DOORS and added"
    else:
        self.printCrit("Can't load layer")
        return
    #Save layer's parameters
    newDoorsLayer.setCustomProperty("nameLevel", nameLevel[0])
    newDoorsLayer.setCustomProperty("zLevel", zLevel[0])
    newDoorsLayer.setCustomProperty("sizeZ", sizeZD[0]) #для дверей другая высота
    newDoorsLayer.loadDefaultStyle()
    
     # Devices
    newDevicesLayer = QgsVectorLayer(dstDevices, "devices"+newNumber, "ogr")
    if newDevicesLayer.isValid():
        QgsMapLayerRegistry.instance().addMapLayer(newDevicesLayer)
        ###print "Successfull loaded STAIRS and added"
    else:
        self.printCrit("Can't load layer")
        return
    #Save layer's parameters
    newDevicesLayer.setCustomProperty("nameLevel", nameLevel[0])
    newDevicesLayer.setCustomProperty("zLevel", zLevel[0])
    newDevicesLayer.loadDefaultStyle()
    
    #Make group
    li = self.iface.legendInterface()
    groupNumber = li.addGroup(nameLevel[0] + ", (" + str(zLevel[0]) + u'м.)')
    li.moveLayer(newRoomsLayer, groupNumber)
    li.moveLayer(newStairsLayer, groupNumber)
    li.moveLayer(newDoorsLayer, groupNumber)
    li.moveLayer(newDevicesLayer, groupNumber)
    
  #метод для выгрузки в json
  def run1(self): 
    
    topo = CreateTopo(self.iface)
    topo.makeTopo()
    #myUUID = str(uuid.uuid4())
    #print myUUID.split('-')[0]
    
    #li = self.iface.legendInterface()
    #numGroup = li.addGroup("new group")
    
    # New name for project
    # create and show the dialog 
    ###dlg = PlanCreatorDialog()
    # show the dialog
    ###dlg.show()
    ###result = dlg.exec_() 
    # See if OK was pressed
    ###if result == 1: 
      # do something useful (delete the line containing pass and
      # substitute with your code
        #pass 
        ###print "Pressed Button Make JSON"

#метод для Начала нового проекта
  def run0(self): 
    ###print "Pressed Button Begin New Project"
    # New filename for project
    projFileName = QFileDialog.getSaveFileName(None, u'Сохранить проект как...', "c:\\", "Project file (*.qgs *.QGS)")
    if projFileName == "":
        self.printWarn(u'Новый проект не создан')
        return
    ###print "Project fileName: " + projFileName
    #Create new project
    self.iface.newProject(True)
    myProject = QgsProject.instance()
    myProject.title("MyProject for BuildingJSON")   #Title for new project
    ###print "Set Title of project: " + myProject.title()
    # Input some parameters
    nameBuilding = QInputDialog.getText(None, u'Ввод названия здания', u'Название здания:', QLineEdit.Normal, u'Здание номер 1')
    ###print nameBuilding[0]
    streetAddress = QInputDialog.getText(None, u'Ввод адреса', u'Адрес здания (улица, дом):', QLineEdit.Normal, u'Университетская, 1')
    ###print streetAddress[0]
    city = QInputDialog.getText(None, u'Ввод города', u'Город:', QLineEdit.Normal, u'Ижевск')
    ###print city[0]
    
    # set CRS
    myProject.writeEntry("SpatialRefSys", "ProjectCrs", "EPSG:3395")
    myProject.writeEntry("SpatialRefSys", "ProjectCRSProj4String", "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs")
    myProject.writeEntry("SpatialRefSys", "ProjectCRSID", 1353)
    # store some custom key values
    myProject.writeEntry("PlanCreator", "projectkey", "PlanCreator v.0.1")
    myProject.writeEntry("PlanCreator", "nameBuilding", nameBuilding[0])
    myProject.writeEntry("PlanCreator", "streetAddress", streetAddress[0])
    myProject.writeEntry("PlanCreator", "city", city[0])
    
    #Save new project with custom key values
    myProject.setFileName(projFileName)
    # Save project to disk 
    if myProject.write():
        ###print "Project saved as: " + projFileName
        self.printInfo(u'Новый проект создан успешно')
    else:
        ###print "Project not saved for same reason"
        self.printCrit(u'Не удалось сохранить проект. Попробуйте выбрать другое место сохранения.')
    #dump properties
    #myProject.dumpProperties()
    #print myProject.readEntry("SpatialRefSys", "ProjectCrs")
    #print myProject.entryList("spatialrefsys", "proj4")
    #print myProject.subkeyList("mapcanvas", "destinationsrs")
    #print myProject.subkeyList("destinationsrs", "spatialrefsys")

  def renderTest(self, painter):
    # use painter for drawing to map canvas
    ###print "PlanCreator: renderTest called!"
    pass
    
  def printInfo(self, text):
    self.iface.messageBar().pushMessage("Info", text, level=QgsMessageBar.INFO, duration=10)

  def printWarn(self, text):
    self.iface.messageBar().pushMessage("Warning", text, level=QgsMessageBar.WARNING, duration=10)
    
  def printCrit(self, text):
    self.iface.messageBar().pushMessage("Critical", text, level=QgsMessageBar.CRITICAL, duration=10)
    
