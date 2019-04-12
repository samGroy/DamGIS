#CulvertVelocity.py
#Script to calculate flow velocity through culverts during springtime flows
#requires culvert dimensions, mean spring Q and V

import sys
import os
import csv
import math

dr=sys.argv[1] #directory where culvert data are located
fn=sys.argv[2] #filename of culvert data
out=sys.argv[3] #output filename

reader=csv.reader(open(dr+fn,'rb'),delimiter=',')
d=list(reader)

#loop through all culverts, even parallel culverts, to calculate wetted cross-sectional area
with open(dr+out, "wb") as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    writer.writerow(['OBJECTID','shape','length','drop','Wetted_AreaC','V_spr_mn','Vc_spr_mn','Qfail'])
    for i in xrange(1,len(d)):
        print ' %i  %i'%(int(d[i][0]),int(d[i][1]))
        depth=float(d[i][15])+1e-6
        height=float(d[i][9])*3.28 #convert metric to english
        width=float(d[i][8])*3.28
        totalArea=float(d[i][7])*10.7639
        Qf=float(d[i][12])
        blocked=float(d[i][6])
        if depth>=height: #if spring depth overtops culvert height
            Ac=totalArea #cross-sectional area must equal culvert cross-sectional area
        elif  'round' in d[i][2]:
            r=height
            #r=pow(float(d[i][6])/3.14,0.5) #retrieve radius from inverse circle area calc
            theta=2*math.acos(1-depth/r) #angle from origin to water lines on culvert sides
            Ac=pow(r,2)/2*(theta-math.sin(theta)) #portion of round culvert is wetted area
        elif 'box' in d[i][2]:
            Ac=depth*width #portion of rectangular/box culvert is wetted area
        elif 'arch' in d[i][2]:
            clearance=height-depth #arch culverts are half-ellipses, calculate clearance area then subtract from total arch area
            if clearance<=0: #if culvert overtopped, wetted area of culvert is total arch area
                Ac=totalArea
            else:
                r=height #perform calc as if culvert was round
                theta=2*math.acos(1-clearance/r)
                skew=(width/2)/r #Ellipse horizontal and vertical axes may be uneven
                Acl=pow(r,2)/2*(theta-math.sin(theta))*skew #multiply clearance area by the skew to get the real area
                Ac=totalArea-Acl #save the wetted area as difference of clearance area from total arch area
        if Ac<=0:
            Ac=1e-6
        if float(d[i][1])==0:
            Ac_sum=Ac
            Qf_sum=Qf
        else:
            Ac_sum+=Ac
            Qf_sum+=Qf
        if i==len(d)-1:
            wo=1
        elif int(d[i+1][1])==0:
            wo=1
        else:
            wo=0
        if wo>0:
            Ac_sum=Ac_sum*(1-(blocked-1e-6)) #debris blocks flow by reducing area
            Vc=float(d[i][13])/Ac_sum
            if float(d[i][14])>Vc:
                Vc=float(d[i][14])
            writer.writerow([d[i][0],d[i][2],d[i][4],d[i][5],Ac_sum,d[i][14],Vc,Qf_sum])
