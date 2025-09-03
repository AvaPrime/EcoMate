# tests/unit/test_validators.py
import pytest
from pydantic import ValidationError

# Assuming the model to be tested is in this path
from ecomate_ai.domain.models import SiteSpec

def test_site_spec_validates_lat_lon():
    """Tests that the SiteSpec model correctly validates valid latitude and longitude."""
    # Valid data
    s = SiteSpec(lat=-34.036, lon=23.047, altitude_m=5)
    assert s.lat == -34.036
    assert s.lon == 23.047

def test_site_spec_invalid_lat_lon():
    """Tests that the SiteSpec model raises a ValidationError for out-of-range lat/lon."""
    # Invalid latitude
    with pytest.raises(ValidationError) as excinfo:
        SiteSpec(lat=-91, lon=23.047, altitude_m=5)
    assert "latitude" in str(excinfo.value).lower()

    # Invalid longitude
    with pytest.raises(ValidationError) as excinfo:
        SiteSpec(lat=-34.036, lon=181, altitude_m=5)
    assert "longitude" in str(excinfo.value).lower()

def test_site_spec_altitude_validation():
    """Tests validation for the altitude field."""
    # Should accept reasonable altitudes
    s = SiteSpec(lat=0, lon=0, altitude_m=8848) # Mt. Everest
    assert s.altitude_m == 8848
    
    s = SiteSpec(lat=0, lon=0, altitude_m=-418) # Dead Sea
    assert s.altitude_m == -418

    # Optional: Add a test for unreasonable altitude if validation exists
    # with pytest.raises(ValidationError):
    #     SiteSpec(lat=0, lon=0, altitude_m=100000) # Above Armstrong limit
