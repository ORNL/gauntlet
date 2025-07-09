# Geographic Augmentation of Extracted Building Features Tool (Gauntlet)

POC: Taylor Hauser - hausertr@ornl.gov  
Purpose: To generate 65 measurements from geospatial polygon data that describes the morphology of the polygons.

## Requirements

Software Requirements:
* python (recommended version 3.10.15)

The required python packages are:
* geopandas>=0.9
* pandas
* scipy
* tqdm

Optional Software Requirements:
* docker
* docker-compose
* git

## Running data through the Gauntlet

Gauntlet is a single script (.py) in the /src folder. Only a few lines of code will need be modified, lines 204 - 214. The data is required to have an unique id field and a polygon geometry field stored in a common geospatial data format (.shp, .gpkg, .geojson, .gdb/feature_class).

_core_count_ is the number for parallel worker that will be used for the processing script. Adjust accordingly for the system being used. Total cores - 2 is recommended.
```
core_count = 50 
```
_task_length_ is the maximum record count that a parallel worker will encounter. The higher _core_count_, the more workers will be using ram. This _task_length_ may need to be adjusted to a smaller length on high core low ram systems.
```
task_length = 150000
```
_id_field_ is a requirement of gauntlet. This should target a column that is a unique identification number within the dataset. Add a unique id, if needed, and ensure only one geometry field (polygon) is in the targeted dataset.
```
id_field = 'BUILD_ID'
```
_in_path_ is the path to the dataset.
```
in_path = '/mnt/output/AL/AL_structures.gdb'
```
_out_path_ is the path and name of the output which includes the .csv extension.
```
out_path = '/mnt/output/AL/al_gauntlet.csv'
```
Geopandas can handle numerous geospatial datasets. The coded example is targeting a feature class within a file geodatabase. Modify to appropriately ingest the data.
```
gdf = gpd.read_file(in_path, layer='AL_Structures')
```

### Using docker and docker-compose

In the docker-compose.yml modify line 8. '/path_to_data' should be replaced with a real file path leading to the directory containing the data.
```
 - /path_to_data:/mnt/output  
```
Navigate to gauntlet repo and build the container
```
docker-compose up -d --build gauntlet
```
If the container is already built use:
```
docker-compose up -d gauntlet
```
Now execute the container with the following parameters once /src/gauntlet.py has been modified with desired inputs.
```
docker-compose exec gauntlet python /src/gauntlet.py
```

## Gauntlet v2 Feature Set

