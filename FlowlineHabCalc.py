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

#user input args. If none given, provide default values. Zero values mean no threshold requested.
if len(sys.argv)>1:
    place=sys.argv[1]
else:
    print('No place specified. default place: New England (NE)')
    place='NE'
if len(sys.argv)>2:
    width=float(sys.argv[2])
else:
    print('no witdh threshold selected (0)')
    width=0.
if len(sys.argv)>3:
    slope=float(sys.argv[3])
else:
    print('no witdh threshold selected (0)')
    slope=0.
if len(sys.argv)>4:
    tidal=int(sys.argv[4])
else:
    print('no slope threshold selected (0)')
    tidal=0

#declare directories/files
basedir=r"D:/FoD/data/joe/"
savedir=basedir + r"HabitatOut/"
f_dams=basedir + r"features/damCOMIDtest%s.csv" %place #file containing dam-flowline/catchment linked COMIDs. These are actually linked to catchments, not flowlines, because of occasional offset in boundaries of both. More important to match dam to its containing catchment
f_outlets=basedir + r"features/outletCOMIDtest%s.csv" %place #file containing dam-flowline/catchment linked COMIDs. These are actually linked to catchments, not flowlines, because of occasional offset in boundaries of both. More important to match dam to its containing catchment
f_chandat=basedir + r"flowData/flowdata%s.csv" % place #additional data, including tidal flag
f_lines=basedir + r"flownets/COMIDflownet%s.csv" % place #downstream neighbor list
#import data
features1=np.loadtxt(f_dams,delimiter=',',skiprows=1,usecols=(1))
features2=np.loadtxt(f_outlets,delimiter=',',skiprows=1,usecols=(1))
features=np.concatenate((features1,features2))
IDs1=np.genfromtxt(f_dams,delimiter=',',skip_header=1,usecols=(0),dtype='str')
IDs2=np.genfromtxt(f_outlets,delimiter=',',skip_header=1,usecols=(0),dtype='str')
IDs=np.concatenate((IDs1,IDs2))
locations1=np.genfromtxt(f_dams,delimiter=',',skip_header=1,usecols=(7,3),dtype='str')
locations2=np.genfromtxt(f_outlets,delimiter=',',skip_header=1,usecols=(7,3),dtype='str')
locations=np.concatenate((locations1,locations2))
type1=np.genfromtxt(f_dams,delimiter=',',skip_header=1,usecols=(2),dtype='str')
type2=np.genfromtxt(f_outlets,delimiter=',',skip_header=1,usecols=(2),dtype='str')
type=np.concatenate((type1,type2))
#chandat=np.loadtxt(f_chandat,delimiter=',',skiprows=1,usecols=(0,1,4,5))
chandat=np.loadtxt(f_chandat,delimiter=',',skiprows=1,usecols=(0,1,3,4,2))
flow=np.loadtxt(f_lines,delimiter=',',skiprows=1,usecols=(0,1))

#optional input args: array of decision user can provide for each dam
if len(sys.argv)>5:
    f_decision = sys.argv[5]
    decision = np.genfromtxt(f_decision,delimiter=',',dtype='str')
else:
    decision = ['keep'] * type[type == 'dam'].size
    decision.extend(['outlet'] * type[type == 'outlet'].size)
    decision=np.array(decision)

#optional input args: array of passage probabilities user can provide for each dam
if len(sys.argv)>6:
    f_passage = sys.argv[6]
    passage = np.loadtxt(f_passage,delimiter=',')
else:
    passage = [0.] * type[type == 'dam'].size #assume dams have 0% passage unless stated otherwise by user
    passage.extend([1.] * type[type == 'outlet'].size) #outlets must have passage = 1 (100%)
    passage = np.array(passage)
    passage[decision=='remove'] = 1.
    passageComp = passage

#declare the arrays, other variables
habup = np.array([0.] * features.size)
habseg = np.array([0.] * features.size)

