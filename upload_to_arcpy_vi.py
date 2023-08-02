import glob
import calendar
import os

aprx = arcpy.mp.ArcGISProject("CURRENT")
file_path = r""
pattern = '*.tif'
fp_p = os.path.join(file_path, pattern)
imgs = glob.glob(fp_p)
pub_sharing = "EVERYBODY"
org_sharing = "EVERYBODY"
tiling_format = "PNG"
publish_layer = "TRUE"
min_zoom = 21
max_zoom = 15
color_ramp = "Red to Green"
output_tpkx = r""
map_obj = aprx.listMaps()[0]

for idx, img in enumerate(imgs):
    lyr_name_out = os.path.splitext(img)[0].split('\\')[-1]
    vi_name = lyr_name_out.split('_')
    
    ras_lyr = arcpy.MakeRasterLayer_management(img, lyr_name_out)
    map_obj.addLayer(ras_lyr.getOutput(0))
    month_num = vi_name[0][2:4]
    month_name = calendar.month_name[int(month_num)]
    day = vi_name[0][4:]
    
    lyr_remove = map_obj.listLayers()[1]
    map_obj.removeLayer(lyr_remove)
    
    lyr_obj = map_obj.listLayers()[0]
    sym = lyr_obj.symbology
    sym.colorizer.colorRamp = aprx.listColorRamps(color_ramp)[0]
    lyr_obj.symbology = sym
    
    arcpy.management.CreateMapTilePackage("Map0", "ONLINE", 
                                              output_tpkx + lyr_name_out + ".tpkx", 
                                              tiling_format, min_zoom, None, 
                                              f"UAV {vi_name[-1]} for {month_name} {day}, 20{vi_name[0][:2]}; Block {vi_name[1].upper()}",
                                              f"{vi_name[-1]}", "DEFAULT", 75, "tpkx", max_zoom, r"in_memory\feature_set1")
    print(f"Done Map Tile Package: {lyr_name_out}")
    
    
    arcpy.management.SharePackage(output_tpkx + lyr_name_out + ".tpkx", '', 
                                None, f"UAV {vi_name[-1]} for {month_name} {day}, 20{vi_name[0][:2]}; Block {vi_name[1].upper()}", 
                                f"{vi_name[-1]}", "CSULB, Scott Winslow, Dr. Gary Adest", pub_sharing, 
                                "'River Ridge Ranch Hub Content';'MSGISci Cohort 10'", 
                                org_sharing, publish_layer, "River Ridge Ranch Hub")
    print(f"Done Share Package: {lyr_name_out}")
    
    lyr_remove2 = map_obj.listLayers()[0]
    map_obj.removeLayer(lyr_remove2)

print('All images are done')