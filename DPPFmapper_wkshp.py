#PPF_Mapper01.py
#Generate PNG maps from input scenarios, called from ScenarioDamSelector.py

#Written by Sam Roy


import arcpy
import numpy
import sys
import h5py

#input args
wshd=sys.argv[1] #watershed name
OV1=sys.argv[2] #objective variable 1 (or MO for multiobjective)
OV2=sys.argv[3] #objective variable 2 (or # of variables)
InName=sys.argv[4] #scenario number, or numbers

#open the scenarios file
f = h5py.File(InName,'r')
scenarios = numpy.array(list(map(int,rec) for rec in f['/' + wshd + '/x'])) #the /s makes sure you take from the scenarios list
fish = numpy.array(list(map(int,rec) for rec in f['/' + wshd + '/fish']))

#load workspace and features to add to new map
mxd = arcpy.mapping.MapDocument(r"D:\FoD\workspace\MCDA_Penobscot_template3-2019.mxd") #call the template workspace file that has all the basic background stuff and template dam wshd/point styles
#mxd = arcpy.mapping.MapDocument(r"D:\FoD\workspace\PPF_MCDA_template.mxd") #call the template workspace file that has all the basic background stuff and template dam wshd/point styles
df = arcpy.mapping.ListDataFrames(mxd)[0] #get he dataframe for the template workspace
##newWshd = arcpy.mapping.Layer(r"d:\FoD\data\dams\damWshds\%s\%s_%s\%s_%s_%s_%s.shp"%(wshd,OV1,OV2,wshd,OV1,OV2,iter)) #convert feature to layer, this feature is the set of dam watershed polygons from user's input
##newPts = arcpy.mapping.Layer(r"d:\FoD\data\dams\damWshds\%s\%s_%s\%s_%s_%s_%s_dampts.shp"%(wshd,OV1,OV2,wshd,OV1,OV2,iter)) #convert feature to layer, this feature is the set of dam points from user's input

DamptFile = r"D:\FoD\data\PenobWorkshops/PenobWshddams.shp"
damPoints = arcpy.MakeFeatureLayer_management(DamptFile)
damlyr=arcpy.mapping.ListLayers(mxd,"PenobWshddams")

WshdFile = r"D:\FoD\data\PenobWorkshops/PenobWkshpWshds.shp"
damwshds = arcpy.MakeFeatureLayer_management(WshdFile)
wshdlyr=arcpy.mapping.ListLayers(mxd,"PenobWkshpWshds")

for i in xrange(len(scenarios[1])):
    iter=i
    print(iter)
    #change decisionAl field to match values from scenario i

    Cols = ['DecisionAl']
    cur=arcpy.da.UpdateCursor(damPoints,Cols)
    counter=0
    for row in cur:
        row[0] = scenarios[counter][i]
        cur.updateRow(row)
        counter+=1
        if counter>2:
            break

    arcpy.RefreshActiveView()

    #change fish field to match values from scenario i

    Cols = ['fish']
    cur=arcpy.da.UpdateCursor(damwshds,Cols)
    counter=2
    for row in cur:
        row[0] = fish[counter][i]
        #import pdb
        #pdb.set_trace()
        cur.updateRow(row)
        counter-=1
        if counter<0:
            break

    arcpy.RefreshActiveView()

    #Export map to PNG file
    usernum=iter
    #if not len(sys.argv) > 6:
    arcpy.mapping.ExportToPNG(mxd,r"D:\FoD\PPF\MCDA-PPF\maps\%s_%s_%s_%s.png"%(wshd,OV1,OV2,iter))
    #else:
    #    usernum=sys.argv[6]
    #    arcpy.mapping.ExportToPNG(mxd,r"D:\FoD\PPF\MCDA-PPF\maps\%s_%s_%s_%s_%s.png"%(usernum,wshd,OV1,OV2,iter))

    #overlay the smaller rose plot image onto the lower left of this one
    from PIL import Image
    mapimage=Image.open(r"D:\FoD\PPF\MCDA-PPF\maps\%s_%s_%s_%s.png"%(wshd,OV1,OV2,iter))
    roseimage=Image.open(r"D:\FoD\PPF\MCDA-PPF\RosePlots\out_%s.png"%str(iter+1))

    #roseimage=roseimage.convert("RGBA")
    #datas=roseimage.getdata()
    #newData = []
    #for item in datas:
    #    if item[0] == 255 and item[1] == 255 and item[2] == 255:
    #        newData.append((255, 255, 255, 0))
    #    else:
    #        newData.append(item)
    #roseimage.putdata(newData)

    #import pdb
    #pdb.set_trace()
    #mask=Image.new('L',roseimage.size,color=255)
    #roseimage.putalpha(mask)
    roseimage=roseimage.crop((200,0,roseimage.size[0]-200,roseimage.size[1]))
    mapbox=mapimage.getbbox()
    #rosebox=roseimage.getbbox()

    wsize = int(min(mapimage.size[0], mapimage.size[1]) * 0.38)
    wpercent = (wsize / float(roseimage.size[0]))
    hsize = int((float(roseimage.size[1]) * float(wpercent)))
    simage=roseimage.resize((wsize,hsize))
    sbox=simage.getbbox()
    box=(mapbox[1]-sbox[1],mapbox[3]-sbox[3])
    #import pdb
    #pdb.set_trace()
    mapimage.paste(simage,box)
    mapimage.save(r"D:\FoD\PPF\MCDA-PPF\combo\%s_%s_%s_%s_%s.png"%(usernum,wshd,OV1,OV2,iter))
