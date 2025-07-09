"""
Geographic Augmentation of Extracted Building Features Tool (Gauntlet)
Version 2.0 (extended contextual features)

Author: Taylor Hauser
Contact: hausertr@ornl.gov
Purpose: To generate 65 features that describes building level morphologies from polygon geometry.
"""

import gc
import math
import traceback
import pandas as pd
import geopandas as gpd
from scipy import spatial
from functools import partial
from typing import  Union, Tuple, List
from tqdm.contrib.concurrent import process_map
from shapely.geometry import mapping, Polygon, MultiPolygon

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def slice_frame(frame:Union[pd.DataFrame, gpd.GeoDataFrame], slice_count:int) -> List[Union[pd.DataFrame, gpd.GeoDataFrame]]:
    """
    A function to divide either a pandas or geopandas dataframe into slice_count number of frames.

    frame:pd.DataFrame or gpd.GeoDataFrame: Original dataframe
    slice_count:int: desired number of dataframes

    Returns: a list of either pandas or geopandas dataframes.
    """

    chunk = int(len(frame) / slice_count)
    counts = range(slice_count)
    counts = [chunk for _ in counts]
    startIndex = [sum(counts[:index]) for index, _ in enumerate(counts)]
    startIndex.append(len(frame))

    tasks = []
    for index, _ in enumerate(startIndex):
        if index == slice_count:
            break
        tasks.append(frame.iloc[startIndex[index]:startIndex[index + 1]])

    return tasks


def bounds(geom:Union[Polygon, MultiPolygon]) -> Tuple[float, float, float, int, int]:
    """
    Generates a number of features: 
    
    lat_diff:float: Difference of the max and min latitude in decimal degrees
    long_diff:float: Difference of the max and min longitude in decimal degrees
    extent_area:float: Area of the bounding envelop in square decimal degrees
    vertex_count:int: Number of vertices within the geometry
    geom_count:int: Number of bounding geometries

    Returns: lat_diff, long_diff, exetent_area, vertex_count, geom_count
    """

    minx, miny, maxx, maxy = geom.bounds

    try:

        return abs(maxy-miny), abs(maxx-minx), geom.envelope.area, \
            sum([len(item) for item in mapping(geom)['coordinates'][0]]), len(mapping(geom)['coordinates'][0])

    except IndexError:

        return abs(maxy-miny), abs(maxx-minx), geom.envelope.area, 0
           

def nnd(x:float, y:float, tree:spatial.cKDTree) -> float:
    """
    Generates the Nearest Neighbor Distance between an x, y and member of the tree. The cKDTree includes the 
    the point (x,y) being evaluated. This why tree.query((x, y) 2) is used, otherwise itself would be the nearest neighbor with an ndd = 0.

    x:float: x coordinate of centroid being evaluated
    y:float: y coordinate of centroid being evaluated
    tree:spatial.cKDTree: KDtree spatial index to be searched

    Returns:float: Distance to nearest centroid in meters.
    """

    return tree.query((x, y), 2)[0][1]


