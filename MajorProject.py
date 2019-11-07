print('Start')
print('Imported packages')
#Imports for program
from qgis.core import *
from qgis.utils import *
import processing
import os

print('Input Variables')
#Variables required to make the program run
#Directory for the program to run in
strDir = 'C:/Users/ethan/Desktop/Uni/GEOM2159_Programming/Project/'
#Your shapefile which will be the boundary and extent of the area of interest
strVector = 'CrakerLakeNP.shp'
#Your DEM file to use for heights
strRaster = 'CraterLake_DEM.tif'
#Number of Horizontal lines for your output
intGrid = 80
#The spacing for your points.
#Large numbers smooths the model, smaller is more accurate
#Be cautious with this depending on your shapefile extent
intPoint = 100

print('Change directory')
os.chdir(strDir)

print('Add files as Qgs objects')
fileVector = QgsVectorLayer(strVector)
fileRaster = QgsRasterLayer(strRaster)

print('Calculate ProjectCRS')
#Get Vector extent
vectorExtent = fileVector.extent()
#Find the centre
centre = vectorExtent.center()
#Convert to string
crsCentre = str(centre.x())
#Generate a new CRS from the centre of the desired extent using a Proj4 projection string
crs = QgsCoordinateReferenceSystem('Proj4: +proj=sinu +lon_0=' + crsCentre + '+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
#Create new project instance
iface.newProject(False)
#Set new instance to the new CRS
QgsProject.instance().setCrs(crs)

print('Reproject Raster')
#Reprojects the raster to the new CRS so other processes can runn correctly
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
                'OUTPUT':'memory:ProjRast'
                }
rasterReproject = processing.run('gdal:warpreproject', dctProjRast)['OUTPUT']
#This is required to make the raster layer work in GRASS and SAGA
ProjRast =  QgsRasterLayer(rasterReproject)

print('Reproject Vector')
#Reprojects the vector to the new CRS so the vector is in metres
#processing.algorithmHelp('native:reprojectlayer')
dctProjVect =  {'INPUT':strVector,
                'TARGET_CRS':crs,
                'OUTPUT':'memory:ProjVect'
                }
vectorReproject = processing.run('native:reprojectlayer', dctProjVect)['OUTPUT']

print('Calculate Grid Lines')
#Get object extent
vectorExtent = vectorReproject.extent()
#Get extent width
width = vectorExtent.width()
#Get extent height
height = vectorExtent.height()
#Will generate 3 vertical lines due to this calc
hspacing = height / 2
#Will generate a number of horizontal lines equal to your input at start of program
vspacing = width / intGrid

print('Generate Grid')
#Generate Grid in extent
#processing.algorithmHelp('qgis:creategrid')
dctGrid =  {'TYPE' : 1,
            'EXTENT' : vectorReproject,
            'HSPACING' : hspacing,
            'VSPACING' : vspacing,
            'HOVERLAY' : 0,
            'VOVERLAY' : 0,
            'CRS' : crs,
            'OUTPUT' : 'memory:Grid'
            }
outputGrid = processing.run('qgis:creategrid', dctGrid)['OUTPUT']

print('Delete Vertical Lines')
#New list
lstDelete = []
#Get features in grid file
gridLines = outputGrid.getFeatures()
#For each feature, get the id, left and right.
#Append id to the empty list if left and right values are equal
for feature in gridLines:
    fid = feature['id']
    left = feature['left']
    right = feature['right']
    if left == right:
        lstDelete.append(fid)

#Edit file and delete all ids with same left and right using the list.
outputGrid.startEditing
outputGrid.dataProvider().deleteFeatures(lstDelete)
outputGrid.commitChanges

print('Clip Grid')
#Clip grid based on the shapefile boundary
#processing.algorithmHelp('native:clip')
dctClip =  {'INPUT' : outputGrid,
            'OVERLAY' : vectorReproject,
            'OUTPUT' : 'memory:Clip'
            }
outputClip = processing.run('native:clip', dctClip)['OUTPUT']

print('Lines to Points')
#All lines generate points spaced by input
#processing.algorithmHelp('qgis:pointsalonglines')
dctPointsLine =    {'INPUT': outputClip,
                    'DISTANCE':intPoint,
                    'START_OFFSET':0,
                    'END_OFFSET':0,
                    'OUTPUT':'memory:PointsLine'
                    }
outputPoints = processing.run('qgis:pointsalonglines', dctPointsLine)['OUTPUT']

print('Add Column')
#Add a new column to the generated point file
#processing.algorithmHelp('qgis:addfieldtoattributestable')
dctNewField =  {'INPUT':outputPoints,
                'FIELD_NAME':'Z',
                'FIELD_TYPE':0,
                'FIELD_LENGTH':24,
                'FIELD_PRECISION':0,
                'OUTPUT':'memory:NewField'
                }
outputPointsT = processing.run('qgis:addfieldtoattributestable',dctNewField)['OUTPUT']
#iface.addVectorLayer(outputPointsT, '','ogr')

print('Point Heights')
#Get point heights from the DEM
#processing.algorithmHelp('grass7:v.what.rast')
dctPointHeights =  {'map':outputPointsT,
                    'raster':ProjRast,
                    'type':0,
                    'column':'Z',
                    'where':'',
                    '-i':True,
                    'output':'memory:PointHeights',
                    'GRASS_REGION_PARAMETER':'',
                    'GRASS_REGION_CELLSIZE_PARAMETER':0,
                    'GRASS_SNAP_TOLERANCE_PARAMETER':-1,
                    'GRASS_MIN_AREA_PARAMETER':0.0001,
                    'GRASS_OUTPUT_TYPE_PARAMETER':0,
                    'GRASS_VECTOR_DSCO':'',
                    'GRASS_VECTOR_LCO':'',
                    'GRASS_VECTOR_EXPORT_NOCAT':True
                    }
outputHeights = processing.run('grass7:v.what.rast',dctPointHeights)['output']
pointHeights = QgsVectorLayer(outputHeights)

print('Point Coords')
#Get coordinates for all points using the CRS we generated
#processing.algorithmHelp('saga:addcoordinatestopoints')
dctPointCoords =   {'INPUT':pointHeights,
                    'OUTPUT':'PointCoords.shp'
                    }
processing.run('saga:addcoordinatestopoints',dctPointCoords)
iface.addVectorLayer('PointCoords.shp','','OGR')

#print('Point Layer to CSV')
#QgsVectorFileWriter.writeAsVectorFormat(outputCoords,'pointXYZ.csv','UTF-8', driverName='CSV')