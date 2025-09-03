# EcoMate Examples

This directory contains example scripts and demonstrations for various EcoMate features and integrations.

## Available Examples

### Google Maps Integration (`google_maps_example.py`)

Demonstrates how to use the Google Maps Platform APIs for geospatial operations in EcoMate.

**Features demonstrated:**
- Address geocoding and reverse geocoding
- Distance and travel time calculations
- Elevation data retrieval
- Site logistics cost estimation
- Site accessibility validation

**Prerequisites:**
1. Google Maps Platform API key
2. Enabled APIs:
   - Geocoding API
   - Distance Matrix API
   - Elevation API

**Setup:**
```bash
# Set your Google Maps API key
export GOOGLE_API_KEY="your-api-key-here"

# Run the example
python examples/google_maps_example.py
```

**Expected Output:**
- Geocoding results for South African addresses
- Distance calculations between major cities
- Elevation data for various locations
- Logistics cost estimates for site installations
- Accessibility assessments for different terrains

## Environment Variables

Make sure to set the following environment variables before running examples:

- `GOOGLE_API_KEY`: Your Google Maps Platform API key
- Other variables as specified in `.env.example`

## Running Examples

### From Project Root
```bash
# Make sure you're in the EcoMate project root
cd /path/to/EcoMate

# Set environment variables
source .env  # or load your .env file

# Run specific example
python examples/google_maps_example.py
```

### From Examples Directory
```bash
# Navigate to examples directory
cd examples

# Set Python path to include ecomate-ai services
export PYTHONPATH="../ecomate-ai:$PYTHONPATH"

# Run example
python google_maps_example.py
```

## Integration with EcoMate Services

These examples show how to integrate external APIs with EcoMate's AI services:

1. **Proposal Generation**: Use geocoding to validate addresses in environmental proposals
2. **Logistics Planning**: Calculate transportation costs for equipment deployment
3. **Site Assessment**: Evaluate terrain difficulty and accessibility
4. **Environmental Context**: Incorporate elevation and geographic data into recommendations

## Adding New Examples

When adding new example scripts:

1. Create a descriptive filename (e.g., `weather_api_example.py`)
2. Include comprehensive docstrings and comments
3. Add error handling and user-friendly output
4. Update this README with usage instructions
5. Test with various input scenarios

## Troubleshooting

### Common Issues

**API Key Errors:**
- Verify your API key is correct
- Check that required APIs are enabled in Google Cloud Console
- Ensure you have sufficient API quota

**Import Errors:**
- Make sure you're running from the correct directory
- Check that `PYTHONPATH` includes the `ecomate-ai` directory
- Verify all dependencies are installed (`pip install -r ecomate-ai/requirements.txt`)

**Network Errors:**
- Check your internet connection
- Verify firewall settings allow HTTPS requests
- Try running with verbose output for debugging

### Getting Help

If you encounter issues:

1. Check the example script's error messages
2. Review the API documentation for the service being used
3. Verify your environment setup matches the requirements
4. Check the EcoMate logs for additional context

## Contributing

To contribute new examples:

1. Follow the existing code style and structure
2. Include comprehensive error handling
3. Add clear documentation and comments
4. Test with various scenarios
5. Update this README with your example

See [CONTRIBUTING.md](../CONTRIBUTING.md) for general contribution guidelines.