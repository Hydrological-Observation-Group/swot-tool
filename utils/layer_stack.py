## author: xin luo 
## creat: 2022.3.16; modify: 2025.7.25
## des: layer stacking for remote sensing images

import rasterio
import numpy as np
from osgeo import gdal
from rasterio.warp import Resampling

def layer_stack(
    band_paths: list,
    output_path: str,
    extent_mode: str = 'intersection',
    resolution: tuple = None,
    resampling: Resampling = Resampling.nearest,
    output_dtype = None,
    output_nodata = None,
) -> str:
    """
    (based on rasterio, faster than gdal-based script)
    des: Band stacking tool (no reprojection, no reference band parameter)
    Paras:
        band_paths: List of band file paths (in band order)
        output_path: Output file path
        extent_mode: Extent mode
            'union' - Output maximum extent of all bands
            'intersection' - Output common extent of all bands (default)
        resolution: Target resolution (x_res, y_res). Uses first band's resolution if not specified
        resampling: Resampling method (default: nearest, options: nearest, bilinear, cubic, etc.)    
        dtypes: Output data type (default: first band type, options: np.int32, np.float32, np.float64 etc.)
        output_nodata: Output nodata value (default: 0)
    Returns:
        Path to output file
    """
    # 1. Read metadata for all bands
    band_info = []
    for path in band_paths:
        with rasterio.open(path) as src:
            # Extract metadata and calculate resolution
            x_res = abs(src.transform.a)
            y_res = abs(src.transform.e)
            band_info.append({
                'transform': src.transform,
                'dtype': src.dtypes[0],
                'nodata': src.nodata,
                'bounds': src.bounds,
                'width': src.width,
                'height': src.height,
                'crs': src.crs,
                'x_res': x_res,
                'y_res': y_res
            })
    
    # 2. Automatically determine output parameters
    # 2.1 Data type: Use first band or find most compatible type
    if output_dtype is None:
        output_dtype = band_info[0]['dtype']

    # 2.2 Nodata value: Find first valid nodata value
    if output_nodata is None:
        output_nodata = band_info[0]['nodata']
        if output_nodata is None:
            output_nodata = 0

    # 2.3 Resolution: Use parameter or first band's resolution
    if resolution is None:
        resolution = (band_info[0]['x_res'], band_info[0]['y_res'])
    
    # 3. Calculate target extent based on mode
    if extent_mode == 'union':
        left = min(info['bounds'].left for info in band_info)
        bottom = min(info['bounds'].bottom for info in band_info)
        right = max(info['bounds'].right for info in band_info)
        top = max(info['bounds'].top for info in band_info)
    elif extent_mode == 'intersection':
        left = max(info['bounds'].left for info in band_info)
        bottom = max(info['bounds'].bottom for info in band_info)
        right = min(info['bounds'].right for info in band_info)
        top = min(info['bounds'].top for info in band_info)
        
        # Validate intersection exists
        if left >= right or bottom >= top:
            raise ValueError("No valid band intersection available. Use 'union' mode instead")
    else:
        raise ValueError(f"Invalid extent mode: {extent_mode}. Use 'union' or 'intersection'")
    
    # 4. Calculate target dimensions and transform matrix
    width = int(round((right - left) / resolution[0]))
    height = int(round((top - bottom) / resolution[1]))
    
    transform = rasterio.Affine(
        resolution[0], 0, left,
        0, -resolution[1], top
    )
    
    # 5. Create output file profile
    out_profile = {
        'driver': 'GTiff',
        'height': height,
        'width': width,
        'count': len(band_paths),
        'dtype': output_dtype,
        'transform': transform,
        'nodata': output_nodata,
        'crs': band_info[0]['crs'],  # Use first band's CRS
    }

    # 6. Process and write each band
    with rasterio.open(output_path, 'w', **out_profile) as dst:
        for band_idx, (info, src_path) in enumerate(zip(band_info, band_paths), start=1):
            with rasterio.open(src_path) as src:
                # Initialize output array with nodata values
                band_data = np.full((height, width), output_nodata, dtype=output_dtype)                
                # Perform resampling (no coordinate transformation)
                rasterio.warp.reproject(
                    source=rasterio.band(src, 1),
                    destination=band_data,
                    src_transform=src.transform,
                    dst_transform=transform,
                    src_nodata=src.nodata,
                    dst_nodata=output_nodata,
                    resampling=resampling,
                    dst_crs=src.crs,  # Same CRS for source and destination
                    src_crs=src.crs   # Prevents coordinate transformation
                ) 
                # Write processed band to output
                dst.write(band_data, band_idx)
    return output_path

