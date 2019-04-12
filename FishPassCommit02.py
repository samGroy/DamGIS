#FishPassCommit.py
#commits fish passage probability to a barrier dbf using data from the dbf and input from user
import os
import sys
import csv
import arcpy
import numpy
import scipy
from scipy import integrate

#user input arg

species=sys.argv[1] #species passed by user
#dr=sys.argv[1] #directory where culvert data are located
#fn=sys.argv[2] #filename of culvert data
#out=sys.argv[3] #output filename

#handle the dbf related to barrier shpfile
db=r'D:/FoD/data/culverts/Culvsnap_TNC-MEDOT_7-16-18.shp'
#db2=r'D:/FoD/data/culverts/Vc_spr_mn_sum.csv'
#find the right params and field
if species.lower() in 'american shad, atlantic salmon, brook trout':
    if species.lower() in 'atlantic salmon':
        fld='SalmoP'
        l=735
    elif species.lower() in 'brook trout':
        fld='BktP'
        l=300 #"Trout and Salmon of North America" book, Behnke
    else:
        fld='ShadP'
        l=417.25
    intercept=5.706
    vbeta=-0.983
    Tbeta=-0.029
    lbeta=0.0022
    scale=0.316
    sh=2.070
    dist='gamma'

elif species.lower() in 'alewife':
    fld='AleP'
    intercept=4.571
    vbeta=-0.920
    Tbeta=-0
    lbeta=0
    l=236
    scale=0.513
    sh=2.431
    dist='gamma'

elif species.lower() in 'blueback herring':
    fld='BbkP'
    intercept=-0.435
    vbeta=-1.165
    Tbeta=0.079
    lbeta=0.0196
    l=220
    scale=0.665
    sh=0
    dist='weibull'
T=16.

#find the other important fields
Lfld='rvrLgth_m' #length in meters
Dfld='Drop' #drop in meters
vfld='Vc_spr_mn' #flow velocity in ft/sec
bar='BarrierCla' #barrier/nonbarrier
BID='BID' #barrier ID number
blk='Blocked_1' #fraction of blockage
#outc='OutletCond'
fields=[BID,bar,Lfld,Dfld,vfld,fld,blk]
#loop through db

with arcpy.da.UpdateCursor(db,fields) as cursor:
    for row in cursor:
#for i in xrange(1,len(db)):
    #rec=db[i]
        print 'Barrier %i'%row[0]
        #binary conditions:
        #if defined as no barrier, passage is 1
        if row[1]=='No Barrier' or row[1]=='No Crossing':
            row[5]=1.
            cursor.updateRow(row)
            #db.pack()
            #del db[i]
            continue
        #if there's a free fall, fish unlikely to pass through, passage is 0
        #this works for now, eventually gauge passability for different species with jumping capabilities
        if float(row[3])>0:
            row[5]=0
            #import pdb; pdb.set_trace()
            cursor.updateRow(row)
            continue

        #Everything else, there may be some probability of passage
        if row[2]<=0:
            D=8.5344 #average length of barrier culverts, meters
        else:
            D=row[2]#now already in meters/3.28 #convert to meters from feet

        v=row[4]/3.28 #feet to meters

        #FishPassProb.py calcs
        mu=(v*vbeta)+(l*lbeta)+(T*Tbeta)+intercept
        zed=(numpy.log(D)-mu)/scale

        if dist is 'gamma':
            f=lambda x: x**(sh**-2-1)*numpy.exp(-x)
            b=sh**-2*numpy.exp(sh*zed)
            S=scipy.integrate.quad(f,b,numpy.inf)[0]/scipy.integrate.quad(f,0,numpy.inf)[0]
        elif dist is 'weibull':
            S=numpy.exp(-numpy.exp(zed))
        if S>1:
            S=1.


        #is culvert blocked, how much?
        if float(row[6])>0:
            #import pdb; pdb.set_trace()
            blocked=1-float(row[6])/100
            #import pdb; pdb.set_trace()
            S=S*blocked

        #remember, what goes up will try to come down
        S=pow(s,2)
        row[5]=S
        cursor.updateRow(row)
        #db.pack()
        #del db[i]
