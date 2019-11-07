print('Start')
print('Imported packages')
from qgis.core import *
from qgis.utils import *
import processing
import os

print('Input Variables')
#Required Variables to be edited by user
#Directory for files
strDir = 'C:/Users/ethan/Desktop/Uni/GEOM2159_Programming/Project/'
#Vector File Name
#Script will use this boundary for point generation
strVector = 'CrakerLakeNP.shp'
#Raster File Name
strRaster = 'CraterLake_DEM.tif'
#Number of Point Rows
intGridRows = 80
#Point Spacing
intPointSpacing = 100

print('Change directory')
os.chdir(strDir)

print('Add files as Qgs objects')
fileVector = QgsVectorLayer(strVector)
fileRaster = QgsRasterLayer(strRaster)

print('Calculate ProjectCRS')
#Get Vector Extent
vectorExtent = fileVector.extent()
#Get Extents centre
centre = vectorExtent.center()
#Convert to string
crsCentre = str(centre.x())
#Build new CRS using the Proj4 string centred around extent
crs = QgsCoordinateReferenceSystem('Proj4: +proj=sinu +lon_0=' + crsCentre + '+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
#New Project
iface.newProject(False)
#Change Projects CRS
QgsProject.instance().setCrs(crs)

print('Reproject Raster')
#Reproject Raster to new CRS so other functions work add output to QGS
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
fileReprRast = iface.addRasterLayer('rasterReproject.tif', 'rasterReproject',)

print('Reproject Vector')
#Reproject Vector to enable other functions to run add output to QGS
#processing.algorithmHelp('native:reprojectlayer')
dctProjVect =  {'INPUT':strVector,
                'TARGET_CRS':crs,
                'OUTPUT':'vectorReproject.shp'
                }
processing.run('native:reprojectlayer', dctProjVect)
fileReprVect = iface.addVectorLayer('vectorReproject.shp', '','ogr')

print('Calculate Grid Extent')
#Get object extent
vectorExtent = fileReprVect.extent()
#Get extent width
width = vectorExtent.width()
#Get extent height
height = vectorExtent.height()
#Will generate 3 vertical lines due to this calc
hspacing = height / 2
#Will generate a number of horizontal lines equal to your input at start of program
vspacing = width / intGridRows

print('Generate Grid')
#Generate Grid using Vector Extent calcs add output to QGS
#processing.algorithmHelp('qgis:creategrid')
dctGrid =  {'TYPE' : 1,
            'EXTENT' : fileReprVect,
            'HSPACING' : hspacing,
            'VSPACING' : vspacing,
            'HOVERLAY' : 0,
            'VOVERLAY' : 0,
            'CRS' : crs,
            'OUTPUT' : 'gridOutput.shp'
            }
processing.run('qgis:creategrid', dctGrid)
fileGrid = iface.addVectorLayer('gridOutput.shp','','ogr')

print('Delete Vertical Lines')
#New list
lstDelete = []
#Get features in grid file
gridLines = fileGrid.getFeatures()
#For each feature, get the id, left and right.
#Append id to the empty list if left and right values are equal
for feature in gridLines:
    fid = feature['id']
    left = feature['left']
    right = feature['right']
    if left == right:
        lstDelete.append(fid)

#Edit file and delete all ids with same left and right using the list.
fileGrid.startEditing
fileGrid.dataProvider().deleteFeatures(lstDelete)
fileGrid.commitChanges

print('Clip Grid')
#Clip grid based on the shapefile boundary and add output to QGS
#processing.algorithmHelp('native:clip')
dctClip =  {'INPUT' : fileGrid,
            'OVERLAY' : fileReprVect,
            'OUTPUT' : 'clipOutput.shp'
            }
processing.run('native:clip', dctClip)
fileClip = iface.addVectorLayer('clipOutput.shp', '','ogr')

print('Lines to Points')
#All lines generate points spaced by input add output to QGS
#processing.algorithmHelp('qgis:pointsalonglines')
dctPointsLine =    {'INPUT': fileClip,
                    'DISTANCE':intPointSpacing,
                    'START_OFFSET':0,
                    'END_OFFSET':0,
                    'OUTPUT':'pointLineOutput.shp'
                    }
processing.run('qgis:pointsalonglines', dctPointsLine)
filePoints = iface.addVectorLayer('pointLineOutput.shp', '','ogr')

print('Add Column')
#Add a new column to the generated point file add output to QGS
#processing.algorithmHelp('qgis:addfieldtoattributestable')
dctNewField =  {'INPUT':filePoints,
                'FIELD_NAME':'Z',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':24,
                'FIELD_PRECISION':0,
                'OUTPUT':'newFieldOutput.shp'
                }
processing.run('qgis:addfieldtoattributestable',dctNewField)
fileColumn = iface.addVectorLayer('newFieldOutput.shp', '','ogr')

print('Point Heights')
#Get point heights from the DEM add output to QGS
#processing.algorithmHelp('grass7:v.what.rast')
dctPointHeights =  {'map':fileColumn,
                    'raster':fileReprRast,
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
fileX = iface.addVectorLayer('pointHeightOutput.shp', '','ogr')

print('Point Coords')
#Get coordinates for all points using the CRS we generated add output to QGS
#processing.algorithmHelp('saga:addcoordinatestopoints')
dctPointCoords =   {'INPUT':fileX,
                    'OUTPUT':'pointXYZ.shp'
                    }
processing.run('saga:addcoordinatestopoints',dctPointCoords)
fileXYZ = iface.addVectorLayer('pointXYZ.shp','','ogr')
