
"""Offline GO Engineering Core v0.1 staging namespace (no solver/Qt deps)."""
from .catalog import (CatalogError, CATALOG_VERSION, STATUS_NOMINAL,
    STATUS_UNSUPPORTED, catalog_info, catalog_sha256, section_names,
    section_record, nominal_section_properties, section_identity)

__all__ = ["CatalogError", "CATALOG_VERSION", "STATUS_NOMINAL",
           "STATUS_UNSUPPORTED", "catalog_info", "catalog_sha256",
           "section_names", "section_record", "nominal_section_properties",
           "section_identity"]
