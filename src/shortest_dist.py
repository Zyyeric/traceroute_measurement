import geopandas as gpd
import pycountry
from shapely.ops import nearest_points

# Load the world dataset from GeoPandas
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Filter out entries without valid geometries or with multipolygon geometries
world = world[world.geometry.type == 'Polygon']

# Ensure the GeoDataFrame uses the WGS84 coordinate system (latitude/longitude)
world = world.to_crs(epsg=4326)

# Create a dictionary to store the shortest distances
distance_map = {}

# Get a list of country names from pycountry
countries = [country.name for country in pycountry.countries]

# Filter the world GeoDataFrame to include only countries from the pycountry list
world = world[world['name'].isin(countries)]

# Loop through each country to compute the shortest distance to every other country
for i, country1 in world.iterrows():
    for j, country2 in world.iterrows():
        if country1['name'] != country2['name']:
            # Find the nearest points
            p1, p2 = nearest_points(country1.geometry, country2.geometry)
            # Calculate the distance in degrees
            distance = p1.distance(p2)
            # Convert the distance to kilometers using the approximate conversion factor
            distance_km = distance * 111.32  # 1 degree latitude ~ 111.32 km
            distance_map[(country1['name'], country2['name'])] = distance_km

# Example output for a few country pairs
for key, value in list(distance_map.items())[:10]:
    print(f"The shortest distance between {key[0]} and {key[1]} is {value:.2f} km.")