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

    def test_calculate_radius(self):
        self.assertAlmostEqual(calculate_radius(100), 14989.6149, places=3)

    def test_is_within_radius(self):
        self.assertTrue(is_within_radius(0, 0, 0, 0, 1000))
        self.assertFalse(is_within_radius(0, 0, 10, 10, 100))

    # More tests can be added here for other functions like perform_traceroute, geolocate_ip_ripe_ipmap, etc.

if __name__ == '__main__':
    unittest.main()
