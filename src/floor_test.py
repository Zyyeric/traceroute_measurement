import math
import json
import requests
import os

def calculate_radius(curr_min_rtt, prev_min_rtt):
    if curr_min_rtt is None:
        print("Error when parsing RTTs; Cannot Calculate Radius")
        return None
    
    rtt_diff = abs(curr_min_rtt - prev_min_rtt)
    speed_of_light = 299792.458  # Speed of light in km/s
    radius = (rtt_diff / 2) * ((speed_of_light/1000) * (2/3))  # travel speed of optic fiber
    return radius

def is_within_radius(lat1, lon1, lat2, lon2, radius):
    # Using the Vincenty formula to calculate the distance between two coordinates
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Calculate the difference between the two coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # Calculate the ellipsoid parameters
    f = 1/298.257223563 # flattening of the Earth's ellipsoid
    b = (1 - f) * 6371 # semi-minor axis of the Earth's ellipsoid

    # Return the distance
    distance = c * b
    
    if distance <= radius:
        return True 
    else:
        print("A wrong ip mapping has occurred")
        return False

def geolocate_city_region(city, region, country):
    # Replace 'YOUR_API_KEY' with your actual API key
    api_key = 'YOUR_API_KEY'
    
    # Construct the API request URL
    url = f'https://api.opencagedata.com/geocode/v1/json?q={city},{region},{country}&key={api_key}'
    
    try:
        # Send a GET request to the API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            
            # Extract the latitude and longitude from the API response
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

def main():
    floor_test_results = []

    # Specify the path to the traceroute data file within the "triviz" directory
    traceroute_file_path = os.path.join("triviz", "6049-6248.txt")

    with open(traceroute_file_path, "r") as file:
        lines = file.readlines()

    # Initialize prev_latitude, prev_longitude, and prev_min_rtt with the first hop's data
    first_hop = lines[0].strip().split(" || ")[0].split()
    geolocation_info = ' '.join(first_hop[3:])
    geolocation_info = geolocation_info.strip('()')
    geolocation_parts = geolocation_info.split(', ')
    city = geolocation_parts[0]
    region = geolocation_parts[1]
    country = geolocation_parts[2]
    prev_latitude, prev_longitude = geolocate_city_region(city, region, country)
    prev_min_rtt = float(first_hop[2])

    for line in lines[1:]:  # Skip the first line since it's used as the starting point
        hops = line.strip().split(" || ")
        for hop in hops:
            hop_data = hop.split()
            if len(hop_data) >= 4:
                ip_address = hop_data[0]
                curr_min_rtt = float(hop_data[2])
                geolocation_info = ' '.join(hop_data[3:])
                geolocation_info = geolocation_info.strip('()')
                geolocation_parts = geolocation_info.split(', ')
                if len(geolocation_parts) >= 4:
                    city = geolocation_parts[0]
                    region = geolocation_parts[1]
                    country = geolocation_parts[2]
                    continent = geolocation_parts[3]
                    
                    radius = calculate_radius(curr_min_rtt, prev_min_rtt)
                    
                    within_radius = False
                    if city != 'None' and region != 'None':
                        latitude, longitude = geolocate_city_region(city, region, country)
                        if latitude is not None and longitude is not None:
                            within_radius = is_within_radius(latitude, longitude, prev_latitude, prev_longitude, radius)
                            if within_radius:
                                prev_latitude, prev_longitude = latitude, longitude
                                prev_min_rtt = curr_min_rtt
                    
                    floor_test_results.append({
                        'ip_address': ip_address,
                        'rtt': prev_min_rtt,
                        'radius': radius,
                        'geolocation_within_radius': within_radius
                    })

    # Log the floor test results
    with open("floor_test_results.json", "w") as file:
        json.dump(floor_test_results, file, indent=4)

    print("Floor test results logged.")
    
if __name__ == "__main__":
    main()