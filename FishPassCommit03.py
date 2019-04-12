#FishPassCommit.py
#commits fish passage probability to a barrier dbf using data from the dbf and input from user
import os
import sys
import csv
#import arcpy
import numpy as np
import scipy.stats as st
#from scipy import integrate

#user input arg
csvdir=sys.argv[1] #dir to csv data file
csvname=sys.argv[2] #name of csv data file

#fish metrics used below
#fish order: 1. river herring, 2. atlantic salmon, 3. american shad,
#4. brook trout, 5. american eel, 6. sea lamprey
fish_length = [0.254, 0.7366, 0.5588, 0.254, 0.055, 0.6096]
m = [12.949,12.949,12.949,12.949,10.687,10.687] #using only trout and eel group models
a=[-0.161,-0.161,-0.161,-0.161,-0.36,-0.36] #using only trout and eel group models
out=[]

#open data file and write contents to numpy array
with open(csvdir + '/' + csvname, 'rb') as infile:
    infile.readline() #skip field names in first row
    with open(csvdir + '/' + csvname + '_out.csv', 'wb') as outfile:
        csvreader = csv.reader(infile, delimiter=',')
        csvwriter = csv.writer(outfile,delimiter=',')
        csvwriter.writerow(['OBJECTID','Vc_spr_mn','RH_P','ASAL_P','ASHA_P','BKT_P','AE_P','SL_P'])
        for row in csvreader:
            Vc=float(row[6])
            out.extend([row[0],row[6]])
            #p=[0]*len(fish_length)
            for i in xrange(len(fish_length)):
                if float(row[3])>0: #height of drop, if any drop, passage is zero. Conservative.
                    p=0
                elif Vc==0:
                    p=1 #assume no flow means pond or lake. 0th order channels that go dry assume there'd be no habitat anyway.
                else:
                    Vc_fish = Vc+fish_length[i]
                    tc = float(row[2])/fish_length[i]
                    ul=m[i]*tc**a[i]
                    vgap=np.log(ul)-np.log(Vc_fish)
                    p=st.norm.cdf(vgap)*0.9 #the 0.9 accounts for the downstream passage, assuming for all culverts there's a 90% success rate
                out.extend([round(p,3)])
            csvwriter.writerow(out)
            out=[]
