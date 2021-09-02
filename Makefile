# Makefile for PlanCreator plugin plugin 
UI_FILES = Ui_PlanCreator.py

RESOURCE_FILES = resources.py

default: compile
	
compile: $(UI_FILES) $(RESOURCE_FILES)

%.py : %.qrc
	pyrcc4 -o $@  $<

%.py : %.ui
	/c/Program\ Files/QGIS\ Valmiera/bin/python.exe /c/Program\ Files/QGIS\ Valmiera/apps\Python27/lib/site-packages/PyQt4/uic/pyuic.py -o $@ $<