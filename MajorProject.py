print('Start')
print('Imported packages')
from qgis.core import *
from qgis.utils import *
import processing
import os

print('Input Variables')
strDir = 'C:/Users/ethan/Desktop/Uni/GEOM2159_Programming/Project/'
strVector = 'CrakerLakeNP.shp'
strRaster = 'CraterLake_DEM.tif'
intGrid = 80

print('Change directory')
os.chdir(strDir)

print('Add files as Qgs objects')
fileVector = QgsVectorLayer(strVector)
fileRaster = QgsRasterLayer(strRaster)

print('Calculate ProjectCRS')
vectorExtent = fileVector.extent()
centre = vectorExtent.center()
crsCentre = str(centre.x())
crs = QgsCoordinateReferenceSystem('Proj4: +proj=sinu +lon_0=' + crsCentre + '+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
#crs = QgsCoordinateReferenceSystem('Proj4: +proj=sinu +lon_0=-122.13771565755209 +x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
iface.newProject(False)
QgsProject.instance().setCrs(crs)
#iface.mapCanvas().setDestinationCrs(crs)

print('Add layers to QGIS')
iface.addRasterLayer(strRaster, 'CraterLake DEM')
iface.addVectorLayer(strVector, '', 'ogr')
#layerVector.setCrs(crs)

print('Reproject Raster')
#processing.algorithmHelp('gdal:warpreproject')
dctProjRast =  {'INPUT':fileRaster,
                'SOURCE_CRS':fileRaster,
                'TARGET_CRS':crs,
                'RESAMPLING':1,
                'NODATA':None,
                'TARGET_RESOLUTION':None,
                'OPTIONS':'',
                'DATA_TYPE':0,
                'TARGET_EXTENT':None,
                'TARGET_EXTENT_CRS':None,
                'MULTIPLETHREADING':False,
                'EXTRA':'',
                'OUTPUT':'rasterReproject.tif'
                }
processing.run('gdal:warpreproject', dctProjRast)
iface.addRasterLayer('rasterReproject.tif', 'rasterReproject',)

print('Reproject Vector')
#processing.algorithmHelp('native:reprojectlayer')
dctProjVect =  {'INPUT':strVector,
                'TARGET_CRS':crs,
                'OUTPUT':'vectorReproject.shp'
                }
processing.run('native:reprojectlayer', dctProjVect)
iface.addVectorLayer('vectorReproject.shp', '','ogr')

#print('Calculate Grid Extent')
#vectorExtent = layerVector.extent()
#width = vectorExtent.width()
#height = vectorExtent.height()
#print(width)
#print(height)

print('Generate Grid')
#processing.algorithmHelp('qgis:creategrid')
dctGrid =  {'TYPE' : 1,
            'EXTENT' : 'vectorReproject.shp',
            'HSPACING' : 4400,
            'VSPACING' : 440,
            'HOVERLAY' : 0,
            'VOVERLAY' : 0,
            'CRS' : crs,
            'OUTPUT' : 'gridOutput.shp'
            }
outputGrid = processing.run('qgis:creategrid', dctGrid)
#fileGrid = QgsVectorLayer('gridOutput.shp')
fileGrid = iface.addVectorLayer('gridOutput.shp','','ogr')

print('Delete Vertical Lines')
lstDelete = []
gridLines = fileGrid.getFeatures()
for feature in gridLines:
    fid = feature['id']
    left = feature['left']
    right = feature['right']
    if left == right:
        lstDelete.append(fid)

fileGrid.startEditing
fileGrid.dataProvider().deleteFeatures(lstDelete)
fileGrid.commitChanges

print('Clip Grid')
#processing.algorithmHelp('native:clip')
dctClip =  {'INPUT' : fileGrid,
            'OVERLAY' : 'vectorReproject.shp',
            'OUTPUT' : 'clipOutput.shp'
            }
processing.run('native:clip', dctClip)
fileClip = iface.addVectorLayer('clipOutput.shp', '','ogr')
#fileClip = QgsVectorLayer('clipOutput.shp')

print('Lines to Points')
#processing.algorithmHelp('qgis:pointsalonglines')
dctPointsLine =    {'INPUT': fileClip,
                    'DISTANCE':100,
                    'START_OFFSET':0,
                    'END_OFFSET':0,
                    'OUTPUT':'pointLineOutput.shp'
                    }
processing.run('qgis:pointsalonglines', dctPointsLine)
iface.addVectorLayer('pointLineOutput.shp', '','ogr')

print('Add Column')
#processing.algorithmHelp('qgis:addfieldtoattributestable')
dctNewField =  {'INPUT':'pointLineOutput.shp',
                'FIELD_NAME':'Z',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':24,
                'FIELD_PRECISION':0,
                'OUTPUT':'newFieldOutput.shp'
                }
processing.run('qgis:addfieldtoattributestable',dctNewField)
iface.addVectorLayer('newFieldOutput.shp', '','ogr')

print('Point Heights')
#processing.algorithmHelp('grass7:v.what.rast')
dctPointHeights =  {'map':'newFieldOutput.shp',
                    'raster':'rasterReproject.tif',
                    'type':0,
                    'column':'Z',
                    'where':'',
                    '-i':True,
                    'output':'pointHeightOutput.shp',
                    'GRASS_REGION_PARAMETER':'',
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                    'GRASS_SNAP_TOLERANCE_PARAMETER':-1,
                    'GRASS_MIN_AREA_PARAMETER':0.0001,
                    'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'',
                    'GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':True
                    }
processing.run('grass7:v.what.rast',dctPointHeights)
iface.addVectorLayer('pointHeightOutput.shp', '','ogr')

print('Point Coords')
#processing.algorithmHelp('saga:addcoordinatestopoints')
dctPointCoords =   {'INPUT':'pointHeightOutput.shp',
                    'OUTPUT':'pointXYZ.shp'
                    }
processing.run('saga:addcoordinatestopoints',dctPointCoords)
iface.addVectorLayer('pointXYZ.shp','','ogr')