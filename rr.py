import rasterio
import os
import requests
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.image as image
from matplotlib import pyplot as plt
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)

chat_id = ""

def calculate_vegetation(images, ndvi_ask, savi_ask, ndre_ask, chat_id):
    files = [file for file in os.listdir(images) if file.endswith('.tif')]  # List all the files in the directory
    indices = [ndre_ask, ndvi_ask, savi_ask]

    if 'y' not in indices:
        print('No indices were selected')
        return

    for file in files:  # Loop through each file in the directory
        try:
            uav_image = rasterio.open(f'{images}/' + file)
            meta = uav_image.meta
            nodata = meta['nodata']
            meta.update({'dtype': 'float32', 'count': 1})
            count = uav_image.meta['count']
            if count == 5:
                red = remove_bg(uav_image.read(3).astype('float32'), nodata) if indices[1] == 'y' else None
                red_edge = remove_bg(uav_image.read(4).astype('float32'), nodata) if indices[0] == 'y' else None
                nir = remove_bg(uav_image.read(5).astype('float32'), nodata)
            elif count == 4:
                red = remove_bg(uav_image.read(2).astype('float32'), nodata) if indices[1] == 'y' else None
                red_edge = remove_bg(uav_image.read(3).astype('float32'), nodata) if indices[0] == 'y' else None
                nir = remove_bg(uav_image.read(4).astype('float32'), nodata)
            elif count == 10:
                red = remove_bg(uav_image.read(6).astype('float32'), nodata) if indices[1] == 'y' else None
                red_edge = remove_bg(uav_image.read(8).astype('float32'), nodata) if indices[0] == 'y' else None
                nir = remove_bg(uav_image.read(10).astype('float32'), nodata) 
            else:
                print(f"Unexpected number of bands: {count}. Please manually assign bands.")
                break

            if indices[0] == 'y':
                calculate_index(red_edge, nir, file, images, meta, '_ndre')
                classify_raster(os.path.join(images, f'{os.path.splitext(file)[0]}_ndre.tif'))
                make_map(os.path.join(images, f'{os.path.splitext(file)[0]}_ndre_classified.tif'), "NDRE map", "NDRE", os.path.join(images, f'{os.path.splitext(file)[0]}_ndre.png'))
            
            if indices[1] == 'y':
                calculate_index(red, nir, file, images, meta, '_ndvi')
                classify_raster(os.path.join(images, f'{os.path.splitext(file)[0]}_ndvi.tif'))
                make_map(os.path.join(images, f'{os.path.splitext(file)[0]}_ndvi_classified.tif'), "NDVI map", "NDVI", os.path.join(images, f'{os.path.splitext(file)[0]}_ndvi.png'))

            if indices[2] == 'y':
                calculate_index(red, nir, file, images, meta, '_savi', L = 0.45)
                classify_raster(os.path.join(images, f'{os.path.splitext(file)[0]}_savi.tif'))
                make_map(os.path.join(images, f'{os.path.splitext(file)[0]}_savi_classified.tif'), "SAVI map", "SAVI", os.path.join(images, f'{os.path.splitext(file)[0]}_savi.png'))
        except:
            print(f'Error. All finished files: \n{os.listdir(images)}')
    
    notify_completion(f'Process is done. Files: \n{os.listdir(images)}', chat_id)


def preprocess(raster):
    return remove_bg(normalize_band(raster)) if raster is not None else np.nan


def normalize_band(band):
    return (band - band.min()) / (band.max() - band.min())


def write_index(filepath, index, meta):
    with rasterio.open(filepath, 'w', **meta) as index_image:
        index_image.write(index, 1)
        msg = f'{filepath} was created'
        print(msg)
        # notify_completion(msg, chat_id)

def layer_stack():
    pass


def notify_completion(message, chat_id):
    t = ""
    url = f"https://api.telegram.org/bot{t}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url).json()['result']['text']


def calculate_index(band1, band2, file, images, meta, suffix='', L=0):
    index = (band2 - band1) / (band2 + band1) if L == 0 else (band2 - band1) / (band2 + band1 + L) * (1 + L)
    index_path = os.path.join(images, f'{os.path.splitext(file)[0]}{suffix}.tif')
    write_index(index_path, index, meta)


