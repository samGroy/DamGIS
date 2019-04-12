#CulvertDimensions
#Script to organize dimension and material data for culverts, then save to text file that can be joined to the culvert shapefile

import csv
import sys

dr=sys.argv[1]
fn=sys.argv[2]
out=sys.argv[3]
#r'd:/FoD/data/culverts/CulvsDims.csv'
reader=csv.reader(open(dr+fn,'rb'),delimiter=',')
d=list(reader)

with open(dr+out, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        #writer.writerow(['OBJECTID','CulvertNbr','shape','material','length','drop','area','width','height','c_coeff','Y_coeff','Q_fail'])
        writer.writerow(['OBJECTID','CulvertNbr','shape','material','length','drop','blocked','area','width','height','coverHeight','c_coeff','Y_coeff','Q_fail'])

        #loop to find largest ID value
        #IDmax=0
        AvgWidth=3.#0.
        AvgLength=28.
        pavement=0.5
        AvgCover=0.5
        #wct=0
        #for i in xrange(1, len(d)):
        #    if len(str(d[i][0]))>IDmax:
        #        IDmax=len(str(d[i][0]))
        #    if not d[i][7]==0 and str(d[i][7]).isdigit():
        #        AvgWidth+=float(d[i][7])
        #        wct+=1
        #    if not d[i][10]==0 and str(d[i][10]).isdigit():
        #        AvgWidth+=float(d[i][10])
        #        wct+=1

        #AvgWidth=AvgWidth/wct
        #print 'Average Width = %s'%AvgWidth

        #Main Work loop
        for i in xrange(1, len(d)):
            print 'Site %s'%i
            #ct=''.join(c for c in d[i][3] if c.isdigit())
            try:
                ct=int(d[i][5])
                if ct<1:
                    ct=1
                elif ct>7:
                    ct=7 #TNC goes up to 7 parallel culvert measurements
            except:
                ct=1 #There's at least one crossing

            #if i==3:
            #    import pdb; pdb.set_trace()
            for j in xrange(ct):
                print '  Culvert %s'%j
                ID=d[i][0] #The OBJECTID, a combination of TNC and MEDOT IDs, where TNC culverts spatially match with MEDOTs, TNC ID used, MEDOT ID placed in second column
                shape=d[i][2] #round, arch, box,...
                material=d[i][3] #metal, concrete, plastic, wood, etc
                try:
                    length=float(d[i][6])*0.3048 #*0.3048 to convert feet to meters
                    if length<=0:
                        length=AvgLength*0.3048
                except:
                    length=AvgLength*0.3048
                try:
                    drop=float(d[i][8])*0.3048
                except:
                    drop=0

                #width calculation
                w=0
                a=0
                try:
                    w+=float(d[i][10+(j)*6])
                    a+=1
                except:
                    w+=0
                try:
                    w+= float(d[i][13+(j)*6])
                    a+=1
                except:
                    w+=0
                if w>0:
                    width=w/a*0.3048
                else:
                    width=AvgWidth*0.3048


                #Height calculation: sum of water height and clearance. For MEDOT culverts w/o TNC matches, I just have/use the basic dimensions.
                if shape == 'Round Culvert':
                    height=width
                else:
                    h=0
                    a=0
                    try:
                        h+= float(d[i][9+(j)*6])+float(d[i][11+(j)*6])
                        a+=1
                    except:
                        h+=0
                    try:
                        h+= float(d[i][12+(j)*6])+float(d[i][14+(j)*6])
                        a+=1
                    except:
                        h+=0
                    if h>0:
                        height=h/a*0.3048
                    else:
                        height=AvgWidth*0.3048


                #area calculation
                if 'round' in shape.lower() or ('pipe' in shape.lower() and not 'arch' in shape.lower()) or 'no data' in shape.lower():
                    area=pow(width/2,2)*3.14
                    shape = 'round'
                elif 'arch' in shape.lower():
                    area=width/2*height/2*3.14
                    shape = 'arch'
                elif 'box' in shape.lower() or 'bridge' in shape.lower():
                    area=width*height
                    shape = 'box'
                else:
                    area=pow(width/2,2)*3.14
                    shape = 'round_est'

                #Simplify material property descriptions
                if 'metal' in material.lower() or 'steel' in material.lower() or 'aluminum' in material.lower() or 'iron' in material.lower():
                    material = 'metal'
                elif 'concrete' in material.lower() or 'stone' in material.lower() or 'rock' in material.lower():
                    material = 'concrete/stone'
                elif 'wood' in material.lower():
                    material = 'wood'
                elif 'plastic' in material.lower():
                    material = 'plastic'
                else:
                    material = 'other'

                #c and Y from materials and opening type
                #assumptions:
                #metal/plastic culverts are always projecting
                #concrete culverts are always headwalled
                #box culverts are always headwalled
                if shape == 'round' or shape == 'round_est':
                    if material == 'metal' or material == 'plastic':
                        c=0.032
                        Y=0.69
                    else: #must be concrete/stone
                        c=0.029
                        Y=0.74
                elif shape == 'arch':
                    if material == 'metal' or material == 'plastic':
                        c=0.06
                        Y=0.75
                    else: #must be concrete
                        c=0.048
                        Y=0.8
                elif shape == 'box':
                    if material == 'concrete/stone' or material == 'wood':
                        c=0.038
                        Y=0.87
                    else:
                        c=0.038
                        Y=0.69
                else:
                    c=0.3
                    Y=0.7

                #max_head is water height from base of culvert to top of pavement
                #requires cover depth as well as pavement thickness (unknown) and culvert Height
                try:
                    cover=float(d[i][7])
                except:
                    cover=AvgCover
                max_head = height+(cover+pavement)*0.3048

                #Submerged inlet control discharge
                #This equation determines the maximum Q in cubic meters per second a culvert can take before overtopping/failure
                #percentage of culvert cross-sectional area blocked by debris
                blocked=float(d[i][51])
                try:
                    #Q=area*pow((width+height)/2,0.5)*pow((max_head/((width+height)/2)-Y+0.5)/c,0.5)
                    Q=area*pow((width+height)/2,0.5)*pow((max_head/((width+height)/2)-Y+0.5)/c,0.5)*(1-blocked)
                    Q=Q*35.3147 #convert cubic meters to cubic feet, for comparison to NHD data
                except:
                    Q=0.
                #write to file
                #writer.writerow([ID,j,shape,material,length,drop,area,width,height,c,Y,Q])
                writer.writerow([ID,j,shape,material,length,drop,blocked,area,width,height,cover,c,Y,Q])
