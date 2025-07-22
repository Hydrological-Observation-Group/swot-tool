nc_var=wse
path_nc_in=path_of_nc_file
path_tif_out=path_of_output_tif_file
gdalmdimtranslate -of "GTiff" -array $nc_var -co "COMPRESS=LZW" $path_nc_in $path_tif_out



