#damDelineateByFlowlines.py
#written by Sam Roy, 4/15/19
#This script uses the NHDPlus_v2 dataset to delineate dam upstream watersheds, useful for determining upstream resources
#Designed specifically to estimate amount of American Shad habitat upstream of dams along the entire east coast of the US. Project headed by Joe Zydlewski

#Notes on previous versions, improvements
#This approach replaces a previous version that used NHD flow direction rasters to delineate each dam watershed entirely. That takes significantly more time.
#This approach also importantly does not require the use of arcpy, there is no need for an ARC license :)

#Datasets used:
#NHD Plus, version 2, east coast HUCs (NE,MA,SA)
    #NHDPlusflowline.shp
    #NHDPlusCatchment.shp
    #NHDPlusAttributes.dbf
    #NHDPlusEROMExtension.dbf
#Dam geodatabase provided by TNC:
    #SEACAP for southern atlantic states
    #Northeast Aquatic Connectivity geodatabase for north atlantic states

#useful definitions
#COMID: unique identification number given to each flowline and associated catchment

#import necessary libraries
import numpy as np
import os
import sys
#debug
import pdb

#user input args
place=sys.argv[1]
width=float(sys.argv[2])
slope=float(sys.argv[3])

#declare directories/files
basedir=r"D:/FoD/data/"
savedir=r"D:/FoD/data/joe/watershedFlowlineLists/"
f_dams=basedir + r"joe/damCOMIDtest%s.csv" %place #file containing dam-flowline/catchment linked COMIDs. These are actually linked to catchments, not flowlines, because of occasional offset in boundaries of both. More important to match dam to its containing catchment
f_outlets=basedir + r"joe/outletCOMIDtest%s.csv" %place #file containing dam-flowline/catchment linked COMIDs. These are actually linked to catchments, not flowlines, because of occasional offset in boundaries of both. More important to match dam to its containing catchment
f_chandims=basedir + r"joe/CHANDIMtest%s.csv" % place #these data come from the EROMextension and simple geomorph rules for bankfull width
f_lines=basedir + r"joe/flownets/COMIDflownet%s.csv" % place
#import data
features1=np.loadtxt(f_dams,delimiter=',',skiprows=1,usecols=(1))
features2=np.loadtxt(f_outlets,delimiter=',',skiprows=1,usecols=(1))
features=np.concatenate((features1,features2))
IDs1=np.genfromtxt(f_dams,delimiter=',',skip_header=1,usecols=(0),dtype='str')
IDs2=np.genfromtxt(f_outlets,delimiter=',',skip_header=1,usecols=(0),dtype='str')
IDs=np.concatenate((IDs1,IDs2))
type1=np.genfromtxt(f_dams,delimiter=',',skip_header=1,usecols=(2),dtype='str')
type2=np.genfromtxt(f_outlets,delimiter=',',skip_header=1,usecols=(0),dtype='str')
type=np.concatenate((type1,type2))
chandims=np.loadtxt(f_chandims,delimiter=',',skiprows=1,usecols=(0,1,4,5))
flow=np.loadtxt(f_lines,delimiter=',',skiprows=1,usecols=(0,3))

#optional input args: array of decisions user can provide for each dam
if len(sys.argv)>4:
    f_decisions = sys.argv[4]
    decisions = np.genfromtxt(f_decisions,delimiter=',',dtype='str')
else:
    decisions = ['keep'] * type[type == 'dam'].size
    decisions.extend(['outlet'] * type[type == 'outlet'].size)
    decisions=np.array(decisions)

#optional input args: array of passage probabilities user can provide for each dam
if len(sys.argv)>5:
    f_passage = sys.argv[5]
    passage = np.loadtxt(f_passage,delimiter=',')
else:
    passage = [0.] * type[type == 'dam'].size #assume dams have 0% passage unless stated otherwise by user
    passage.extend([1.] * type[type == 'outlet'].size) #outlets must have passage = 1 (100%)
    passage = np.array(passage)
    passageComp = passage

up=[] #declare the upstream list as empty

#write-out file
f = open(basedir + r"joe/habitatOut/Habitat%s_wd%sm_slp%s.csv" % (place, width, slope), "w")
f.write('UNIQUE_ID, type, catchmentID, habitat_sqkm, habitatSegment_sqkm\n')

#loop through dams, retieve full list of upstream flowlines/catchments saved to txt
for i in xrange(features.size):
    #if not os.path.isfile(savedir + 'dam_%i_wfll.csv' % int(dams[i])):
    print '%i of %i' % (i+1, len(features)) #show them you're working on it
    current=np.array([features[i]]) #declare the current search location as dam[i]
    #current=np.array([6290171])
    watershed=[] #declare the list of upstream COMIDs
    hab=0.
    habseg=0.
    #import pdb
    #pdb.set_trace()
    while np.sum(current)>0: #break this while loop if there are no more upstream flowlines
        watershed=np.concatenate([watershed,current])
        #sum habitat
        hab = hab + np.sum(chandims[np.isin(chandims[:,0],current),1]*(chandims[np.isin(chandims[:,0],current),3]/1e3))
        pdb.set_trace()
        #determine if upper catchments are in or above other upstream dams, remove these for calculation of habitat segment between features
        if np.any(np.isin(current,features)) and np.isin(features[i],current,invert=True):
            currentSeg = np.isin(current,features,invert=True) #separate index array currentSeg = catchments that do not host dams/features
        habseg = habseg + np.sum(chandims[np.isin(chandims[:,0],currentSeg),1]*(chandims[np.isin(chandims[:,0],currentSeg),3]/1e3))

        for j in xrange(current.size): #loop through list of dams that were upstream
            #find match of current COMID in 'TO' column of flow, retrieve COMID in 'FROM' column. We are looking upstream for COMIDS.
            #print '   upstream number %i' % j
            #import pdb
            #pdb.set_trace()
            up=np.concatenate([up,flow[flow[:,1]==current[j],0]])
        current=np.unique(up[up>0]) #take the unique list because islands can cause upstream merging, duplicate COMIDs that persist and compound with the total number of islands all the way to headwaters (FROMMCOMID=0)
        current=current[np.isin(current,watershed,invert=True)]#third way to remove duplicates...if an island has unequal number of reaches on either side the unique comparison will be offset. So, check if the offending COMID(s) already exist in watershed
        current=current[np.isin(current,chandims[:,0])]#get rid of "coastline" features that somehow infiltrated the list
        if slope: #remove flow lines with slopes exceeding threshold
            curslp=chandims[np.isin(chandims[:,0],current),2]
            current=current[curslp<=slope]
        if width:
            #pdb.set_trace()
            curwd=chandims[np.isin(chandims[:,0],current),3]
            current=current[curwd>=width]
        #print '    there are %i upstream reaches' % watershed.size #this could become a very big number
        up=[] #reset upstream population
    f.write('%s,%s,%s,%s\n' % (IDs[i], type[i], features[i], hab))
    np.savetxt(savedir + 'dam_%i_wfll.csv' % int(features[i]), watershed,fmt='%i', delimiter=',')
    #np.savetxt(savedir + 'dam_6290171_wfll.csv', watershed,fmt='%i', delimiter=',')
f.close()
