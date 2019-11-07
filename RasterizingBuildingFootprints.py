# -*- coding: utf-8 -*-
"""
Created on Fri Aug 24 16:55:37 2018

@author: Mehdi Heris;
"""

import time
from shapely.geometry import mapping, shape
from shapely.geometry import box as shBox
import fiona
import numpy as np
import rasterio
#from itertools import product


t1=time.clock()

# set the input layers and output locations
inputRaster=r'I:\Buldings\Rasters\new_results\Utah_avg.tif'
inputBuildingsShape2=r'I:\Buldings\Shapefiles\UT\Utah_Corrected.shp'
outputFolder=r'I:\Buldings\Shapefiles\UT'
#outGridShpe=outputFolder+r'\gridDC.shp'



# set the output rasters (results)
bldgMaxToWriteRaster     = outputFolder +r'\bldgMax.tif'
bldgMinToWriteRaster     = outputFolder +r'\bldgMin.tif'
bldgAveToWriteRaster     = outputFolder +r'\bldgAve.tif'
bldgSumToWriteRaster     = outputFolder+ r'\bldgSum.tif'
bldgCountToWriteRaster   = outputFolder+ r'\bldgCount.tif'
bldgCentroidCountToWriteRaster= outputFolder+ r'\bldgCentroidCount.tif'



bldgSumDataType='float32'
bldgMaxDataType='float64'
bldgMinDataType='float64'
bldgAvgDataType='float64'
bldgCntDataType='int16'
bldgCenteriodCntDataType='int16'




with rasterio.open(inputRaster) as nlcdWindow:
    kwds = nlcdWindow.meta.copy()
    thisWindowWidth=nlcdWindow.width
    thisWindowHeight=nlcdWindow.height
    cellSize= kwds['transform'][0]
    topY  = nlcdWindow.bounds[3]
    leftX = nlcdWindow.bounds[0]
    windowShape = nlcdWindow.shape
    topLeftCornerWindow = [nlcdWindow.bounds[0],nlcdWindow.bounds[3]]
    profile = nlcdWindow.profile



# start the arrays for each raster output. the rasters have the same shape as the nlcd window
arBldgSum=np.zeros(windowShape)
arBldgSumAllBldgArea=np.zeros(windowShape)
arBldgMax=np.zeros(windowShape)
arBldgMin=np.zeros(windowShape)
arBldgCount=np.zeros(windowShape)
arBldgCentroid=np.zeros(windowShape)



# read the building shape file as geometries and put them in a list
buildingsPolys = [shape(bldg['geometry']) for bldg in fiona.open(inputBuildingsShape2)]

print ('read the buildings',(time.clock()-t1))

# an error variable to know howw many intersection fail
er=0
# grab each building in this loop
for bldg in buildingsPolys:
    # get the area of the building
    bldgArea=bldg.area
    # get the bound of the building
    bldgBounds=bldg.bounds
    
    # calculate the count of centroid for each cell
    centroidX=(bldg.centroid.coords)[0][0]
    centroidY=(bldg.centroid.coords)[0][1]
    col   = int((centroidX - leftX)/cellSize)
    row   = int((topY - centroidY)/cellSize)
    arBldgCentroid[row,col]+=1
    
    # let's find the distance form the top left corner of the raster
    xDifTL=bldgBounds[0]-topLeftCornerWindow[0]
    yDifTL=topLeftCornerWindow[1]-bldgBounds[3]
    # lets find the top left corner of the first grid cell that is supposed to be intersected later
    colStart=int(xDifTL//30)
    rowStart=int(yDifTL//30)

    # lets find the end row and collumn of the window cells of this building
    colEnd=int((bldgBounds[2]-topLeftCornerWindow[0])//30)+1
    rowEnd=int((topLeftCornerWindow[1]-bldgBounds[1])//30)+1

    # get the shape of the window cell that has intersection with this building
    nmRowWinCell=rowEnd-rowStart
    nmColWinCell=colEnd-colStart
    shapeWinCell=[nmRowWinCell,nmColWinCell]


    # let's go through each cell in the window cells whcih are the cells having intersection with
    # this specific budiling
    for row1 in range(0, shapeWinCell[0]):
        for col1 in range(0,shapeWinCell[1]):
            # the current cell
            thisRow=row1+rowStart
            thisCol=col1+colStart
            #print (thisRow,thisCol)
            #shapely.geometry.box(minx, miny, maxx, maxy, ccw=True)
            # here create a shape polygon geometry of the current cell
            minXBox=thisCol*30+topLeftCornerWindow[0]
            maxYBox=topLeftCornerWindow[1]-(thisRow*30)
            maxXBox=minXBox+30
            minYBox=maxYBox-30
            thisCell=shBox(minXBox, minYBox, maxXBox, maxYBox, ccw=True)
            # run the intersection
            if bldg.intersects(thisCell) ==True:
                try:
                    area = bldg.intersection(thisCell).area
                    #print(area,bldgArea,(thisRow,thisCol))
                    # update the arrays with the values being generated through intersection
                    # count
                    arBldgCount[thisRow,thisCol]=arBldgCount[thisRow,thisCol]+1
                    # sum
                    arBldgSum[thisRow,thisCol]=arBldgSum[thisRow,thisCol]+area
                    # sums of buildings to build average building area later
                    arBldgSumAllBldgArea[thisRow,thisCol]=arBldgSumAllBldgArea[thisRow,thisCol]+bldgArea
                    # Max
                    if arBldgMax[thisRow,thisCol]<area:
                        arBldgMax[thisRow,thisCol]=bldgArea
                    # min
                    if arBldgMin[thisRow,thisCol]==0 or arBldgMin[thisRow,thisCol]>area:
                        arBldgMin[thisRow,thisCol]=bldgArea
                    
                except:
                    er+=1
                    
# calcualate the average building array using sum of building areas and count
arAveBldgArea= np.divide(arBldgSumAllBldgArea,arBldgCount,where=arBldgCount!=0)
print('error is', er)
print ('built all arrays',(time.clock()-t1))




arBldgSum = (arBldgSum).astype(bldgSumDataType)
arAveBldgArea = (arAveBldgArea).astype(bldgAvgDataType)
arBldgMax= (arBldgMax).astype(bldgMaxDataType)
arBldgMin=(arBldgMin).astype(bldgMinDataType)
arBldgCount=arBldgCount.astype(bldgCntDataType)
arBldgCentroid=arBldgCentroid.astype(bldgCenteriodCntDataType)

# write arrays to rasters



profile['dtype']=bldgMaxDataType
with rasterio.open(bldgMaxToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arBldgMax)
    
profile['dtype']=bldgMinDataType    
with rasterio.open(bldgMinToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arBldgMin)
    
profile['dtype']=bldgAvgDataType    
with rasterio.open(bldgAveToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arAveBldgArea)
    
profile['dtype']=bldgSumDataType    
with rasterio.open(bldgSumToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arBldgSum)
    
profile['dtype']=bldgCntDataType    
with rasterio.open(bldgCountToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arBldgCount)


profile['dtype']=bldgCenteriodCntDataType    
with rasterio.open(bldgCentroidCountToWriteRaster, 'w', **profile) as output:
    output.write_band(1,arBldgCentroid)
print ('all done',(time.clock()-t1))
