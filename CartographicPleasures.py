# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterRasterLayer,
                       QgsCoordinateReferenceSystem,
                       QgsProject)
import processing
import os

class CartographicPleasuresScript(QgsProcessingAlgorithm):
    """
    This script takes a vector and raster layer, converts them to local coordinate
    reference system and generates a comma seperated values file to use for 
    the CartohraphicPleasures R code.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    VINPUT = 'VECTOR INPUT'
    RINPUT = 'RASTER INPUT'
    OUTPUT = 'OUTPUT'
    SPACING = 'SPACING'
    CRS = 'CRS'
    LINES = 'LINES'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CartographicPleasuresScript()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Cartographic Pleasures'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Cartographic Pleasures')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Cartographic Pleasures')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Cartographic Pleasures'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(".tif & .shp to pointXYZ (WIP)")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.VINPUT,
                self.tr('Input Vector layer'),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        # We add the input raster features source.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RINPUT,
                self.tr('Input Raster layer')
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.LINES,
                self.tr('Number of Lines'),
                80,
                self.CRS,
                False,
                0.000001
            )
        )

        self.addParameter(
            QgsProcessingParameterDistance(
                self.SPACING,
                self.tr('Point Spacing'),
                100,
                self.CRS,
                False,
                0.000001
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        vSource = self.parameterAsSource(
            parameters,
            self.VINPUT,
            context
        )

        rSource = self.parameterAsRasterLayer(
            parameters,
            self.RINPUT,
            context
        )
        
        lines = self.parameterAsInt(
            parameters,
            self.LINES,
            context
        )
        
        spacing = self.parameterAsInt(
            parameters,
            self.SPACING,
            context
        )
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            source.sourceCrs()
        )
        
        # Send some information to the user
        feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))
        
        
        #print('Add files as Qgs objects')
        #fileVector = QgsVectorLayer(source)
        #fileRaster = QgsRasterLayer(rSource)

        #print('Calculate ProjectCRS')
        vectorExtent = vSource.sourceExtent()
        centre = vectorExtent.center()
        crsCentre = str(centre.x())
        crs = QgsCoordinateReferenceSystem('Proj4: +proj=sinu +lon_0=' + crsCentre + '+x_0=0 +y_0=0 +ellps=WGS84 +units=m +no_defs')
        QgsProject.instance().setCrs(crs)


        #print('Reproject Raster')
        #processing.algorithmHelp('gdal:warpreproject')
        dctProjRast =  {'INPUT':rSource,
                        'SOURCE_CRS':rSource,
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
                        'OUTPUT':'memory'
                        }
        rasterReproject = processing.run('gdal:warpreproject', dctProjRast)

        #print('Reproject Vector')
        #processing.algorithmHelp('native:reprojectlayer')
        dctProjVect =  {'INPUT' : vSource,
                        'TARGET_CRS' : crs,
                        'OUTPUT' : 'memory'
                        }
        vectorReproject = processing.run('native:reprojectlayer', dctProjVect)

        print('Calculate Grid Extent')
        extentVector = QgsVectorLayer('vectorReproject.shp')
        vectorExtent = extentVector.extent()
        width = vectorExtent.width()
        height = vectorExtent.height()
        hspacing = height / 2
        vspacing = width / lines

        #print('Generate Grid')
        #processing.algorithmHelp('qgis:creategrid')
        dctGrid =  {'TYPE' : 1,
                    'EXTENT' : vectorReproject,
                    'HSPACING' : hspacing,
                    'VSPACING' : vspacing,
                    'HOVERLAY' : 0,
                    'VOVERLAY' : 0,
                    'CRS' : crs,
                    'OUTPUT' : 'memory'
                    }
        outputGrid = processing.run('qgis:creategrid', dctGrid)

        #print('Delete Vertical Lines')
        lstDelete = []
        gridLines = outputGrid.getFeatures()
        for feature in gridLines:
            fid = feature['id']
            left = feature['left']
            right = feature['right']
            if left == right:
                lstDelete.append(fid)

        outputGrid.startEditing
        outputGrid.dataProvider().deleteFeatures(lstDelete)
        outputGrid.commitChanges

        #print('Clip Grid')
        #processing.algorithmHelp('native:clip')
        dctClip =  {'INPUT' : outputGrid,
                    'OVERLAY' : 'vectorReproject.shp',
                    'OUTPUT' : 'memory'
                    }
        clipOutput = processing.run('native:clip', dctClip)

        #print('Lines to Points')
        #processing.algorithmHelp('qgis:pointsalonglines')
        dctPointsLine =    {'INPUT': clipOutput,
                            'DISTANCE': spacing,
                            'START_OFFSET':0,
                            'END_OFFSET':0,
                            'OUTPUT':'memory'
                            }
        pointsOutput = processing.run('qgis:pointsalonglines', dctPointsLine)

        #print('Add Column')
        #processing.algorithmHelp('qgis:addfieldtoattributestable')
        dctNewField =  {'INPUT': pointsOutput,
                        'FIELD_NAME':'Z',
                        'FIELD_TYPE':0,
                        'FIELD_LENGTH':24,
                        'FIELD_PRECISION':0,
                        'OUTPUT':'memory'
                        }
        fieldOutput = processing.run('qgis:addfieldtoattributestable',dctNewField)

        #print('Point Heights')
        #processing.algorithmHelp('grass7:v.what.rast')
        dctPointHeights =  {'map': fieldOutput,
                            'raster':'rasterReproject.tif',
                            'type':0,
                            'column':'Z',
                            'where':'',
                            '-i':True,
                            'output':'memory',
                            'GRASS_REGION_PARAMETER':'',
                            'GRASS_REGION_CELLSIZE_PARAMETER':0,
                            'GRASS_SNAP_TOLERANCE_PARAMETER':-1,
                            'GRASS_MIN_AREA_PARAMETER':0.0001,
                            'GRASS_OUTPUT_TYPE_PARAMETER':0,
                            'GRASS_VECTOR_DSCO':'',
                            'GRASS_VECTOR_LCO':'',
                            'GRASS_VECTOR_EXPORT_NOCAT':True
                            }
        heightOutput = processing.run('grass7:v.what.rast',dctPointHeights)

        #print('Point Coords')
        #processing.algorithmHelp('saga:addcoordinatestopoints')
        dctPointCoords =   {'INPUT':heightOutput,
                            'OUTPUT':'memory'
                            }
        coordsOutput = processing.run('saga:addcoordinatestopoints',dctPointCoords)

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: dest_id}