|Indicator       |Description                                                                                             |
|----------------|--------------------------------------------------------------------------------------------------------|
|shape_area      |Area of polygon in unprojected units                                                                    |
|shape_length    |Perimeter length in unprojected units                                                                   |
|sqft            |Area in square feet                                                                                     |
|nnd             |Distance, in meters, to the nearest neighbor                                                            |
|lat_dif         |The max latitude minus the min latitude in unprojected units                                            |
|long_dif        |The max longitude minus the min longitude in unprojected units                                          |
|envel_area      |the area of the bounding box of the geometry in unprojected units                                       |
|vertex_count    |The count of vertices in the geometry                                                                   |
|geom_count      |The count of polygons in the geometry                                                                   |
|complexity_ratio|Shape_length/shape_area, a measure of how complex the shape is                                          |
|iasl            |Inverse average segment length                                                                          |
|vpa             |Vertices per area                                                                                       |
|complexity_ps   |Complexity per segment, describes the average complexity within each segment                            |
|ipq             |Isoperimetric quotient, describes how well a shape maximizes its area for the given perimeter length    |
|sqmeters        |Area in square meters                                                                                   |
|n_count_50      |Number of building centroids within 50 meters (min = 1 itself is included)                              |
|omd_50          |Observed mean distance, the average distance of centroids within 50 meters                              |
|emd_50          |Expected mean distance, the average distance if all centroids were uniformly spaced and equidistant     |
|nni_50          |Nearest Neighbor Index (Average nearest neighbor) The overall pattern of points in the 50 meter buffer  |
|intensity_50    |The amount of nni occurring within the 50 meter buffer                                                  |
|n_size_mean_50  |The average size of buildings within the 50 meter buffer (sqft)                                         |
|n_size_std_50   |The standard deviation of building sizes within the 50 meter buffer (sqft)                              |
|n_size_min_50   |The smallest building size within the 50 meter buffer (sqft)                                            |
|n_size_max_50   |The largest building sizes within with in the 50 meter buffer (sqft)                                    |
|n_size_cv_50    |The Coefficient of variation of building sizes with in the 50 meter buffer (sqft)                        |
|n_count_100     |Number of building centroids within 100 meters (min = 1 itself is included)                             |
|omd_100         |Observed mean distance, the average distance of centroids within 100 meters                             |
|emd_100         |Expected mean distance, the average distance if all centroids were uniformly spaced and equidistant     |
|nni_100         |Nearest Neighbor Index (Average nearest neighbor) The overall pattern of points in the 100 meter buffer |
|intensity_100   |The amount of nni occurring within the 100 meter buffer                                                 |
|n_size_mean_100 |The average size of buildings within the 100 meter buffer (sqft)                                        |
|n_size_std_100  |The standard deviation of building sizes within the 100 meter buffer (sqft)                             |
|n_size_min_100  |The smallest building size within the 100 meter buffer (sqft)                                           |
|n_size_max_100  |The largest building sizes within with in the 100 meter buffer (sqft)                                   |
|n_size_cv_100   |The Coefficient of variation of building sizes with in the 100 meter buffer (sqft)                       |
|n_count_250     |Number of building centroids within 250 meters (min = 1 itself is included)                             |
|omd_250         |Observed mean distance, the average distance of centroids within 250 meters                             |
|emd_250         |Expected mean distance, the average distance if all centroids were uniformly spaced and equidistant     |
|nni_250         |Nearest Neighbor Index (Average nearest neighbor) The overall pattern of points in the 250 meter buffer |
|intensity_250   |The amount of nni occurring within the 250 meter buffer                                                 |
|n_size_mean_250 |The average size of buildings within the 250 meter buffer (sqft)                                        |
|n_size_std_250  |The standard deviation of building sizes within the 250 meter buffer (sqft)                             |
|n_size_min_250  |The smallest building size within the 250 meter buffer (sqft)                                           |
|n_size_max_250  |The largest building sizes within with in the 250 meter buffer (sqft)                                   |
|n_size_cv_250   |The Coefficient of variation of building sizes with in the 250 meter buffer (sqft)                       |
|n_count_500     |Number of building centroids within 500 meters (min = 1 itself is included)                             |
|omd_500         |Observed mean distance, the average distance of centroids within 500 meters                             |
|emd_500         |Expected mean distance, the average distance if all centroids were uniformly spaced and equidistant     |
|nni_500         |Nearest Neighbor Index (Average nearest neighbor) The overall pattern of points in the 500 meter buffer |
|intensity_500   |The amount of nni occurring within the 500 meter buffer                                                 |
|n_size_mean_500 |The average size of buildings within the 500 meter buffer (sqft)                                        |
|n_size_std_500  |The standard deviation of building sizes within the 500 meter buffer (sqft)                             |
|n_size_min_500  |The smallest building size within the 500 meter buffer (sqft)                                           |
|n_size_max_500  |The largest building sizes within with in the 500 meter buffer (sqft)                                   |
|n_size_cv_500   |The Coefficient of variation of building sizes with in the 1000 meter buffer (sqft)                      |
|n_count_1000    |Number of building centroids within 1000 meters (min = 1 itself is included)                            |
|omd_1000        |Observed mean distance, the average distance of centroids within 1000 meters                            |
|emd_1000        |Expected mean distance, the average distance if all centroids were uniformly spaced and equidistant     |
|nni_1000        |Nearest Neighbor Index (Average nearest neighbor) The overall pattern of points in the 1000 meter buffer|
|intensity_1000  |The amount of nni occurring within the 1000 meter buffer                                                |
|n_size_mean_1000|The average size of buildings within the 1000 meter buffer (sqft)                                       |
|n_size_std_1000 |The standard deviation of building sizes within the 1000 meter buffer (sqft)                            |
|n_size_min_1000 |The smallest building size within the 1000 meter buffer (sqft)                                          |
|n_size_max_1000 |The largest building sizes within with in the 1000 meter buffer (sqft)                                  |
|n_size_cv_1000  |The Coefficient of variation of building sizes with in the 1000 meter buffer (sqft)                      |
