"""Guarantee GO Factory geometry names/weights stay synchronized with Core v0.1."""
import unittest

from go_factory_generator.sections import SECTION_LIBRARY
from go_factory_generator.engineering_core import section_names, section_record


class FactoryCatalogParityTests(unittest.TestCase):
    def test_every_factory_section_exists_in_core(self):
        self.assertEqual(set(SECTION_LIBRARY), set(section_names()))

    def test_dims_and_approximate_boq_weights_match(self):
        for name, raw in SECTION_LIBRARY.items():
            with self.subTest(name=name):
                record = section_record(name)
                self.assertEqual(record["family"], raw.family)
                for field, value in (
                    ("h_m", raw.depth_m),
                    ("b_m", raw.width_m),
                    ("tw_m", raw.web_m),
                    ("tf_m", raw.flange_m),
                    ("t_m", raw.thickness_m),
                    ("legacy_weight_kg_m", raw.unit_weight_kg_m),
                ):
                    self.assertAlmostEqual(record[field], value, places=12)

    def test_nominal_metadata_is_never_marked_verified(self):
        from go_factory_generator.engineering_core import section_identity
        for name in SECTION_LIBRARY:
            meta = section_identity(name)
            self.assertEqual(meta["section_catalog_id"], name)
            self.assertEqual(meta["section_catalog_version"], "0.1.0")
            self.assertEqual(meta["section_legacy_mass_status"], "APPROXIMATE_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
