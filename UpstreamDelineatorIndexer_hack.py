#For every dam, look upstream and identify all other dams.
#Make a list of the dam IDs. This info is used to determine connectivity above the most downstream dam.
#Each dam has an array of IDs attached to it.
#This one is for the Merrimack, but can me modified for another shed.

#arg1 = directory of barrier shapefile
#arg2 = name of shape file


#Steps:
#get a dam
#build its watershed using dam location (already snapped to flow lines) and flow direction
#convert raster wshd to polygon
#select dams within wshd polygon
#add dam IDs to an array
#save array as text named after the hosting dam

#Written by Sam Roy
import os
import arcpy
from arcpy import env
from arcpy.sa import *
import numpy
import sys

#input args
datadir=sys.argv[1] #indicate the directory of the data

print datadir
#environment settings
savedir = datadir + r"\out"
env.workspace = savedir
arcpy.env.overwriteOutput=True
arcpy.CheckOutExtension('Spatial')
BarrierWshdst = savedir + r"\BarrierWshdstemp.shp"
Site = savedir + r"\Site.shp"
#datasets
#Pre-existing impoundments
BarrierFile = datadir + r"/" + sys.argv[2]
print BarrierFile
Barrier = arcpy.MakeFeatureLayer_management(BarrierFile)

#Flow direction
FD = r"D:/FoD/data/france/franceFD.tif"#r"D:\FoD\data\NHD\NHDPlusNE\NHDPlus01\NHDPlusFdrFac01a\fdr" #switch to \fdr if area is outside of PPF project area

#Projection data
spatial_refFD = arcpy.Describe(FD).spatialReference
UTM = arcpy.Describe(Barrier).spatialReference

#important column data for search and update
SitesCols = ['BID']#['OBJECTID','BarrierCla','1_skm']

#Append trigger
trigger=1
#counter=0
cur=arcpy.da.SearchCursor(Barrier,SitesCols) #just go through ones that previously passed the environment/development/impoundment tests.
for row in cur:
	#Get ID
	ID = int(row[0])
	print '%s' %ID
	#if row[1]=='No Barrier' or row[1]=='No Crossing' or row[2]==0:
	#	continue
	#if row[1]=='Unknown':
	#	continue
	#counter+=1
	#if counter>=100: #just for now, cap it off to prove things can work
		#break

	#if os.path.isfile(savedir + r"\%s.txt"%ID):
		#trigger+=1
		#continue

	#Get dam site
	#Define site selection expression
	#print "defining dam site"
	column = '"%s"' % SitesCols[0]
	expS = column + " = %i" % ID
	#import pdb; pdb.set_trace()
	#Select current Site
	SiteSelect = arcpy.SelectLayerByAttribute_management(Barrier,"NEW_SELECTION",expS)

	wshdPoly = savedir + r"\Barrier_%s.shp" %ID
	if not os.path.isfile(wshdPoly):
		print "constructing watershed polygon"
		#Necessary to project to FD projection
		#print "projecting"
		#import pdb; pdb.set_trace()
		#arcpy.Project_management(SiteSelect,Site,spatial_refFD)
		#getcount = int(arcpy.GetCount_management("Parcel").getOutput(0))
		#create watershed mask
		#print "masking"
		#wshd = Watershed(FD,Site)
		##wshd.save(savedir + r"\Dam_%s.tif" %ID)
		arcpy.RasterToPolygon_conversion(wshd,wshdPoly,"NO_SIMPLIFY","VALUE")

		#add damID field
		#print "Adding ID"
		arcpy.AddField_management (wshdPoly, "SITEID", "LONG", 10)
		arcpy.CalculateField_management (wshdPoly, "SITEID", '%s' %ID)

	#Select dams that fit in the wshd
	#print "selecting upstream dams"
	UpSelect = arcpy.SelectLayerByLocation_management(Barrier,"INTERSECT",wshdPoly,0,"NEW_SELECTION")

	#iterate through these dams and add their ID to an array
	#print "adding dams to the upstream list"
	result = arcpy.GetCount_management(UpSelect)
	UpCnt = int(result.getOutput(0))
	UpDams = numpy.zeros(UpCnt)
	i=0
	cur2 = arcpy.da.SearchCursor(UpSelect,SitesCols)
	for row2 in cur2:
		UpDams[i] = row2[0]
		i+=1

	#Save array of upstream dam ids. I think the host dam should also be in this array.
	#That's okay, can be dealt with during processing
	numpy.savetxt(savedir + r"\%s.txt" %ID,UpDams,fmt='%i')

	#Merge the shed masks together
	#print "merging watersheds"
	if trigger == 1:
		arcpy.CreateFeatureclass_management(savedir,"BarrierWshdstemp.shp","POLYGON",wshdPoly,"","",UTM)
		trigger+=1
	if trigger >= 1:
		arcpy.Append_management(wshdPoly,BarrierWshdst,"NO_TEST")


#arcpy.Project_management(BarrierWshdst,DamExpWshds,UTM)
arcpy.AddField_management(BarrierWshdst, "area_skm", "DOUBLE",12,6)
arcpy.CalculateField_management(BarrierWshdst, "area_skm","!SHAPE.AREA@SQUAREKILOMETERS!","PYTHON")
##
