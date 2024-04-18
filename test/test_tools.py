import unittest
from unittest.mock import patch, MagicMock
from src.geolocate import (
    is_valid_ip,
    extract_ip_addresses_and_rtts,
    geolocate_ip_ipgeolocation,
    calculate_radius,
    is_within_radius,
    # Add any other functions you need to import for testing
)

class TestNetworkTools(unittest.TestCase):

    def test_is_valid_ip(self):
        # Valid IP addresses
        self.assertTrue(is_valid_ip("192.168.1.1"))
        self.assertTrue(is_valid_ip("255.255.255.255"))
        # Invalid IP addresses
        self.assertFalse(is_valid_ip("192.168.1.256"))  # Invalid byte in IP
        self.assertFalse(is_valid_ip("192.168.1"))  # Incomplete IP
        self.assertFalse(is_valid_ip("abc.def.ghi.jkl"))  # Non-numeric

    def test_extract_ip_addresses_and_rtts(self):
        sample_output = """
        traceroute to 192.168.1.1 (192.168.1.1), 64 hops max, 52 byte packets
         1  192.168.0.1 (192.168.0.1)  3.674 ms  1.029 ms  0.975 ms
         2  192.168.1.1 (192.168.1.1)  2.897 ms  3.003 ms  3.100 ms
        """
        expected_result = [
            ("192.168.0.1", [3.674, 1.029, 0.975]),
            ("192.168.1.1", [2.897, 3.003, 3.100])
        ]
        self.assertEqual(extract_ip_addresses_and_rtts(sample_output), expected_result)

    @patch('src.geolocate.requests.get')
    def test_geolocate_ip_ipgeolocation(self, mock_get):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "ip": "192.168.1.1",
            "latitude": "10.000",
            "longitude": "20.000",
            "country_name": "Wonderland"
        }
        mock_get.return_value = mock_response

        # Test the function
        result = geolocate_ip_ipgeolocation("192.168.1.1", "dummy_api_key")
        self.assertIsNotNone(result)
        self.assertEqual(result['latitude'], "10.000")
        self.assertEqual(result['longitude'], "20.000")
        self.assertEqual(result['country_name'], "Wonderland")

    def test_is_within_radius(self):
        self.assertTrue(is_within_radius(0, 0, 0, 0, 1000))
        self.assertFalse(is_within_radius(0, 0, 10, 10, 100))

    def test_positive_case(self):
        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = 40.7142
        longitude2 = -74.0064
        radius = 1  # 1 km
        self.assertTrue(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

    def test_negative_case(self):
        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = 51.5072
        longitude2 = -0.1275
        radius = 100  # 100 km
        self.assertFalse(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

    def test_edge_case(self):
        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = 40.7048
        longitude2 = -74.0171
        radius = 5  # 5 km
        self.assertTrue(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

    def test_boundary_cases(self):
        latitude1 = 0.0
        longitude1 = 0.0
        latitude2 = 90.0
        longitude2 = 180.0
        radius = 10000  # 10000 km
        self.assertTrue(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

        latitude1 = -90.0
        longitude1 = -180.0
        latitude2 = 90.0
        longitude2 = 180.0
        radius = 20000  # 20000 km
        self.assertTrue(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

    def test_null_input(self):
        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = None
        longitude2 = -74.0064
        radius = 1
        self.assertFalse(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = 51.5072
        longitude2 = None
        radius = 100
        self.assertFalse(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

    def test_invalid_input(self):
        latitude1 = 40.7128
        longitude1 = -74.0059
        latitude2 = 91.0  # Invalid latitude
        longitude2 = -74.0064
        radius = 1
        self.assertFalse(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))

        latitude1 = 40.7128
        longitude1 = -184.0  # Invalid longitude
        latitude2 = 51.5072
        longitude2 = -0.1275
        radius = 100
        self.assertFalse(is_within_radius(latitude1, longitude1, latitude2, longitude2, radius))


if __name__ == '__main__':
    unittest.main()
