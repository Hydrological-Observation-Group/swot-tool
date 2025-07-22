### author: xin luo 
### create: 2025.2.9, modified: 2025.7.21
### des: read the SWOT data and select the variables within the given geometry.

import geopandas as gpd
from pyproj import CRS

def swot_pixc_mask(pixc_nc, 
                    vars_sel=['latitude', 'longitude', 'height', \
                              'solid_earth_tide', 'pole_tide', \
                              'load_tide_fes', 'iono_cor_gim_ka', 'geoid',\
                              'pixel_area','geolocation_qual'], 
                    region_gpd=None, 
                    path_masked=None):
    """
    des: read the SWOT_L2_HR_PIXC data and select the variables within the given geometry.    
    args:
      pixc_nc (xarray): the SWOT PIXC dataset.
      vars (list): list of variables to be selected.
      region_gpd (geopandas): the geometry to be used for selecting the data.    
    returns:
      pix_masked (xarray): the selected variables within the geometry.
    """ 
    pixc_masked = pixc_nc.copy(deep=True)
    # Select main variables to be written out
    if vars_sel is not None:
      pixc_masked = pixc_masked[vars_sel]

    if region_gpd is not None:
        if region_gpd.crs.to_epsg() != 4326:
          region_gpd = region_gpd.to_crs(epsg='4326')
        else:
          # Remove variables outside the vector geometry
          points = gpd.GeoDataFrame(geometry=gpd.points_from_xy(pixc_masked.longitude, pixc_masked.latitude))
          id_points_in_geom = points.sindex.query(region_gpd.geometry.unary_union, predicate='contains')
          pixc_masked = pixc_masked.isel(points=id_points_in_geom )
    if pixc_masked.sizes['points'] == 0:
      print(f"No points found within the geometry")
      return None    

    # Write the selected variables to a new .nc file
    if path_masked is not None:
        pixc_masked.to_netcdf(path_masked)
        print(f"file read and written to {path_masked}")
    return pixc_masked


def swot_raster_mask(raster_nc, 
                     vars_sel=['x', 'y', 'wse','sig0', 'geoid', 'wse_qual'], 
                     region_gpd=None, 
                     path_masked=None):
    """
    des: read the SWOT_L2_HR_Raster data and select the variables within the given geometry.    
    args:
      raster_nc (xarray): the SWOT Raster dataset.
      vars (list): list of variables to be selected.
      region_gpd (geopandas): the geometry to be used for selecting the data.    
    returns:
      raster_masked (xarray): the selected variables within the geometry.
    """
    raster_masked = raster_nc.copy(deep=True)
    # Select main variables to be written out
    if vars_sel is not None:
        raster_masked = raster_masked[vars_sel]

    if region_gpd is not None:
        epsg_gpd = str(region_gpd.crs.to_epsg())
        crs_wkt = raster_nc.crs.attrs['crs_wkt']
        epsg_raster = str(CRS.from_wkt(crs_wkt).to_epsg())
        if epsg_gpd != epsg_raster:
          raise ValueError(f"EPSG code mismatch: {epsg_gpd} != {epsg_raster}. Please check the CRS of the data.")
        else:
          raster_masked = raster_masked.rio.clip(region_gpd.geometry.values, region_gpd.crs, drop=True)

    # Write the selected variables to a new .nc file
    if path_masked is not None:
        for var in raster_masked.data_vars:
            if 'grid_mapping' in raster_masked[var].attrs:
                del raster_masked[var].attrs['grid_mapping']
        raster_masked.to_netcdf(path_masked)
        print(f"file read and written to {path_masked}")
    return raster_masked