def multi_nnd(df:Union[pd.DataFrame, gpd.GeoDataFrame], tree:spatial.cKDTree)-> Union[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Calls function nnd on a dataframe that is a portion of the total work.

    df:pd.DataFrame or gpd.GeoDataFrame: dataframe with lon and lat coordinates

    Returns: a dataframe with the additional attribute NND.
    """

    df['nnd'] = df.apply(lambda x: nnd(x.lon, x.lat, tree), axis=1)

    return df


def nni(x:float, y:float, tree:spatial.cKDTree, nnd:float, sqft:float, buff:int) -> Tuple[int, float, float, float, float, float, float, float, float, float]:
    """
    NNI generates a variety of contextual features to use for classification  

    cluster:int: Count of points within _buff_ meters
    omd:float: Observed mean distance of the scan window
    emd:float: Expected mean distance of the scan window
    nni:float: Nearest Neighbor Index of the scan window
    intensity:float: Amount of NNI within the scan window. 
        intensity is biased as population (n_count) of scan window 
        increases so does intensity regardless of nni pattern.
    n_size_mean:float: Mean size of polygons in scan window (sqft)
    n_size_std:float: Standard Deviation size of polygons in scan window (sqft)
    n_size_min:float: Smallest size of polygons in scan window (sqft)
    n_size_max:float: Largest size of polygons in scan window (sqft)
    n_size_cv:float: Coefficient of Variation size of polygons in scan window (sqft)

    Returns: a Tuple(cluster,omd,emd,nni,intensity,n_size_mean,n_size_std,n_size_min,n_size_max,n_size_cv)
    """

    try:
        results = tree.query_ball_point((x, y), buff)
        cluster = len(results)

        if cluster == 0:

            return 0, 0, 0, 0, 0, None, None, None, None, None

        if cluster == 1:
            sqfts = sqft.iloc[results].describe()
            n_size_mean, n_size_std, n_size_min, n_size_max = sqfts[1], sqfts[2], sqfts[3], sqfts[-1]

            return 1, 0, 0, 0, 0, n_size_mean, 0, n_size_min, n_size_max, 0

        else:            
            nearDs = tree.query((x, y), cluster)[0]           
            intensity = math.pi * (sum(nearDs ** 2)) / cluster
            nnds = nnd.iloc[results]
            omd = (sum(nnds)) / cluster
            emd = .5 * math.sqrt(math.pi * buff ** 2 / cluster)
            nni = omd / emd
            sqfts = sqft.iloc[results].describe()

            n_size_mean, n_size_std, n_size_min, n_size_max = sqfts[1], sqfts[2], sqfts[3], sqfts[-1]
            n_size_cv = n_size_std/n_size_mean

            return cluster, omd, emd, nni, intensity, n_size_mean, n_size_std, n_size_min, n_size_max, n_size_cv

    except:

        traceback.print_exc()
        

def multi_gauntlet_atts(w_gdf:gpd.GeoDataFrame, tree:spatial.cKDTree)-> Union[pd.DataFrame, gpd.GeoDataFrame]:
    """
    Generates the majority of Gauntlet features by calling bounds, nnd, and nni in apply 
    functions on a sliced (partial) geopandas dataframes. Once generated the geopandas 
    dataframe is contactenated into a single dataframe in main.

    w_gdf:gpd.GeoDataFrame: the sliced dataframe to be processed by worker
    tree:spatial.cKDTree: The spatial index to be queried for various Guantlet features

    Returns: a dataframe with full Gauntlet attribution.
    """

    try:        
          
        w_gdf = w_gdf[~w_gdf[f'{w_gdf.geometry.name}'].isna()]

        if len(w_gdf) == 0:

            del w_gdf
            gc.collect()

            return

        w_gdf['shape_area'] = w_gdf.geometry.area
        w_gdf['shape_length'] = w_gdf.geometry.length        
        
        w_gdf[['lat_dif', 'long_dif', 'envel_area', 'vertex_count', 'geom_count']] = pd.DataFrame(w_gdf[f'{w_gdf.geometry.name}'].apply(bounds).tolist(), index=w_gdf.index)        
        w_gdf['complexity_ratio'] = w_gdf['shape_length'] / w_gdf['shape_area']
        w_gdf['iasl'] = w_gdf['vertex_count'] / w_gdf['shape_length']
        w_gdf['vpa'] = w_gdf['vertex_count'] / w_gdf['shape_area']
        w_gdf['complexity_ps'] = w_gdf['complexity_ratio'] / w_gdf['vertex_count']
        w_gdf['ipq'] = 4*math.pi*w_gdf['shape_area']/w_gdf['shape_length']**2        
        
        ### NNI ###               
        global all_NND
        global all_sqft

        w_gdf[['n_count_50', 'omd_50', 'emd_50', 'nni_50', 'intensity_50', 'n_size_mean_50', 'n_size_std_50', 'n_size_min_50',
        'n_size_max_50', 'n_size_cv_50']] = pd.DataFrame(w_gdf.apply(lambda x: nni(x.lon, x.lat, tree, all_NND, all_sqft, 50),
                                                            axis=1).tolist(), index=w_gdf.index)
        
        w_gdf[['n_count_100', 'omd_100', 'emd_100', 'nni_100', 'intensity_100', 'n_size_mean_100', 'n_size_std_100', 'n_size_min_100',
        'n_size_max_100', 'n_size_cv_100']] = pd.DataFrame(w_gdf.apply(lambda x: nni(x.lon, x.lat, tree, all_NND, all_sqft, 100),
                                                            axis=1).tolist(), index=w_gdf.index)
        
        w_gdf[['n_count_250', 'omd_250', 'emd_250', 'nni_250', 'intensity_250', 'n_size_mean_250', 'n_size_std_250', 'n_size_min_250',
        'n_size_max_250', 'n_size_cv_250']] = pd.DataFrame(w_gdf.apply(lambda x: nni(x.lon, x.lat, tree, all_NND, all_sqft, 250),
                                                            axis=1).tolist(), index=w_gdf.index)
        
        w_gdf[['n_count_500', 'omd_500', 'emd_500', 'nni_500', 'intensity_500', 'n_size_mean_500', 'n_size_std_500', 'n_size_min_500',
        'n_size_max_500', 'n_size_cv_500']] = pd.DataFrame(w_gdf.apply(lambda x: nni(x.lon, x.lat, tree, all_NND, all_sqft, 500),
                                                            axis=1).tolist(), index=w_gdf.index)
        
        w_gdf[['n_count_1000', 'omd_1000', 'emd_1000', 'nni_1000', 'intensity_1000', 'n_size_mean_1000', 'n_size_std_1000', 'n_size_min_1000',
        'n_size_max_1000', 'n_size_cv_1000']] = pd.DataFrame(w_gdf.apply(lambda x: nni(x.lon, x.lat, tree, all_NND, all_sqft, 1000),
                                                            axis=1).tolist(), index=w_gdf.index)
        
        out = w_gdf.drop(columns=[f'{w_gdf.geometry.name}'])

        del w_gdf    
        gc.collect()        
        
        return out
        
    except:

        traceback.print_exc()


if __name__ == "__main__":

    ##### Modify below as needed #####

    core_count = 50  # Number of cpus to be used
    task_length = 150000 # When working in parallel the max size of a dataframe a worker can process
    
    id_field = 'BUILD_ID' # A unique identification number is required for joining.
    in_path = '/mnt/output/AL/AL_structures.gdb' # path to data
    out_path = '/mnt/output/AL/al_gauntlet.csv' # path and name of output .csv

    print('loading geopandas dataframe')
    gdf = gpd.read_file(in_path, layer='AL_Structures') # example for targeting a feature class in a file gdb.

    ##### Modify above as needed #####

    gdf = gdf[[f'{id_field}',f'{gdf.geometry.name}']]

    gdf_epsg = gdf.crs.to_epsg()
    if gdf_epsg == 4326:
        pass
    else:
        print('projecting to WGS 84')
        gdf = gdf.to_crs(4326)

    utm_pro = gdf.estimate_utm_crs(datum_name='WGS 84')
    utm_epsg = utm_pro.to_epsg()

    print(f'Projecting to {utm_pro.name}')
    gdf = gdf.to_crs(utm_epsg)

    print('generating pre-gauntlet features')
    gdf['lat'] = gdf.geometry.centroid.y
    gdf['lon'] = gdf.geometry.centroid.x
    gdf['sqmeters'] = gdf.geometry.area
    gdf['sqft'] = gdf.sqmeters * 10.7639

    print('projecting to WGS 84')
    gdf = gdf.to_crs(4326)

    print('Creating Spatial Index')
    tree_points = tuple(zip(gdf.lon, gdf.lat))
    tree_idx = spatial.cKDTree(tree_points)

    del tree_points
    gc.collect()

    print('Slicing frame')
    tasks = slice_frame(gdf, core_count)

    del gdf
    gc.collect()
    
    assignment = partial(multi_nnd, tree=tree_idx)
    results = process_map(assignment, tasks, chunksize=1, max_workers=core_count, desc='Calculating Nearest Neighbor Distance (NND)')
    gdf = pd.concat(results)

    del results
    gc.collect()  

    global all_NND
    all_NND = gdf.nnd
    global all_sqft
    all_sqft = gdf.sqft

    chunk_count = len(gdf)/task_length

    if chunk_count < core_count:
        chunk_count = core_count

    if chunk_count == core_count:
        tasks = slice_frame(gdf, (int(chunk_count)))
    else:
        tasks = slice_frame(gdf, (int(chunk_count)+1))    

    del gdf
    gc.collect()

    assignment = partial(multi_gauntlet_atts, tree=tree_idx)
    results = process_map(assignment, tasks, chunksize=1, max_workers=core_count, desc='Generating remaining Gauntlet features')
    out = pd.concat(results)

    del results
    gc.collect()

    out = out.drop(columns=['lat','lon'])
    out.to_csv(out_path, index=False)

    print('Finished')
