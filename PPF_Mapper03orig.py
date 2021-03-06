#PPF_Mapper01.py
#Generate PNG maps from input scenarios, called from ScenarioDamSelector.py

#Written by Sam Roy


import arcpy

#input args
wshd=sys.argv[1] #watershed name
OV1=sys.argv[2] #objective variable 1 (or MO for multiobjective)
OV2=sys.argv[3] #objective variable 2 (or # of variables)
iter=sys.argv[4] #scenario number, or numbers

#load workspace and features to add to new map
mxd = arcpy.mapping.MapDocument(r"D:\FoD\workspace\PPF_MCDA_Penobscot_template.mxd") #call the template workspace file that has all the basic background stuff and template dam wshd/point styles
#mxd = arcpy.mapping.MapDocument(r"D:\FoD\workspace\PPF_MCDA_template.mxd") #call the template workspace file that has all the basic background stuff and template dam wshd/point styles
df = arcpy.mapping.ListDataFrames(mxd)[0] #get he dataframe for the template workspace
newWshd = arcpy.mapping.Layer(r"d:\FoD\data\dams\damWshds\%s\%s_%s\%s_%s_%s_%s.shp"%(wshd,OV1,OV2,wshd,OV1,OV2,iter)) #convert feature to layer, this feature is the set of dam watershed polygons from user's input
newPts = arcpy.mapping.Layer(r"d:\FoD\data\dams\damWshds\%s\%s_%s\%s_%s_%s_%s_dampts.shp"%(wshd,OV1,OV2,wshd,OV1,OV2,iter)) #convert feature to layer, this feature is the set of dam points from user's input

#add the new layer(s) to the data frame, change new layer style to match the template style, hide the template layer, and move the new one to the template's place
arcpy.mapping.AddLayer(df,newWshd,"TOP")
arcpy.ApplySymbologyFromLayer_management(arcpy.mapping.ListLayers(mxd,"",df)[0], arcpy.mapping.ListLayers(mxd,"",df)[4]) #This works because we know the order of layers remains constant, and the new layer is set to be at the top
arcpy.mapping.ListLayers(mxd,"",df)[4].visible = False
arcpy.mapping.MoveLayer(df,arcpy.mapping.ListLayers(mxd,"",df)[4],arcpy.mapping.ListLayers(mxd,"",df)[0],"BEFORE")

#for dam points, add them to top too, though you don't need to move them, just hide the template points
arcpy.mapping.AddLayer(df,newPts,"TOP")
arcpy.ApplySymbologyFromLayer_management(arcpy.mapping.ListLayers(mxd,"",df)[0], arcpy.mapping.ListLayers(mxd,"",df)[1]) #This works because we know the order of layers remains constant, and the new layer is set to be at the top
arcpy.mapping.ListLayers(mxd,"",df)[1].visible = False
arcpy.mapping.ListLayers(mxd,"",df)[0].showClassLabels = True
arcpy.mapping.ListLayers(mxd,"",df)[0].showLabels = True

#Export map to PNG file
if not len(sys.argv) > 5:
    arcpy.mapping.ExportToPNG(mxd,r"d:\FoD\images\PPFmaps\%s_%s_%s_%s.png"%(wshd,OV1,OV2,iter))
else:
    usernum=sys.argv[5]
    arcpy.mapping.ExportToPNG(mxd,r"d:\FoD\images\PPFmaps\%s_%s_%s_%s_%s.png"%(usernum,wshd,OV1,OV2,iter))

#overlay the smaller rose plot image onto the lower left of this one
from PIL import Image
mapimage=Image.open(r"d:\FoD\images\PPFmaps\%s_%s_%s_%s_%s.png"%(usernum,wshd,OV1,OV2,iter))
roseimage=Image.open(r"d:\FoD\images\PPFmaps\roses\%s.png"%usernum)

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

wsize = int(min(mapimage.size[0], mapimage.size[1]) * 0.4)
wpercent = (wsize / float(roseimage.size[0]))
hsize = int((float(roseimage.size[1]) * float(wpercent)))
simage=roseimage.resize((wsize,hsize))
sbox=simage.getbbox()
box=(mapbox[1]-sbox[1],mapbox[3]-sbox[3])
#import pdb
#pdb.set_trace()
mapimage.paste(simage,box)
mapimage.save(r"d:\FoD\images\MCDAworkshop\%s_%s_%s_%s_%s.png"%(usernum,wshd,OV1,OV2,iter))
