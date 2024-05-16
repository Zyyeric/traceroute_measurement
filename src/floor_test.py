import math
import json
import requests
import os
import random
from geopy.distance import great_circle

def calculate_radius(curr_min_rtt, prev_min_rtt):
    if curr_min_rtt is None:
        print("Error when parsing RTTs; Cannot Calculate Radius")
        return None
    
    rtt_diff = abs(curr_min_rtt - prev_min_rtt)
    speed_of_light = 299.792458  # Speed of light in km/ms
    radius = (rtt_diff / 2) * ((speed_of_light) * (2 / 3))  # travel speed of optic fiber
    return radius

def is_within_radius(lat1, lon1, lat2, lon2, radius):
    if None in [lat1, lon1, lat2, lon2]:
        print(f"Invalid coordinates received: {lat1}, {lon1}, {lat2}, {lon2}")
        return False
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    f = 1 / 298.257223563
    b = (1 - f) * 6371

    distance = c * b
    
    if distance <= radius:
        return True 
    else:
        print("A wrong IP mapping has occurred")
        return False

def geolocate_city_region(city, region, country):
    api_key = '37fd03c63efb47bb9c7d5804927a6a48'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={city},{region},{country}&key={api_key}'
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data['results']:
                result = data['results'][0]
                latitude = result['geometry']['lat']
                longitude = result['geometry']['lng']
                return latitude, longitude
        print(f"Error occurred while geolocating city and region: {city}, {region}")
        return None, None
    
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making the API request: {e}")
        return None, None

def get_country_borders(country_code):
    api_key = '37fd03c63efb47bb9c7d5804927a6a48'
    url = f'https://api.opencagedata.com/geocode/v1/json?q={country_code}&key={api_key}&pretty=1&no_annotations=1'
    print(f"Requesting URL: {url}")
    try:
        response = requests.get(url)
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response for country code {country_code}: {response.text}")
            data = response.json()
            print(f"Data for country code {country_code}: {data}")
            if data['results']:
                bounds = data['results'][0]['bounds']
                northeast = bounds['northeast']
                southwest = bounds['southwest']
                return [(northeast['lng'], northeast['lat']), (southwest['lng'], southwest['lat'])]
        print(f"Error occurred while fetching borders for country code: {country_code}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making the API request: {e}")
        return None

def flatten_polygons(polygons):
    flattened = []
    for polygon in polygons:
        if isinstance(polygon[0][0], list):
            flattened.extend(flatten_polygons(polygon))
        else:
            flattened.append(polygon)
    return flattened

def sample_coordinates(coordinates, sample_size=100):
    if len(coordinates) > sample_size:
        return random.sample(coordinates, sample_size)
    return coordinates

def find_nearest_points(country1_code, country2_code, sample_size=100):
    borders1 = get_country_borders(country1_code)
    borders2 = get_country_borders(country2_code)
    
    if not borders1 or not borders2:
        print(f"Could not fetch borders for one or both countries: {country1_code}, {country2_code}")
        return None, None, None, None
    
    sampled_borders1 = sample_coordinates(borders1, sample_size)
    sampled_borders2 = sample_coordinates(borders2, sample_size)
    
    min_distance = float('inf')
    closest_points = None

    for point1 in sampled_borders1:
        for point2 in sampled_borders2:
            dist = great_circle((point1[1], point1[0]), (point2[1], point2[0])).kilometers
            if dist < min_distance:
                min_distance = dist
                closest_points = (point1[1], point1[0], point2[1], point2[0])
    
    if closest_points:
        return closest_points
    else:
        return None, None, None, None

