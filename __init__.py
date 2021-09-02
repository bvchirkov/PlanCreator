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
 This script initializes the plugin, making it known to QGIS.
"""
def name(): 
  return "PlanCreator plugin" 
def description():
  return "Allows input building's floor plans and export them into json"
def version(): 
  return "Version 0.1" 
def qgisMinimumVersion():
  return "2.0"
def classFactory(iface): 
  # load PlanCreator class from file PlanCreator
  from PlanCreator import PlanCreator 
  return PlanCreator(iface)