def calculate_osavi(band1, band2, file, images, meta, suffix='', L=0.16):
    index = (band2 - band1) / (band2 + band1 + L)
    index_path = os.path.join(images, f'{os.path.splitext(file)[0]}{suffix}.tif')
    write_index(index_path, index, meta)


def remove_bg(band, nodata=0):
    band[band == nodata] = None
    return band


def classify_raster(image_path):
    cmap = plt.cm.get_cmap("RdYlGn")  # Use "RdGn" color map
    with rasterio.open(image_path) as src:
        raster = src.read(1)
        meta = src.meta.copy()
        meta.update(dtype='uint8', nodata=0)
        # profile = src.profile  # Get the raster profile
        # profile.update(count=4, dtype=np.uint8, nodata=6)

        index_class_bins = [-np.inf, 0, 0.3, 0.5, np.inf]
        index_uav_class = np.digitize(raster, index_class_bins)
        index_uav_class = np.ma.masked_where(
            np.ma.getmask(raster), index_uav_class
        )
        ndvi_nobg = np.where(index_uav_class == 5, np.nan, index_uav_class)

        with rasterio.open(f'{os.path.splitext(image_path)[0]}_classified.tif', 'w', **meta) as dst:
            dst.write(ndvi_nobg, 1)

        # with rasterio.open(f'{os.path.splitext(image_path)[0]}_classified.tif') as src2:
        #     profile = src2.profile  # Get the raster profile
        #     colorized_data = cmap(src2)  # Apply the color map to the data
        #     colorized_data = np.nan_to_num(colorized_data)  # Replace NaN values with zeros
        #     colorized_data = (colorized_data * 255).astype(np.uint8)  # Scale the data to 8-bit range
        #     # Update the profile to reflect the colorized data
        #     profile.update(count=3, dtype=np.uint8)

        #     # Write the colorized data to a new raster file
        #     with rasterio.open("D://output.tif", "w", **profile) as dst:
        #         dst.write(colorized_data)



def layer_stack(rasters, output_path):
    with rasterio.open(rasters[0]) as src:
        meta = src.meta

    meta.update(count=len(rasters))

    # Create the parent directory if it doesn't exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(output_path, 'w', **meta) as dst:
        # Iterate over the input rasters and write each layer to the stack
        for idx, raster in enumerate(rasters, start=1):
            try:
                with rasterio.open(raster) as src:
                    dst.write(src.read(1), idx)
            except Exception as e:
                print(f"Error processing raster '{raster}': {e}")
            else:
                print(f"Processed raster '{raster}'")


def call_arcpy():
    pass


# def layer_stack2(rasters, output_path):
#     if len(rasters) == 0:
#         return
#     opened_images = []
#     rasters.sort()
#     directory_path = Path(f"D://{i}//{j}//")
#     directory_path.mkdir(parents=True, exist_ok=True)
#     for image in rasters:
#         with rasterio.open(image) as dataset:
#             band = dataset.read(1).astype('float32')
#             opened_images.append(band)
#     layer_stack = np.stack(opened_images, axis=0)
#     with rasterio.open(rasters[0]) as src:
#         meta = src.meta.copy()
#     meta.update(count=layer_stack.shape[0], dtype=str(layer_stack.dtype))
#     with rasterio.open(output_path, 'w', **meta) as src:
#         src.write(layer_stack)


def make_map(img, title, label, image_path):
    img = rasterio.open(img).read(1)

    fig, ax = plt.subplots(figsize=(9,9))
    im = ax.imshow(img, cmap='RdYlGn')
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(label)
    ax.set_title(title, fontsize=32, fontweight=600, loc='center', y=1)
    line1, = ax.plot([1, 2, 3,4,5], label='label1')
    line2, = ax.plot([1, 2, 3], label='label2')
    ax.axis('off')
    plt.savefig(f'{os.path.splitext(image_path)[0]}_classified.png')


# images = input("images: ")  # Prompt user to input directory containing images
# ndvi_ask = input("Do you want to calculate NDVI? (y/n) ")
# savi_ask = input("Do you want to calculate SAVI? (y/n) ")
# ndre_ask = input("Do you want to calculate NDRE? (y/n) ")

# calculate_vegetation(images, ndvi_ask, savi_ask, ndre_ask, chat_id)