def process_traceroute_file(traceroute_file_path):
    floor_test_results = []
    valid_data_points = []
    all_data_points = []

    prev_latitude, prev_longitude, prev_min_rtt = None, None, None
    first_valid_row = True

    with open(traceroute_file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        # Remove non-numeric leading characters
        line = line.lstrip(' ╭─╰─')  
        # Skip lines with special characters or non-standard entries
        if any(ch in line for ch in ['✓', '✘', '*', 'inf', 'S&T']):
            continue

        parts = line.strip().split()
        if len(parts) < 4 or not parts[2].replace('.', '', 1).isdigit():
            continue

        ip_address, asn, rtt = parts[0], parts[1], parts[2]
        rtt = float(rtt) if rtt != '-inf' else None
        geolocation = ' '.join(parts[3:]).strip('()')
        geolocation_parts = geolocation.rsplit(', ', 3)

        all_data_points.append({
            'ip_address': ip_address,
            'asn': asn,
            'rtt': rtt,
            'geolocation': geolocation
        })

        if rtt is None:
            first_valid_row = True  # Reset for the next valid row
            continue  # Skip if RTT is invalid

        if len(geolocation_parts) < 4 or 'None' in geolocation_parts[:2]:
            # Skip if city or region is None
            if len(geolocation_parts) < 4:
                country1 = None
            else:
                country1 = geolocation_parts[2].strip()
            country2 = "SG"  # Default to Singapore as the fallback (or adjust as needed)
            if not country1 or len(country1) != 2:
                print(f"Invalid country code detected: {country1}")
                continue
            latitude, longitude, _, _ = find_nearest_points(country1, country2)
            if latitude is None or longitude is None:
                first_valid_row = True  # Reset for the next valid row
                continue  # Skip if nearest points calculation fails

            valid_data_points.append({
                'ip_address': ip_address,
                'rtt': rtt,
                'latitude': latitude,
                'longitude': longitude
            })
            if first_valid_row:
                prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
                first_valid_row = False
            continue

        city, region, country, continent = geolocation_parts
        if city == 'None' or region == 'None':
            # Skip if city or region is None
            country1 = country.strip()
            country2 = "SG"  # Default to Singapore as the fallback (or adjust as needed)
            if not country1 or len(country1) != 2:
                print(f"Invalid country code detected: {country1}")
                continue
            latitude, longitude, _, _ = find_nearest_points(country1, country2)
            if latitude is None or longitude is None:
                first_valid_row = True  # Reset for the next valid row
                continue  # Skip if nearest points calculation fails

            valid_data_points.append({
                'ip_address': ip_address,
                'rtt': rtt,
                'latitude': latitude,
                'longitude': longitude
            })
            if first_valid_row:
                prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
                first_valid_row = False
            continue
        else:
            latitude, longitude = geolocate_city_region(city, region, country.strip())
            if latitude is None or longitude is None:
                first_valid_row = True  # Reset for the next valid row
                continue  # Skip if geolocation lookup fails

        if first_valid_row:
            prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
            first_valid_row = False
            continue

        city, region, country, continent = geolocation_parts
        if city == 'None' or region == 'None':
            # Skip if city or region is None
            country1 = country.strip()
            country2 = "SG"  # Default to Singapore as the fallback (or adjust as needed)
            if not country1 or len(country1) != 2:
                print(f"Invalid country code detected: {country1}")
                continue
            latitude, longitude, _, _ = find_nearest_points(country1, country2)
            if latitude is None or longitude is None:
                first_valid_row = True  # Reset for the next valid row
                continue  # Skip if nearest points calculation fails

            valid_data_points.append({
                'ip_address': ip_address,
                'rtt': rtt,
                'latitude': latitude,
                'longitude': longitude
            })
            if first_valid_row:
                prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
                first_valid_row = False
            continue
        else:
            latitude, longitude = geolocate_city_region(city, region, country.strip())
            if latitude is None or longitude is None:
                first_valid_row = True  # Reset for the next valid row
                continue  # Skip if geolocation lookup fails

        valid_data_points.append({
            'ip_address': ip_address,
            'rtt': rtt,
            'latitude': latitude,
            'longitude': longitude
        })

    if not valid_data_points:
        print("No valid data points found.")
        return

    for data_point in valid_data_points:
        latitude, longitude, rtt = data_point['latitude'], data_point['longitude'], data_point['rtt']
        
        if first_valid_row:
            prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
            first_valid_row = False
            continue

        radius = calculate_radius(rtt, prev_min_rtt) if prev_min_rtt is not None else None
        within_radius = is_within_radius(prev_latitude, prev_longitude, latitude, longitude, radius) if radius is not None else True

        floor_test_results.append({
            'ip_address': data_point['ip_address'],
            'rtt': rtt,
            'radius': radius,
            'geolocation_within_radius': within_radius
        })

        prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt

    output_file_path = os.path.splitext(traceroute_file_path)[0] + "_floor_test_results.json"
    with open(output_file_path, "w") as file:
        json.dump({
            'all_data_points': all_data_points,
            'floor_test_results': floor_test_results
        }, file, indent=4)

    print(f"Floor test results logged for {traceroute_file_path}.")

def main():
    trviz_directory = "../trviz"  # Update the relative path to the "triviz" directory
    
    while True:
        file_name = input("Enter the traceroute data file name (or 'q' to quit): ")
        
        if file_name.lower() == 'q':
            break
        
        traceroute_file_path = os.path.join(trviz_directory, file_name)
        
        if os.path.isfile(traceroute_file_path):
            process_traceroute_file(traceroute_file_path)
        else:
            print(f"File '{file_name}' not found in the 'triviz' directory.")

if __name__ == "__main__":
    main()







# use the dictionary as a mapping 
# to find the shortest distance between two countries

# stop at the first incorrect result 
# look into more interesting data -> brazil -> use japan / US to test code 