"""Geospatial service for EcoMate AI.

This module provides high-level geospatial services including site assessment,
batch processing, and logistics cost calculation.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import structlog
from pydantic import ValidationError

from .client import GeospatialClient, GeospatialAPIError
from .models import (
    AccessibilityLevel,
    BatchGeospatialRequest,
    BatchGeospatialResponse,
    GeospatialAnalysis,
    GeospatialQuery,
    GeospatialResponse,
    Location,
    LogisticsCost,
    SiteAssessment,
    TerrainType,
)

logger = structlog.get_logger(__name__)


class GeospatialService:
    """High-level geospatial service for EcoMate AI."""
    
    def __init__(self, client: Optional[GeospatialClient] = None):
        """Initialize the geospatial service.
        
        Args:
            client: GeospatialClient instance, creates default if None
        """
        self.client = client or GeospatialClient()
        logger.info("Geospatial service initialized")
    
    async def assess_site(self, location: Location, 
                         include_logistics: bool = True,
                         depot_location: Optional[Location] = None) -> SiteAssessment:
        """Perform comprehensive site assessment.
        
        Args:
            location: Site location to assess
            include_logistics: Whether to include logistics cost analysis
            depot_location: Depot location for logistics calculation
            
        Returns:
            Complete site assessment
        """
        logger.info("Starting site assessment", 
                   latitude=location.latitude, longitude=location.longitude)
        
        try:
            # Perform comprehensive geospatial analysis
            analysis = await self.client.analyze_site_comprehensive(location)
            
            # Calculate logistics cost if requested
            logistics_cost = None
            if include_logistics and depot_location:
                logistics_cost = await self.calculate_logistics_cost(
                    depot_location, location
                )
            
            # Generate overall assessment
            overall_score = self._calculate_overall_score(analysis, logistics_cost)
            
            # Determine project viability
            viable = (
                analysis.installation_feasibility and 
                analysis.accessibility != AccessibilityLevel.INACCESSIBLE and
                overall_score >= 6.0
            )
            
            # Generate summary recommendations
            summary_recommendations = self._generate_summary_recommendations(
                analysis, logistics_cost, viable
            )
            
            return SiteAssessment(
                location=location,
                geospatial_analysis=analysis,
                logistics_cost=logistics_cost,
                overall_score=overall_score,
                project_viable=viable,
                assessment_date=datetime.utcnow(),
                summary_recommendations=summary_recommendations
            )
            
        except Exception as e:
            logger.error("Site assessment failed", error=str(e))
            raise GeospatialAPIError(f"Site assessment failed: {str(e)}")
    
    async def calculate_logistics_cost(self, origin: Location, 
                                     destination: Location,
                                     equipment_weight_kg: float = 1000,
                                     crew_size: int = 4) -> LogisticsCost:
        """Calculate logistics cost for site access.
        
        Args:
            origin: Origin location (depot/warehouse)
            destination: Destination location (site)
            equipment_weight_kg: Weight of equipment to transport
            crew_size: Number of crew members
            
        Returns:
            Detailed logistics cost breakdown
        """
        try:
            # Get distance and travel time
            distance_matrix = await self.client.calculate_distance_matrix(
                origin, destination
            )
            
            if not distance_matrix:
                raise GeospatialAPIError("Could not calculate distance matrix")
            
            # Get elevation data for destination
            elevation_data = await self.client.get_elevation_google(
                [(destination.latitude, destination.longitude)]
            )
            
            # Get slope data for terrain assessment
            slope_data = await self.client.calculate_slope(
                destination.latitude, destination.longitude
            )
            
            # Base costs (example rates)
            base_fuel_cost_per_km = 0.15  # USD per km
            base_crew_cost_per_hour = 50.0  # USD per hour per person
            base_equipment_cost_per_kg_km = 0.02  # USD per kg per km
            
            # Calculate base costs
            fuel_cost = distance_matrix.distance_km * base_fuel_cost_per_km * 2  # Round trip
            crew_cost = (distance_matrix.duration_minutes / 60) * base_crew_cost_per_hour * crew_size * 2
            equipment_cost = distance_matrix.distance_km * equipment_weight_kg * base_equipment_cost_per_kg_km * 2
            
            # Apply terrain multipliers
            terrain_multiplier = 1.0
            access_difficulty_multiplier = 1.0
            
            if elevation_data and elevation_data[0].elevation_m > 1500:
                terrain_multiplier += 0.3
            if elevation_data and elevation_data[0].elevation_m > 2500:
                terrain_multiplier += 0.5
            
            if slope_data:
                if slope_data.slope_degrees > 15:
                    access_difficulty_multiplier += 0.4
                elif slope_data.slope_degrees > 8:
                    access_difficulty_multiplier += 0.2
                
                if slope_data.terrain_type == TerrainType.MOUNTAINOUS:
                    terrain_multiplier += 0.6
                elif slope_data.terrain_type == TerrainType.HILLY:
                    terrain_multiplier += 0.3
            
            # Apply multipliers
            total_multiplier = terrain_multiplier * access_difficulty_multiplier
            
            adjusted_fuel_cost = fuel_cost * total_multiplier
            adjusted_crew_cost = crew_cost * total_multiplier
            adjusted_equipment_cost = equipment_cost * total_multiplier
            
            # Calculate total cost
            total_cost = adjusted_fuel_cost + adjusted_crew_cost + adjusted_equipment_cost
            
            # Add contingency (10-30% based on terrain difficulty)
            contingency_rate = 0.1 + (total_multiplier - 1.0) * 0.2
            contingency_cost = total_cost * contingency_rate
            
            final_total = total_cost + contingency_cost
            
            return LogisticsCost(
                origin=origin,
                destination=destination,
                distance_km=distance_matrix.distance_km,
                travel_time_hours=distance_matrix.duration_minutes / 60,
                fuel_cost_usd=adjusted_fuel_cost,
                crew_cost_usd=adjusted_crew_cost,
                equipment_transport_cost_usd=adjusted_equipment_cost,
                terrain_multiplier=terrain_multiplier,
                access_difficulty_multiplier=access_difficulty_multiplier,
                contingency_cost_usd=contingency_cost,
                total_cost_usd=final_total,
                cost_breakdown={
                    "base_fuel": fuel_cost,
                    "base_crew": crew_cost,
                    "base_equipment": equipment_cost,
                    "terrain_adjustment": (total_multiplier - 1.0) * (fuel_cost + crew_cost + equipment_cost),
                    "contingency": contingency_cost
                },
                calculation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Logistics cost calculation failed", error=str(e))
            raise GeospatialAPIError(f"Logistics cost calculation failed: {str(e)}")
    
    async def process_geospatial_query(self, query: GeospatialQuery) -> GeospatialResponse:
        """Process a geospatial query request.
        
        Args:
            query: Geospatial query parameters
            
        Returns:
            Geospatial response with requested data
        """
        try:
            results = []
            
            for location in query.locations:
                # Geocode if address provided
                if location.address and not (location.latitude and location.longitude):
                    geocoded = await self.client.geocode(location.address)
                    if geocoded:
                        location = geocoded
                    else:
                        logger.warning("Geocoding failed", address=location.address)
                        continue
                
                # Perform requested analyses
                analysis_data = {}
                
                if "elevation" in query.data_types:
                    elevation_data = await self.client.get_elevation_google(
                        [(location.latitude, location.longitude)]
                    )
                    if elevation_data:
                        analysis_data["elevation"] = elevation_data[0]
                
                if "slope" in query.data_types:
                    slope_data = await self.client.calculate_slope(
                        location.latitude, location.longitude
                    )
                    if slope_data:
                        analysis_data["slope"] = slope_data
                
                if "soil" in query.data_types:
                    soil_data = await self.client.get_soil_data(
                        location.latitude, location.longitude
                    )
                    if soil_data:
                        analysis_data["soil"] = soil_data
                
                if "comprehensive" in query.data_types:
                    comprehensive = await self.client.analyze_site_comprehensive(location)
                    analysis_data["comprehensive"] = comprehensive
                
                results.append({
                    "location": location,
                    "data": analysis_data
                })
            
            return GeospatialResponse(
                query_id=query.query_id,
                results=results,
                total_locations=len(results),
                successful_locations=len([r for r in results if r["data"]]),
                processing_time_seconds=(datetime.utcnow() - query.timestamp).total_seconds(),
                response_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Geospatial query processing failed", error=str(e))
            raise GeospatialAPIError(f"Query processing failed: {str(e)}")
    
    async def process_batch_request(self, request: BatchGeospatialRequest) -> BatchGeospatialResponse:
        """Process batch geospatial requests.
        
        Args:
            request: Batch request with multiple queries
            
        Returns:
            Batch response with all results
        """
        logger.info("Processing batch geospatial request", 
                   query_count=len(request.queries))
        
        try:
            # Process queries with concurrency limit
            semaphore = asyncio.Semaphore(request.max_concurrent_requests)
            
            async def process_single_query(query: GeospatialQuery) -> GeospatialResponse:
                async with semaphore:
                    return await self.process_geospatial_query(query)
            
            # Execute all queries concurrently
            tasks = [process_single_query(query) for query in request.queries]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful and failed responses
            successful_responses = []
            failed_queries = []
            
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    failed_queries.append({
                        "query_id": request.queries[i].query_id,
                        "error": str(response)
                    })
                else:
                    successful_responses.append(response)
            
            return BatchGeospatialResponse(
                batch_id=request.batch_id,
                responses=successful_responses,
                failed_queries=failed_queries,
                total_queries=len(request.queries),
                successful_queries=len(successful_responses),
                failed_queries_count=len(failed_queries),
                processing_time_seconds=(datetime.utcnow() - request.timestamp).total_seconds(),
                response_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Batch request processing failed", error=str(e))
            raise GeospatialAPIError(f"Batch processing failed: {str(e)}")
    
    async def find_optimal_sites(self, candidate_locations: List[Location],
                               depot_location: Location,
                               max_sites: int = 5,
                               weight_accessibility: float = 0.3,
                               weight_cost: float = 0.4,
                               weight_terrain: float = 0.3) -> List[SiteAssessment]:
        """Find optimal sites from candidate locations.
        
        Args:
            candidate_locations: List of candidate site locations
            depot_location: Depot location for logistics calculation
            max_sites: Maximum number of sites to return
            weight_accessibility: Weight for accessibility score
            weight_cost: Weight for cost score
            weight_terrain: Weight for terrain score
            
        Returns:
            List of top-ranked site assessments
        """
        logger.info("Finding optimal sites", 
                   candidates=len(candidate_locations), max_sites=max_sites)
        
        try:
            # Assess all candidate sites
            assessments = []
            
            for location in candidate_locations:
                try:
                    assessment = await self.assess_site(
                        location, include_logistics=True, depot_location=depot_location
                    )
                    assessments.append(assessment)
                except Exception as e:
                    logger.warning("Site assessment failed", 
                                 location=location, error=str(e))
                    continue
            
            # Calculate composite scores
            scored_assessments = []
            
            for assessment in assessments:
                if not assessment.project_viable:
                    continue
                
                # Normalize scores (0-10 scale)
                accessibility_score = self._normalize_accessibility_score(
                    assessment.geospatial_analysis.accessibility
                )
                
                cost_score = 10.0  # Default if no logistics cost
                if assessment.logistics_cost:
                    # Invert cost (lower cost = higher score)
                    max_cost = 10000  # Assumed maximum reasonable cost
                    cost_score = max(0, 10 - (assessment.logistics_cost.total_cost_usd / max_cost) * 10)
                
                terrain_score = max(0, 10 - assessment.geospatial_analysis.terrain_difficulty_score)
                
                # Calculate weighted composite score
                composite_score = (
                    accessibility_score * weight_accessibility +
                    cost_score * weight_cost +
                    terrain_score * weight_terrain
                )
                
                scored_assessments.append((assessment, composite_score))
            
            # Sort by composite score (descending)
            scored_assessments.sort(key=lambda x: x[1], reverse=True)
            
            # Return top sites
            return [assessment for assessment, _ in scored_assessments[:max_sites]]
            
        except Exception as e:
            logger.error("Optimal site finding failed", error=str(e))
            raise GeospatialAPIError(f"Optimal site finding failed: {str(e)}")
    
    def _calculate_overall_score(self, analysis: GeospatialAnalysis, 
                               logistics_cost: Optional[LogisticsCost]) -> float:
        """Calculate overall site score (0-10)."""
        base_score = 10.0 - analysis.terrain_difficulty_score
        
        # Adjust for accessibility
        accessibility_adjustment = {
            AccessibilityLevel.EXCELLENT: 0,
            AccessibilityLevel.GOOD: -0.5,
            AccessibilityLevel.MODERATE: -1.0,
            AccessibilityLevel.DIFFICULT: -2.0,
            AccessibilityLevel.INACCESSIBLE: -5.0
        }
        
        base_score += accessibility_adjustment.get(analysis.accessibility, -2.0)
        
        # Adjust for logistics cost
        if logistics_cost:
            if logistics_cost.total_cost_usd > 5000:
                base_score -= 2.0
            elif logistics_cost.total_cost_usd > 2000:
                base_score -= 1.0
        
        return max(0.0, min(10.0, base_score))
    
    def _normalize_accessibility_score(self, accessibility: AccessibilityLevel) -> float:
        """Convert accessibility level to numeric score (0-10)."""
        scores = {
            AccessibilityLevel.EXCELLENT: 10.0,
            AccessibilityLevel.GOOD: 8.0,
            AccessibilityLevel.MODERATE: 6.0,
            AccessibilityLevel.DIFFICULT: 4.0,
            AccessibilityLevel.INACCESSIBLE: 0.0
        }
        return scores.get(accessibility, 5.0)
    
    def _generate_summary_recommendations(self, analysis: GeospatialAnalysis,
                                        logistics_cost: Optional[LogisticsCost],
                                        viable: bool) -> List[str]:
        """Generate summary recommendations for site."""
        recommendations = []
        
        if not viable:
            recommendations.append("Site not recommended due to accessibility or terrain constraints")
            return recommendations
        
        if analysis.accessibility == AccessibilityLevel.EXCELLENT:
            recommendations.append("Excellent site accessibility - standard equipment sufficient")
        elif analysis.accessibility == AccessibilityLevel.DIFFICULT:
            recommendations.append("Specialized access equipment required")
        
        if logistics_cost and logistics_cost.total_cost_usd > 3000:
            recommendations.append("High logistics cost - consider bulk delivery or local sourcing")
        
        if analysis.terrain_difficulty_score < 3:
            recommendations.append("Favorable terrain conditions for installation")
        elif analysis.terrain_difficulty_score > 6:
            recommendations.append("Challenging terrain - detailed site survey recommended")
        
        if analysis.elevation and analysis.elevation.elevation_m > 2000:
            recommendations.append("High altitude site - consider equipment specifications")
        
        return recommendations