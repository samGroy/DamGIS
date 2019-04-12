#FishPassCommit.py
#commits fish passage probability to a barrier dbf using data from the dbf and input from user
import os
import sys
import dbf
import arcpy
import numpy
import scipy
from scipy import integrate

#user input arg

species=sys.argv[1] #species passed by user

#handle the dbf related to barrier shpfile
db=r'D:/FoD/data/culverts/PublicallySharableRoadXing3_2017/PSX_3_17_working_6_14_18.shp'
#find the right params and field
if species.lower() in 'american shad, atlantic salmon':
    if species.lower() in 'atlantic salmon':
        fld='SalmoP'
        l=735
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
Dfld='CrossingSt'
vfld='Vc_spr_mn'
bar='BarrierCla'
blk='Blocked'
outc='OutletCond'
fields=[bar,Dfld,vfld,fld,blk,outc]
#loop through db
i=0
with arcpy.da.UpdateCursor(db,fields) as cursor:
    for row in cursor:
#for i in xrange(1,len(db)):
    #rec=db[i]
        print 'Barrier %i'%i
        i+=1
        #binary conditions:
        #if defined as no barrier, passage is 1
        if row[0]=='No Barrier' or row[0]=='No Crossing':
            row[3]=1.
            cursor.updateRow(row)
            #db.pack()
            #del db[i]
            continue
        #if there's a free fall, fish unlikely to pass through, passage is 0
        if "fall" in row[5].lower():
            row[3]=0
            #import pdb; pdb.set_trace()
            cursor.updateRow(row)
            continue

        #Everything else, there may be some probability of passage
        if row[1]<=0:
            D=13.1 #average length of barrier culverts
        else:
            D=row[1]/3.28 #convert to meters from feet

        v=row[2]/3.28 #feet to meters

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
        if not 'no' in row[4].lower() and row[4] not in ' ':
            #import pdb; pdb.set_trace()
            blocked=1-float(row[4][:-1])/100
            #import pdb; pdb.set_trace()
            S=S*blocked
        row[3]=S
        cursor.updateRow(row)
        #db.pack()
        #del db[i]