#pdb.set_trace()
#loop through dams, retieve full list of upstream flowlines/catchments saved to txt
for i in xrange(features.size):
    #if not os.path.isfile(savedir + 'dam_%i_wfll.csv' % int(dams[i])):
    print '%i of %i' % (i+1, len(features)) #show them you're working on it
    current=np.array([features[i]]) #declare the current search location as dam[i]
    currentseg=current
    #current=np.array([6290171])
    watershed=[] #declare the list of upstream COMIDs
    #import pdb
    #pdb.set_trace()
    while np.sum(current)>0: #break this while loop if there are no more upstream flowlines
        watershed=np.concatenate([watershed,current])
        up=np.array([]) #reset upstream population
        upseg=np.array([])
        #sum habitat, habitat segment
        if tidal:
            #pdb.set_trace()
            habup[i] = habup[i] + np.sum(chandat[(np.isin(chandat[:,0],current)) & (chandat[:,4]==0),1]*(chandat[(np.isin(chandat[:,0],current)) & (chandat[:,4]==0),3]/1e3))
            habseg[i] = habseg[i] + np.sum(chandat[(np.isin(chandat[:,0],currentseg)) & (chandat[:,4]==0),1]*(chandat[(np.isin(chandat[:,0],currentseg)) & (chandat[:,4]==0),3]/1e3))
        else:
            habup[i] = habup[i] + np.sum(chandat[np.isin(chandat[:,0],current),1]*(chandat[np.isin(chandat[:,0],current),3]/1e3))
            habseg[i] = habseg[i] + np.sum(chandat[np.isin(chandat[:,0],currentseg),1]*(chandat[np.isin(chandat[:,0],currentseg),3]/1e3))
        #pdb.set_trace()
        #compound passage for upstream features, if they are found in this search round
        if np.any(np.isin(features,current)):
            #if np.isin(IDs[i],IDs[np.isin(features,current,invert=True)]):
            #    pdb.set_trace()
            current_passageComp=passageComp[i]
            passageComp[(np.isin(features,current))] = passageComp[(np.isin(features,current))] * passage[i]
            #passageComp[(np.isin(features,current)) & (np.isin(IDs[np.isin(features,current,invert=True)],IDs[i]))] = passageComp[(np.isin(features,current)) & (np.isin(IDs[np.isin(features,current,invert=True)],IDs[i]))] * passage[i]
            passageComp[i]=current_passageComp
        for j in xrange(current.size): #loop through list of dams that were upstream
            #find match of current COMID in 'TO' column of flow, retrieve COMID in 'FROM' column. We are looking upstream for COMIDS.
            #print '   upstream number %i' % j
            #import pdb
            #pdb.set_trace()
            up=np.concatenate([up,flow[flow[:,1]==current[j],0]])
            if np.isin(current[j],currentseg):
                upseg=np.concatenate([upseg,flow[flow[:,1]==current[j],0]])

        current=np.unique(up[up>0]) #take the unique list because islands can cause upstream merging, duplicate COMIDs that persist and compound with the total number of islands all the way to headwaters (FROMMCOMID=0)
        upseg=upseg[np.isin(upseg,features,invert=True)] #for the feature's segment, remove flowlines that intersect upstream dams
        currentseg=np.unique(upseg[upseg>0])
        current=current[np.isin(current,watershed,invert=True)]#third way to remove duplicates...if an island has unequal number of reaches on either side the unique comparison will be offset. So, check if the offending COMID(s) already exist in watershed
        currentseg=currentseg[np.isin(currentseg,watershed,invert=True)]
        current=current[np.isin(current,chandat[:,0])]#get rid of "coastline" features that somehow infiltrated the list
        currentseg=currentseg[np.isin(currentseg,chandat[:,0])]

        if slope: #remove flow lines with slopes exceeding threshold
            curslp=chandat[np.isin(chandat[:,0],current),2]
            current=current[curslp<=slope]
            curslpseg=chandat[np.isin(chandat[:,0],currentseg),2]
            currentseg=currentseg[curslpseg<=slope]
        if width:
            #pdb.set_trace()
            curwd=chandat[np.isin(chandat[:,0],current),3]
            current=current[curwd>=width]
            curwdseg=chandat[np.isin(chandat[:,0],currentseg),3]
            currentseg=currentseg[curwdseg>=width]
        #print '    there are %i upstream reaches' % watershed.size #this could become a very big number
    #np.savetxt(savedir + 'dam_%i_wfll.csv' % int(features[i]), watershed,fmt='%i', delimiter=',')
    #np.savetxt(savedir + 'dam_6290171_wfll.csv', watershed,fmt='%i', delimiter=',')

#Next, write results to a file on disk. Print them in descending order based on functional habitat amounts.
idx=np.argsort(habseg*passageComp)[::-1]

#write-out file
f = open(savedir + r"Habitat%s_wd%sm_slp%s_tidal%i.csv" % (place, width, slope, tidal), "w")
f.write('%.2f,Total functional habitat\n' % np.sum(habseg*passageComp))
f.write('%.2f,Maximum habitat\n' % np.sum(habseg))
f.write('%.2f,Channel width threshold\n' % width)
f.write('%s,Slope threshold\n' % slope)
f.write('%i,Omit tidal reaches\n' % tidal)
f.write('UNIQUE_ID,type,catchmentID,habitat_sqkm,habitatSegment_sqkm,functional_habitatSegment_sqkm,PassageToHabitat,Decision,HUC6_location,HUC10_location\n')
for i in idx:
    f.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (IDs[i], type[i], features[i], habup[i], habseg[i], habseg[i]*passageComp[i], passageComp[i], decision[i],locations[i,0],locations[i,1]))
f.close()
