# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlanCreator-3
                                 A QGIS plugin
 Инструмент создания пространственно-информационной модели здания
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2021-08-27
        copyright            : (C) 2021 by bvchirkov
        email                : b.v.chirkov@udsu.ru
        git sha              : $Format:%H$
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


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PlanCreator class from file PlanCreator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .plan_creator import PlanCreator
    return PlanCreator(iface)
