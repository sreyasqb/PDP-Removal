#QB

from qgis.core import QgsGeometry, NULL
from qgis.gui import QgsRubberBand
# from PyQt5.QtGui import QDialog
from PyQt5.QtWidgets import QDialog,QMessageBox
# from PyQt4.QtGui import QColor, QInputDialog, QDialog, QFileDialog
# from PyQt4.QtCore import *
from PyQt5 import uic
from PyQt5.QtGui import QColor
import processing
import math
import numpy as np
import time
from shapely.geometry import Point, Polygon 
import traceback
import time
from math import sin, cos, radians
from shapely.geometry import LineString
from shapely import affinity
import math

# FORM_CLASS, _ = uic.loadUiType(QgsProject.instance().homePath() + "/User_Interface2.ui")
FORM_CLASS, _ = uic.loadUiType("H:\\training\\User_Interface2.ui")   


class Dialog_Input(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(Dialog_Input, self).__init__(parent)
        self.setupUi(self)

dlg = Dialog_Input()
dlg.show()

def welfile():
    dlg.wellsfile.setText(QFileDialog.getOpenFileName(
                         dlg,
                         "Browse for Wells file",
                         QgsProject.instance().homePath(),"Shape File (*.shp )")[0])



def create_points(startpoint,
                  endpoint,
                  distance,
                  geom,
                  fid,
                  divide):
    """Creating Points at coordinates along the line
    """
    # don't allow distance to be zero or/and loop endlessly
    QgsDistanceArea().setEllipsoid(
        QgsProject.instance().ellipsoid()
        )

    if distance <= 0:
        distance = QgsDistanceArea().measureLength(geom) #geom.length()

    length = QgsDistanceArea().measureLength(geom) #geom.length()

    if length < endpoint:
        endpoint = length

    if divide > 0:
        length2 = length
        if startpoint > 0:
            length2 = length - startpoint
        if endpoint > 0:
            length2 = endpoint
        if startpoint > 0 and endpoint > 0:
            length2 = endpoint - startpoint
        distance = length2 / divide
        current_distance = distance
    else:
        current_distance = distance

    feats = []

    if endpoint > 0:
        length = endpoint

    # set the first point at startpoint
    point = geom.interpolate(startpoint)
    # convert 3D geometry to 2D geometry as OGR seems to have problems with this
    
    point = QgsGeometry.fromPointXY(point.asPoint())
    field_id = QgsField(name="id", type=QVariant.String)
    fieldX = QgsField(name="xValue", type=QVariant.Double)
    fieldY = QgsField(name="yValue", type=QVariant.Double)

    fields = QgsFields()

    fields.append(field_id)
    fields.append(fieldX)
    fields.append(fieldY)

    
    counter = 0


    point = geom.interpolate(startpoint + current_distance)
    pointValue = QgsGeometry.asPoint(point)
    # Create a new QgsFeature and assign it the new geometry


    feature = QgsFeature(fields)
    feature['xValue'] = pointValue.x()
    feature['yValue'] = pointValue.y()
    feature['id'] = fid
    
    feature.setGeometry(point)
    feats.append(feature)
    current_distance = current_distance + distance
    counter+=1

    return feats


def points_along_line(layerout,
                      startpoint,
                      endpoint,
                      distance,
                      layer,
                      apiId,
                      pdpId,
                      regions,
                      divide=0):
    """Adding Points along the line
    """

    crs = layer.crs().authid()



    layer_type = "memory"

    virt_layer = QgsVectorLayer("Point?crs=%s" % crs,
                                layerout,
                                layer_type)
    provider = virt_layer.dataProvider()
    virt_layer.startEditing()   # actually writes attributes

    units = layer.crs().mapUnits()

    unitname = QgsUnitTypes.toString(units)
    provider.addAttributes([QgsField("api14", QVariant.String),
                            QgsField("xValue", QVariant.Double),
                            QgsField("yValue", QVariant.Double)])


    # Loop through all (selected) features

    midPoints = []

    pdpIndex = [field.name() for field in layer.fields()].index(pdpId)


    for feature in layer.getFeatures():
        geom = feature.geometry()
        # Add feature ID of selected feature
        # fid = feature.id()
        fid = feature[apiId]
        # wellName = str(feature[apiId])
        featureDSUId = str(feature[pdpId])
        # if featureDSUId not in wells:
        #     wells[featureDSUId] = [wellName]
        # else:
        #     wells[featureDSUId].append(wellName)
        if not geom:
            QgsMessageLog.logMessage("No geometry", "QChainage")
            continue

        featurePoint = create_points(startpoint,
                                 endpoint,
                                 distance,
                                 geom,
                                 fid,
                                 divide)
        pointGeom = featurePoint[0].geometry()
        if not regions[featureDSUId].contains(pointGeom):
            print(fid)
            # print()
            with edit(layer):
                layer.changeAttributeValue(feature.id(),pdpIndex,NULL)
                
        # if pointGeom
        provider.addFeatures(featurePoint)
        virt_layer.updateExtents()

    print('done')
    proj = QgsProject.instance()
    proj.addMapLayers([virt_layer])
    virt_layer.commitChanges()
    virt_layer.reload()
    virt_layer.triggerRepaint()
    return

def getAllInfo():
    # wells_line_file = dlg.wellsfile.text()

    acreage_file = 'H:\\training\\UpCurve DSU_UTM.shp'
    wells_line_file = 'H:\\training\\UpCurve PDP_UTM.shp'
    start_time = time.time()
    acreage = iface.addVectorLayer(acreage_file,"Acreage","ogr")
    wells_line = iface.addVectorLayer(wells_line_file,"Wells Line","ogr")
    pdpId = 'DSU ID'
    dsuId = 'UID_NEW'
    apiId = 'api14'
    
    
    regions = {}
    for feature in acreage.getFeatures():
        geom =  feature.geometry().asMultiPolygon()
        polygon = QgsGeometry.fromMultiPolygonXY( geom )
        featureDSUId = str(feature[dsuId]) 
        regions[featureDSUId] = polygon
    # print(regions)
    # print('done')

    points_along_line('center points',0,0,1,wells_line,apiId,pdpId,regions,divide = 2)

dlg.wellsbrowse.clicked.connect(welfile)
# dlg.opbrowse.clicked.connect(opfolderr)

dlg.startbutton.clicked.connect(getAllInfo)
dlg.bufferValue.setEnabled(False)

result = dlg.exec_()
