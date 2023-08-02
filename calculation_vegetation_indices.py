import rasterio
import glob
import os
from rr import *

def calculate_indices(red, red_edge, nir, green, output, output_folder, meta_file):
    calculate_index(red, nir, output, output_folder, meta_file, 'ndvi')
    calculate_index(green, nir, output, output_folder, meta_file, 'gndvi')
    calculate_index(red_edge, nir, output, output_folder, meta_file, 'ndre')
    calculate_index(red, nir, output, output_folder, meta_file, 'savi', L=0.5)
    calculate_osavi(red, nir, output, output_folder, meta_file, 'osavi')

output_folder = "D://index_for_Hub"
folders = os.listdir("E://")
folders.sort()
for i in folders[:-2]:
    sub_folders = os.listdir(f"E://{i}")
    for j in sub_folders:
        imgs=[]
        imgs = glob.glob(f"E://{i}//{j}//*.tif")
        imgs.sort()
        len_arr = len(imgs)
        meta_file = rasterio.open(imgs[0]).meta.copy()
        meta_file.update({'dtype': 'float32', 'count': 1})
        output =  f"{i}_{j}_"
        if len_arr == 4:
            red = remove_bg(rasterio.open(imgs[-1]).read(1).astype('float32'), meta_file['nodata'])
            red_edge = remove_bg(rasterio.open(imgs[-2]).read(1).astype('float32'), meta_file['nodata'])
            nir = remove_bg(rasterio.open(imgs[1]).read(1).astype('float32'), meta_file['nodata'])
            green = remove_bg(rasterio.open(imgs[0]).read(1).astype('float32'), meta_file['nodata'])
        elif len_arr == 5:
            red = remove_bg(rasterio.open(imgs[-1]).read(1).astype('float32'), meta_file['nodata'])
            red_edge = remove_bg(rasterio.open(imgs[-2]).read(1).astype('float32'), meta_file['nodata'])
            nir = remove_bg(rasterio.open(imgs[2]).read(1).astype('float32'), meta_file['nodata'])
            green = remove_bg(rasterio.open(imgs[1]).read(1).astype('float32'), meta_file['nodata'])
        elif len_arr == 10:
            red = remove_bg(rasterio.open(imgs[-4]).read(1).astype('float32'), meta_file['nodata'])
            red_edge = remove_bg(rasterio.open(imgs[-2]).read(1).astype('float32'), meta_file['nodata'])
            nir = remove_bg(rasterio.open(imgs[4]).read(1).astype('float32'), meta_file['nodata'])
            green = remove_bg(rasterio.open(imgs[3]).read(1).astype('float32'), meta_file['nodata'])
        else:
            continue
        calculate_indices(red, red_edge, nir, green, output, output_folder, meta_file)
        print('Done')
msg='done'
notify_completion(msg, chat_id)

