#ScenarioDamSelector02.py
#Given a database dirname, watershed, objective variables, and list of scenarios,
#select watersheds and points for every existing dam in each scenario
#fade watershed visibility based on individual or compounded fish passage effects.

#Written by Sam Roy
import os
import arcpy
from arcpy import env
from arcpy.sa import *
import h5py
import csv
import sys
import numpy

#input args
InName = sys.argv[1] #hdf5 file name
wshd=sys.argv[2] #watershed name
OV1=sys.argv[3] #objective variable 1 (or MO)
OV2=sys.argv[4] #objective variable 2 (or #)
#sys.argv[5], if present, is a list of scenarios to map
fishpass=0
dampt=0

#environment settings
basedir = r"D:/FoD"#r"G:\GISdrive\FoD"
datadir = basedir + r"/data"
scratchdir = basedir + r"/scratch.gdb"
savedir = datadir + r"/culverts/subset/ScenarioMapsOut/%s/%s_%s"%(wshd,OV1,OV2)

env.workspace = savedir
arcpy.env.overwriteOutput=True
arcpy.CheckOutExtension('Spatial')
DamWshds = datadir + r"/culverts/subset/BarrWshds.shp"
dams = arcpy.MakeFeatureLayer_management(DamWshds)
if dampt:
	DamptFile = datadir + r"/culverts/subset/Barr.shp"
	damPoints = arcpy.MakeFeatureLayer_management(DamptFile)
#fn to determine existence of field
def FieldExist(featureclass, fieldname):
    fieldList = arcpy.ListFields(featureclass, fieldname)

    fieldCount = len(fieldList)

    if (fieldCount == 1):
        return True
    else:
        return False

print savedir

if not os.path.exists(savedir):
	os.makedirs(savedir)
#important column data for search and update
SitesCols = ['BID']

#open the scenarios file
f = h5py.File(InName,'r')
scenarios = numpy.array(list(map(int,rec) for rec in f['/' + wshd + '_' + OV1 + '_' + OV2 + '/s'])) #the /s makes sure you take from the scenarios list
#scenarios = numpy.array(list(map(int,rec) for rec in f['/' + wshd + '/' + OV1+'_' + OV2]))

#import pdb
#pdb.set_trace()

if len(sys.argv) > 5:
	sn=sys.argv[5]
	if ('[' in sn) or ('(' in sn):
		sni=(x-1 for x in map(int,sn[1:len(sn)-1].split(',')))
	else:
		if sn[len(sn)-1] is ',':
			sn=sn[0:len(sn)-1]
		sni=(x-1 for x in map(int,sn.split(',')))
else:
	sni=xrange(scenarios.shape[1])

#import pdb
#pdb.set_trace()


if fishpass:
	if (wshd=='All') or (wshd=='all'):
		dirs=list(basedir + r'/PPF/BarrIndex/' + r for r in list(os.listdir(basedir + r'/PPF/BarrIndex/')) if 'DownDam' in r)
		DownList=numpy.array([]).astype('int')
		for d in xrange(len(dirs)):
			if d==0:
				DownList=numpy.loadtxt(dirs[d],dtype='i4',delimiter=',')[:,0:2]
			else:
				DownList = numpy.concatenate((DownList,numpy.loadtxt(dirs[d],dtype='i4',delimiter=',')[:,0:2]))
	else:
		f2 = basedir + "\PPF\BarrIndex\%sDownDamList.txt"%wshd
		DownList = numpy.loadtxt(f2,dtype='i4',delimiter=',')

	f3 = basedir + "\PPF\BarrData\Barr_2-11-19.csv"
	dataclip = numpy.loadtxt(f3,delimiter=',',skiprows=1,usecols=(67,68,69,70,71,72))
	#fish passage data held in dataclip cols 7-10, DID in 2

g=0 #counter for user number

for i in sni:
	column = '"%s"' % SitesCols[0]
	#pdb.set_trace()
	s = ','.join([str(j) for j in (filter(lambda a: a != 0, scenarios[:,i]))])
	if s:
		g+=1
		exp = column + ' IN (%s)'%s
		ScenSelect = arcpy.SelectLayerByAttribute_management(dams,"NEW_SELECTION",exp)
		result = arcpy.GetCount_management(ScenSelect)
		if dampt:
			import pdb
			pdb.set_trace()
			dpSelect = arcpy.SelectLayerByAttribute_management(damPoints,"NEW_SELECTION",exp)
		print "  scenario %i has %i dams"%(i,int(result.getOutput(0)))
		#pdb.set_trace()
		if fishpass:
			scn=filter(lambda a: a != 0, scenarios[:,i])
			fish=numpy.ones([len(scn),2])
			for j in xrange(len(scn)):
				pointer=scn[j]
				idxF=numpy.where(dataclip[:,0].astype(int)==pointer)[0][0]
				#fish[j,0]=dataclip[idxF,1]*dataclip[idxF,2]
				#fish[j,1]=dataclip[idxF,3]*dataclip[idxF,4]
				while pointer>0:
					idxD=numpy.where(DownList[:,0]==pointer)[0][0]
					if numpy.in1d(pointer,scn)[0]:
						#print 'pointer=%i'%pointer
						idxF=numpy.where(dataclip[:,0].astype(int)==pointer)[0][0]
 						#print 'idxF=%i'%idxF
						fish[j,0]=fish[j,0]*dataclip[idxF,1]*dataclip[idxF,2]
						fish[j,1]=fish[j,1]*dataclip[idxF,3]*dataclip[idxF,4]
					pointer=DownList[idxD][1]
			#add field to the shpfile
			#ScenPolys = arcpy.MakeFeatureLayer_management(ScenSelect)
			if (not FieldExist(ScenSelect, 'Pass')):
				arcpy.AddField_management(ScenSelect,'Pass','FLOAT',4,3)
			if (not FieldExist(ScenSelect, 'PassSal')):
				arcpy.AddField_management(ScenSelect,'PassSal','FLOAT',4,3)
			if (not FieldExist(ScenSelect, 'PassV')):
				arcpy.AddField_management(ScenSelect,'PassV','FLOAT',4,3)
			if (not FieldExist(ScenSelect, 'PassSalV')):
				arcpy.AddField_management(ScenSelect,'PassSalV','FLOAT',4,3)
			Cols = ['DID','Pass','PassSal','PassV','PassSalV']
			cur=arcpy.da.UpdateCursor(ScenSelect,Cols)
			for row in cur:
				try:
					idxS=numpy.where(numpy.in1d(scn,row[0]).astype(int))[0][0]
					row[1] = fish[idxS,0]*100
					row[2] = fish[idxS,1]*100
					row[3] = pow(fish[idxS,0],0.25)*100
					if row[3]>90:
						row[3]=90
					row[4] = pow(fish[idxS,1],0.25)*100
					if row[4]>90:
						row[4]=90
				except IndexError:
					row[1] = 100
					row[2] = 100
					row[3] = 100
					row[4] = 100
					continue
				#index the match
				cur.updateRow(row)
		arcpy.CopyFeatures_management(ScenSelect, savedir + "\%s_%s_%s_%i.shp"%(wshd,OV1,OV2,i))
		if dampt:
			arcpy.CopyFeatures_management(dpSelect, savedir + "\%s_%s_%s_%i_dampts.shp"%(wshd,OV1,OV2,i))
		if g<10:
			gstr="0%s"%g
		else:
			gstr="%s"%g
		#os.system("PPF_mapper03.py %s %s %s %s %s"%(wshd,OV1,OV2,i,gstr))
