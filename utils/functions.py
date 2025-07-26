### author: xin luo, 
### create: 2024.6.9, modified: 2025.7.21
### des: some useful functions for swot data processing.

import numpy as np
import rioxarray   # rioxarray is used for reprojection and clipping of raster data

def IQR_filter(arr):
  '''
  param: 1d or 2d np.array(), the swot height.
  retrun: numpy MaskedArray, the filtered swot height.
  '''
  Q1, Q3 = np.nanpercentile(arr, (25, 75))
  IQR = Q3 - Q1
  wse_low_thre, wse_high_thre = Q1 - 1.5*IQR, Q3 + 1.5*IQR 
  arr_masked = np.ma.masked_where(np.logical_or(arr>wse_high_thre, arr<wse_low_thre), arr)
  return arr_masked, IQR

def iter_IQR(arr, IQR_thre, iter_max):
  iter = 0
  arr_IQR, IQR = IQR_filter(arr)
  while IQR > IQR_thre and iter < iter_max:    
      iter += 1
      arr_IQR_mask = arr_IQR.mask
      arr_IQR, IQR = IQR_filter(arr_IQR.filled(np.nan))
      arr_IQR.mask = arr_IQR.mask | arr_IQR_mask
  return arr_IQR, IQR


def pixc_to_slant_raster(pixc, key='height'):
    '''
     des: convert the swot pixel data to slant range format.
    '''
    az = pixc.azimuth_index.astype(int)
    rng = pixc.range_index.astype(int)
    out_arr = np.zeros((pixc.interferogram_size_azimuth + 1, \
                        pixc.interferogram_size_range + 1)) + np.nan
    # handle complex interferogram
    if key=='interferogram':
        out_arr = out_arr.astype('complex64')
        var = pixc[key][:,0] + 1j * pixc[key][:,1]
    else:
        var = pixc[key]
    out_arr[az, rng] = var
    return out_arr

def pixc_geophy_cor(pixc_nc):
    """geophysical corrections for the height data.
       by following the swot l2 hr pixc document, only solid earth tide, 
          pole tide, and load tide are not corrected for the height.
    """
    height = pixc_nc.height.values
    solid_tide = pixc_nc.solid_earth_tide.values
    pole_tide = pixc_nc.pole_tide.values
    load_tide = pixc_nc.load_tide_fes.values

    return height - (solid_tide + pole_tide + load_tide)    

def swot_raster_reproj(raster_nc, epsg_from, epsg_to):
    '''
    des: reproject the raster dataset from one EPSG code to another.
    args:
      raster_nc (xarray): the SWOT Raster dataset.
      epsg_from (str): the EPSG code of the original dataset.
      epsg_to (str): the EPSG code to which the dataset will be reprojected.
    returns:
      raster_reproj_nc (xarray): the reprojected raster dataset.
    '''
    ## Ensure the dataset is compatible with rioxarray
    if not raster_nc.rio.crs:
        raster_nc = raster_nc.rio.write_crs("EPSG:"+epsg_from)
    ## Reprojection
    raster_reproj_nc = raster_nc.rio.reproject("EPSG:"+epsg_to)
    return raster_reproj_nc