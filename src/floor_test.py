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
    api_key = '37fd03c63efb47bb9c7d5804927a6a48'
    
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
                #print(latitude, longitude)
                return latitude, longitude
        
        print(f"Error occurred while geolocating city and region: {city}, {region}")
        return None, None
    
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while making the API request: {e}")
        return None, None

def process_traceroute_file(traceroute_file_path):
    floor_test_results = []

    prev_asn = None  # Initialize the previous ASN to None
    prev_latitude, prev_longitude, prev_min_rtt = None, None, 0.0
    first_row = True

    with open(traceroute_file_path, "r") as file:
        lines = file.readlines()

    for line in lines:
        line = line.lstrip(' ╭─╰─')  # Remove any leading non-numeric characters
        if any(ch in line for ch in ['✓', '✘', '*', 'inf', 'S&T']):
            continue  # Skip lines with special characters or non-standard entries

        parts = line.strip().split()
        if len(parts) < 4 or not parts[2].replace('.', '', 1).isdigit():
            continue

        ip_address, asn, rtt = parts[0], parts[1], parts[2]
        if asn == '*':
            continue  # Skip if ASN is not available

        rtt = float(rtt) if rtt != '-inf' else None
        if rtt is None:
            continue  # Skip if RTT is invalid

        geolocation = ' '.join(parts[3:]).strip('()')
        geolocation_parts = geolocation.split(', ')
        if len(geolocation_parts) < 4 or 'None' in geolocation_parts[:2]:
            continue  # Skip if geolocation is incomplete

        city, region, country, continent = geolocation_parts[:4]
        latitude, longitude = geolocate_city_region(city, region, country)
        if latitude is None or longitude is None:
            continue  # Skip if geolocation lookup fails

        if first_row:
            prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt
            prev_asn = asn  # Set previous ASN after processing the first row
            first_row = False
            continue

        if asn == prev_asn:
            continue  # Skip consecutive duplicates

        # Calculate the radius and check if within the expected range
        radius = calculate_radius(rtt, prev_min_rtt) if prev_min_rtt is not None else None
        within_radius = is_within_radius(prev_latitude, prev_longitude, latitude, longitude, radius) if radius is not None else True

        # Prepare data for output
        floor_test_results.append({
            'ip_address': ip_address,
            'asn': asn,
            'rtt': rtt,
            'radius': radius,
            'geolocation_within_radius': within_radius
        })

        # Update previous markers
        prev_asn = asn
        prev_latitude, prev_longitude, prev_min_rtt = latitude, longitude, rtt

    # Save the results to a file
    output_file_path = os.path.splitext(traceroute_file_path)[0] + "_floor_test_results.json"
    with open(output_file_path, "w") as file:
        json.dump(floor_test_results, file, indent=4)

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