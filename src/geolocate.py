import requests
import json
import subprocess
import math

def perform_traceroute(target):
    traceroute_output = subprocess.check_output(["traceroute", target]).decode("utf-8")
    ip_addresses_and_rtts = extract_ip_addresses_and_rtts(traceroute_output)
    return ip_addresses_and_rtts

def extract_ip_addresses_and_rtts(traceroute_output):
    lines = traceroute_output.strip().split("\n")
    ip_addresses_rtts = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            ip_address = None
            rtts = []
            for part in parts[1:]:
                if '(' in part and ')' in part:
                    ip_address = part.strip('()')
                    if is_valid_ip(ip_address):
                        ip_addresses_rtts.append((ip_address, []))
                else:
                    try:
                        rtt = float(part)
                        rtts.append(rtt)
                    except ValueError:
                        pass
            if ip_address and rtts:
                ip_addresses_rtts[-1] = (ip_address, rtts)
    return ip_addresses_rtts


def is_valid_ip(ip):
    try:
        parts = ip.split(".")
        if len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts):
            return True
    except ValueError:
        pass
    return False

def geolocate_ip_ipgeolocation(ip_address, api_key):
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip_address}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while geolocating IP using ipgeolocation.io: {ip_address}")
        print(f"Error details: {e}")
        return None

def geolocate_ip_ripe_ipmap(ip_address):
    url = f"https://ipmap-api.ripe.net/v1/locate/{ip_address}/best"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while geolocating IP using RIPE IPmap: {ip_address}")
        print(f"Error details: {e}")
        return None

def calculate_radius(rtts):
    if not rtts:
        print("Error when parsing RTTs; Cannot Calculate Radius")
        return None
    max_rtt = max(rtts)
    speed_of_light = 299792.458  # Speed of light in km/s
    radius = (max_rtt / 2) * ((speed_of_light/1000) * (2/3)) #travel speed of optic fibre
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
    
    print(distance, radius)
    if distance <= radius:
        return True 
    else:
        print("A wrong ip mapping has occurred")
        return False

def main():
    target = input("Enter the target IP address: ")
    source_latitude = float(input("Enter the latitude of the package's origin: "))
    source_longitude = float(input("Enter the longitude of the package's origin: "))
    ip_addresses_rtts = perform_traceroute(target)
    
    ipgeolocation_results = []
    ripe_ipmap_results = []
    floor_test_results = []
    
    ipgeolocation_api_key = "5fb60422ea374a6bb349d9772154da5b"
    
    #print(f"this is ip_addresses_rtts:{ip_addresses_rtts}")
    for ip_address, rtts in ip_addresses_rtts:
        #print(f"this is ip_address:{ip_address}")
        ipgeolocation_data = geolocate_ip_ipgeolocation(ip_address, ipgeolocation_api_key)
        #print(ipgeolocation_data)
        ripe_ipmap_data = geolocate_ip_ripe_ipmap(ip_address)
        #print(ripe_ipmap_data)
        
        radius = calculate_radius(rtts)
        
        ipgeolocation_within_radius = False
        ripe_ipmap_within_radius = False
        
        if ipgeolocation_data:
            ipgeolocation_results.append(ipgeolocation_data)
            if 'latitude' in ipgeolocation_data and 'longitude' in ipgeolocation_data:
                ipgeolocation_latitude = float(ipgeolocation_data['latitude'])
                ipgeolocation_longitude = float(ipgeolocation_data['longitude'])
                ipgeolocation_within_radius = is_within_radius(ipgeolocation_latitude, ipgeolocation_longitude,
                                                            source_latitude, source_longitude, radius)
        else:
            ipgeolocation_results.append(None)
        
        if ripe_ipmap_data:
            ripe_ipmap_results.append(ripe_ipmap_data)
            if isinstance(ripe_ipmap_data, dict) and ripe_ipmap_data['location']!= None:
                #todo: log the ip addresses that don't have geolocation mapping 
                location_data = ripe_ipmap_data['location']
                if 'latitude' in location_data and 'longitude' in location_data:
                    ripe_ipmap_latitude = float(location_data['latitude'])
                    ripe_ipmap_longitude = float(location_data['longitude'])
                    ripe_ipmap_within_radius = is_within_radius(ripe_ipmap_latitude, ripe_ipmap_longitude,
                                                                source_latitude, source_longitude, radius)
        else:
            ripe_ipmap_results.append(None)
        
        floor_test_results.append({
            'ip_address': ip_address,
            'rtt': rtts,
            'radius': radius,
            'ipgeolocation_within_radius': ipgeolocation_within_radius,
            'ripe_ipmap_within_radius': ripe_ipmap_within_radius
        })
    
    # Log the geolocation results and floor test results
    with open("ipgeolocation_results.json", "w") as file:
        json.dump(ipgeolocation_results, file, indent=4)
    
    with open("ripe_ipmap_results.json", "w") as file:
        json.dump(ripe_ipmap_results, file, indent=4)
    
    with open("floor_test_results.json", "w") as file:
        json.dump(floor_test_results, file, indent=4)
    
    print("Geolocation results and floor test results logged.")
    
if __name__ == "__main__":
    main()