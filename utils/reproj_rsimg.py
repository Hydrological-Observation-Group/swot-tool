## author: xin luo 
## creat: 2025.7.25
## des: Reproject a raster image to a new coordinate reference system (CRS).

import rasterio as rio
from rasterio.warp import calculate_default_transform, reproject
from rasterio.warp import Resampling

def reproj_rsimg(rsimg_stacked_rio, target_crs, path_reprojected):
    """
    des: Reproject a raster image to a new coordinate reference system (CRS).
    Args:
        rsimg_stacked_rio: The input raster image (stacked).
        target_crs: The target CRS to reproject to.
        path_reprojected: path to save the reprojected raster image.
    Returns:
        The path of reprojected raster image.
    """

    transform, width, height = calculate_default_transform(
                    rsimg_stacked_rio.crs, target_crs, rsimg_stacked_rio.width, 
                    rsimg_stacked_rio.height, *rsimg_stacked_rio.bounds)

    kwargs = rsimg_stacked_rio.meta.copy()
    kwargs.update({
    'crs': target_crs,
    'transform': transform,
    'width': width,
    'height': height
    })    
    with rio.open(path_reprojected, 'w', **kwargs) as dst:
        for i in range(1, rsimg_stacked_rio.count + 1):
            reproject(
            source=rio.band(rsimg_stacked_rio, i),
            destination=rio.band(dst, i),
            src_transform=rsimg_stacked_rio.transform,
            src_crs=rsimg_stacked_rio.crs,
            dst_transform=transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest
            )
    return path_reprojected
