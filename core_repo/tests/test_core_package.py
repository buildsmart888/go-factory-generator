"""Canonical independent Core v0.1 package acceptance tests."""
import unittest
from go_engineering_core import (
    catalog_info, section_record, nominal_section_properties, CatalogError,
    catalog_sha256,
)

class CoreContractTests(unittest.TestCase):
    def test_catalog(self):
        info = catalog_info()
        self.assertEqual(info["version"], "0.1.0")
        self.assertEqual(info["count"], 75)
        self.assertEqual(info["nominal_count"], 40)
        self.assertEqual(info["sha256"], catalog_sha256())
    def test_h_properties(self):
        x = nominal_section_properties(
            "H-300x300x10x15", axis="strong", acknowledge_unverified=True)
        self.assertAlmostEqual(x["A_m2"], .0117)
        self.assertGreater(x["Ix_m4"], x["Iy_m4"])
        self.assertFalse(x["verified"])
    def test_no_silent_default(self):
        with self.assertRaises(CatalogError):
            nominal_section_properties("H-300x300x10x15", axis="strong")
        with self.assertRaises(CatalogError):
            nominal_section_properties("C-150x65x20x2.3", axis="strong", acknowledge_unverified=True)

if __name__ == "__main__":
    unittest.main()
