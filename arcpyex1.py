import arcpy, json, fileinput, shutil, os

# main funtion
def execute(workspace):
    land = arcpy.GetParameterAsText(0)
    river = arcpy.GetParameterAsText(1)
    dis = arcpy.GetParameterAsText(2)
    outputmjh = workspace + "\outputmjh.shp"
    arcpy.AggregatePolygons_cartography(river, outputmjh, dis)
    output = workspace + "\point.shp"
    arcpy.FeatureVerticesToPoints_management(outputmjh, output)
    arcpy.AddXY_management(output)
    outputjson = workspace + "\mypjsonfeatures.json"
    arcpy.FeaturesToJSON_conversion(output, outputjson, "FORMATTED")
    extractRiver(outputjson)
    DownDirectionpath = workspace + '\DownDirection.txt'
    createPolyline(DownDirectionpath,"down.shp")
    UpDirectionpath = workspace + '\UpDirection.txt'
    createPolyline(UpDirectionpath,"up.shp")
    nearAnalyst(land,workspace)

# ouput two different point textfiles of up and down direction river
def extractRiver(filepath):
    f = file(filepath)
    s = json.load(f)
    newarr = s['features']
    xmin = newarr[0]['geometry']['x']
    ymin = newarr[0]['geometry']['y']
    xmax = newarr[0]['geometry']['x']
    ymax = newarr[0]['geometry']['y']
    idmax = -1
    for val in newarr:
        if val['geometry']['x'] < xmin:
            xmin = val['geometry']['x']
            xminID = val['attributes']['FID']
        if val['geometry']['y'] < ymin:
            ymin = val['geometry']['y']
            yminID = val['attributes']['FID']
        if val['geometry']['x'] > xmax:
            xmax = val['geometry']['x']
            xmaxID = val['attributes']['FID']
        if val['geometry']['y'] > ymax:
            ymax = val['geometry']['y']
            ymaxID = val['attributes']['FID']
        idmax = idmax + 1
    f2 = open(workspace + '\UpDirection.txt', 'w')
    i = ymaxID
    fid = 0
    while i <= xmaxID:
        f2.write(str(fid))
        f2.write(' ')
        f2.write(str(newarr[i]['geometry']['x']))
        f2.write(' ')
        f2.write(str(newarr[i]['geometry']['y']))
        f2.write('\n')
        i = i + 1
        fid = fid + 1
    f2.close()
    f3 = open(workspace + '\DownDirection.txt', 'w')
    i = xminID
    fid = 0
    while i >= 0:
        f3.write(str(fid))
        f3.write(' ')
        f3.write(str(newarr[i]['geometry']['x']))
        f3.write(' ')
        f3.write(str(newarr[i]['geometry']['y']))
        f3.write('\n')
        i = i - 1
        fid = fid + 1
    i = idmax
    while i >= yminID:
        f3.write(str(fid))
        f3.write(' ')
        f3.write(str(newarr[i]['geometry']['x']))
        f3.write(' ')
        f3.write(str(newarr[i]['geometry']['y']))
        f3.write('\n')
        i = i - 1
        fid = fid + 1
    f3.close()
    f.close()

# create polyline based on the point textfiles
def createPolyline(path,output):
    infile = path
    fc = output
    arcpy.CreateFeatureclass_management(workspace, fc, "Polyline")
    cursor = arcpy.da.InsertCursor(workspace + '\\' + fc, ["SHAPE@"])
    array = arcpy.Array()
    point = arcpy.Point()
    for line in fileinput.input(infile):
        point.ID, point.X, point.Y = line.split()
        array.add(point)
    polyline = arcpy.Polyline(array)
    cursor.insertRow([polyline])
    fileinput.close()
    del cursor

# compute the distance between buildings and river through near analyst
def nearAnalyst(land,workspace):
    arcpy.Near_analysis(land, workspace + "\up.shp")
    cursor = arcpy.da.SearchCursor(land, ['FID','NEAR_DIST'],'"NEAR_DIST" <= 50')
    array = []
    for row in cursor:
        array.append({'id': row[0]})
    arcpy.Near_analysis(land, workspace + "\down.shp")
    cursor = arcpy.da.SearchCursor(land, ['FID', 'NEAR_DIST'])
    for row2 in cursor:
        for i in array:
            if row2[0] == i['id']:
                i['distance'] = row2[1]
    cursor = arcpy.da.SearchCursor(land, ['FID','NEAR_DIST'],'"NEAR_DIST" <= 50')
    for row in cursor:
        array.append({'id': row[0]})
    arcpy.Near_analysis(land, workspace + "\up.shp")
    cursor = arcpy.da.SearchCursor(land, ['FID','NEAR_DIST'])
    for row3 in cursor:
        for i in array:
            if row3[0] == i['id']:
                i['distance'] = row3[1]
    fieldname = arcpy.ValidateFieldName("distance")
    arcpy.AddField_management(land, fieldname, "DOUBLE")
    with arcpy.da.UpdateCursor(land, ['FID', 'distance']) as cursor:
        for row in cursor:
            for i in array:
                if row[0] == i['id']:
                    row[1] = i['distance']
                    cursor.updateRow(row)
    arcpy.DeleteField_management(land, 'NEAR_DIST')
    arcpy.DeleteField_management(land, 'NEAR_FID')
    del cursor

if __name__ == '__main__':
    # make temporary file
    os.mkdir('C:\TestExample1')
    workspace = "C:\TestExample1"
    execute(workspace)
    # delete the temporary file
    shutil.rmtree(workspace)