# def layer_stack(path_imgs, path_out, union=True, res=None):
#     '''
#     (based on gdal)
#     des: layer stacking of the multiple bands of image.
#     input:
#         path_imgs: list, contains the paths of bands/imgs to be stacked
#         path_out: str, the output path of the layer stacked image
#         union: bool, if true, the output extent is the extents union of input images. 
#                 otherwise, the output extent is the extents intersection of input images.
#         res: resolution of the layer stacked image.
#     return:
#         imgs_stacked: np.array(), the stacked image.
#     '''

#     ## basic information of the stacked image 
#     left_min, right_min, bottom_min, up_min = float("inf"), float("inf"), float("inf"), float("inf")
#     left_max, right_max, bottom_max, up_max = -float("inf"), -float("inf"), -float("inf"), -float("inf")
#     for i, path_img in enumerate(path_imgs):
#         img = gdal.Open(path_img, gdal.GA_ReadOnly)
#         if i == 0:
#             base_proj = img.GetProjection() ## the projection of the stacked image is same to the the first image.
#             base_geotrans = img.GetGeoTransform()
#         im_geotrans = img.GetGeoTransform()
#         im_x = img.RasterXSize  # 
#         im_y = img.RasterYSize  # 
#         left = im_geotrans[0]
#         up = im_geotrans[3]
#         right = left + im_geotrans[1] * im_x + im_geotrans[2] * im_y
#         bottom = up + im_geotrans[5] * im_y + im_geotrans[4] * im_x
#         if left_min > left: left_min = left; 
#         if right_min > right: right_min = right
#         if up_min > up: up_min = up
#         if bottom_min > bottom: bottom_min = bottom
#         if left_max < left: left_max = left
#         if right_max < right: right_max = right
#         if up_max < up: up_max = up
#         if bottom_max < bottom: bottom_max = bottom
#     if union == True:
#         extent = [left_min, right_max, up_max, bottom_min]
#     else:
#         extent = [left_max, right_min, up_min, bottom_max]

#     if res is not None:
#         dx, dy = res, -res
#     else:
#         dx, dy = base_geotrans[1], base_geotrans[5]
#     ## update the basis information of the stacked image.
#     base_width = int(np.round((extent[1] - extent[0]) / float(dx)))  ## new col, integer
#     base_height = int(np.round((extent[3] - extent[2]) / float(dy)))  ## new row, integer
#     base_dx = (extent[1] - extent[0]) / float(base_width)   ## update dx and dy, may be a little bias with the original dx and dy.  
#     base_dy = (extent[3] - extent[2]) / float(base_height)
#     base_geotrans = (extent[0], base_dx, 0.0, extent[2], 0.0, base_dy)

#     ### One image by one image for layer stacking 
#     ### stacked image initialization.
#     base_n = 0      ### number of bands of the stacked image.
#     for path_img in path_imgs:
#         ## image to be layer stacked
#         stack_img = gdal.Open(path_img)
#         stack_Proj = stack_img.GetProjection()
#         stack_n = stack_img.RasterCount
#         ## align stack image to the base image
#         driver = gdal.GetDriverByName('GTiff')
#         stack_img_align = driver.Create(path_out, base_width, base_height, stack_n, gdal.GDT_Float32)
#         stack_img_align.SetGeoTransform(base_geotrans)
#         stack_img_align.SetProjection(base_proj)
#         gdal.ReprojectImage(stack_img, stack_img_align, stack_Proj, base_proj, gdal.GRA_Bilinear)
#         ## Layer stacking (update the stacked image )
#         n_bands = base_n+stack_n   ## Update the number of bands of the base image
#         imgs_stacked = driver.Create(path_out, base_width, base_height, n_bands, gdal.GDT_Float32) ## update the output stacked image
#         if(imgs_stacked != None):
#             imgs_stacked.SetGeoTransform(base_geotrans)     # 
#             imgs_stacked.SetProjection(base_proj)           #         
#         ### update the bands of the base image.
#         for i_band in range(base_n):
#             imgs_stacked.GetRasterBand(i_band+1).WriteArray(base_img.GetRasterBand(i_band+1).ReadAsArray())
#         ### write the stack image and obtained the new stacked image (base image + stack image).
#         for i_band in range(stack_n):
#             imgs_stacked.GetRasterBand(base_n+i_band+1).WriteArray(stack_img_align.GetRasterBand(i_band+1).ReadAsArray())
#         ## Update base image, i.e., the new stacked image.
#         base_n = n_bands
#         base_img = imgs_stacked
#     print('Images layer stacking done.')
#     del base_img, stack_img 
#     return imgs_stacked.ReadAsArray().transpose((1,2,0))