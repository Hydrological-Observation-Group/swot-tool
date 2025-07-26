### author: xin luo 
### create: 2025.7.24
### des: timeseries data interpolation functions.


import pandas as pd
def interpolate_at_target(timeseries_data, timeseries_target, method='linear'):
    """
    des: interpolate timeseries_data to match the timestamps of timeseries_target.
    params:
        timeseries_data: pd.Series with datetime index, the series to be interpolated.
        timeseries_target: pd.Series with datetime index, the series with target timestamps.
        method: str, interpolation method, default is 'linear'. options include 'nearest', 'linear', 'time', 'quadratic'/'cubic' etc.
    returns:
        pd.Series: interpolated values of timeseries_data at the timestamps of timeseries_target.
    """
    # merge indices of both series
    combined_index = timeseries_data.index.union(timeseries_target.index).sort_values()
    # reindex timeseries_data to the combined index and interpolate
    full_series = timeseries_data.reindex(combined_index).interpolate(method=method)
    # return the interpolated values at the indices of timeseries_target
    return full_series.loc[timeseries_target.index]

