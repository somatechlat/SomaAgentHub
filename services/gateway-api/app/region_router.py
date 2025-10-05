"""
Region-aware routing for multi-region deployments.

Routes requests to the appropriate regional backend based on:
- User location (geolocation)
- Data residency requirements
- Regional capacity/health
"""

import os
import logging
from typing import Optional, Dict
from enum import Enum
from fastapi import Request, HTTPException
from geolite2 import geolite2

logger = logging.getLogger(__name__)


class Region(str, Enum):
    """Supported AWS regions."""
    
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


class DataResidencyZone(str, Enum):
    """Data residency zones for compliance."""
    
    US = "us"
    EU = "eu"
    APAC = "apac"


# Region configuration
REGION_CONFIG = {
    Region.US_WEST_2: {
        "endpoint": os.getenv("US_WEST_2_ENDPOINT", "https://api-usw2.somaagent.io"),
        "data_zone": DataResidencyZone.US,
        "continents": ["NA", "SA"],  # North/South America
        "weight": 50,
        "enabled": True
    },
    Region.EU_WEST_1: {
        "endpoint": os.getenv("EU_WEST_1_ENDPOINT", "https://api-euw1.somaagent.io"),
        "data_zone": DataResidencyZone.EU,
        "continents": ["EU", "AF"],  # Europe, Africa
        "weight": 50,
        "enabled": True
    }
}


class RegionRouter:
    """Routes requests to appropriate regional backend."""
    
    def __init__(self):
        """Initialize region router with geolocation database."""
        self.geo_reader = geolite2.reader()
    
    def get_client_region(self, request: Request) -> Region:
        """
        Determine client's region from IP address.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Region enum for routing
        """
        # Get client IP
        client_ip = request.client.host
        
        # Check for forwarded IP (behind load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Lookup geolocation
        try:
            match = self.geo_reader.get(client_ip)
            if match and 'continent' in match:
                continent = match['continent']['code']
                
                # Route based on continent
                for region, config in REGION_CONFIG.items():
                    if continent in config['continents'] and config['enabled']:
                        logger.info(f"Routing {client_ip} ({continent}) to {region}")
                        return region
        except Exception as e:
            logger.warning(f"Geolocation lookup failed for {client_ip}: {e}")
        
        # Default to US region
        logger.info(f"Using default region for {client_ip}")
        return Region.US_WEST_2
    
    def get_region_for_user(self, user_id: str, user_metadata: Optional[Dict] = None) -> Region:
        """
        Get region for a user based on their data residency requirements.
        
        Args:
            user_id: User identifier
            user_metadata: Optional user metadata with residency info
            
        Returns:
            Region where user's data should be stored
        """
        if not user_metadata:
            return Region.US_WEST_2
        
        # Check for explicit data residency requirement
        data_zone = user_metadata.get("data_residency")
        
        if data_zone == DataResidencyZone.EU:
            return Region.EU_WEST_1
        elif data_zone == DataResidencyZone.US:
            return Region.US_WEST_2
        elif data_zone == DataResidencyZone.APAC:
            return Region.AP_SOUTHEAST_1
        
        # Default based on user's country
        country = user_metadata.get("country")
        if country in ["DE", "FR", "UK", "IT", "ES", "NL", "BE", "AT", "CH"]:
            return Region.EU_WEST_1
        
        return Region.US_WEST_2
    
    def get_endpoint(self, region: Region) -> str:
        """
        Get API endpoint URL for a region.
        
        Args:
            region: Target region
            
        Returns:
            Endpoint URL
        """
        config = REGION_CONFIG.get(region)
        if not config or not config['enabled']:
            raise HTTPException(
                status_code=503,
                detail=f"Region {region} is not available"
            )
        
        return config['endpoint']
    
    def validate_data_residency(self, user_id: str, target_region: Region) -> bool:
        """
        Validate that data can be stored in target region.
        
        Args:
            user_id: User identifier
            target_region: Proposed storage region
            
        Returns:
            True if residency requirements are met
        """
        # In production, lookup user's data residency requirements from database
        # For now, implement basic EU/US separation
        
        user_data_zone = self._get_user_data_zone(user_id)
        target_data_zone = REGION_CONFIG[target_region]['data_zone']
        
        # EU users must stay in EU
        if user_data_zone == DataResidencyZone.EU and target_data_zone != DataResidencyZone.EU:
            logger.warning(f"Data residency violation: EU user {user_id} -> {target_region}")
            return False
        
        return True
    
    def _get_user_data_zone(self, user_id: str) -> DataResidencyZone:
        """
        Get user's data residency zone.
        
        Args:
            user_id: User identifier
            
        Returns:
            DataResidencyZone enum
        """
        # In production, query user database
        # For now, default to US
        return DataResidencyZone.US
    
    def get_healthy_regions(self) -> list[Region]:
        """
        Get list of currently healthy regions.
        
        Returns:
            List of Region enums that are enabled and healthy
        """
        # In production, check health status from monitoring system
        healthy = []
        
        for region, config in REGION_CONFIG.items():
            if config['enabled']:
                # TODO: Add actual health check
                healthy.append(region)
        
        return healthy
    
    def select_region_weighted(self) -> Region:
        """
        Select a region using weighted random selection.
        
        Returns:
            Region selected based on configured weights
        """
        import random
        
        regions = []
        weights = []
        
        for region, config in REGION_CONFIG.items():
            if config['enabled']:
                regions.append(region)
                weights.append(config['weight'])
        
        if not regions:
            raise HTTPException(status_code=503, detail="No healthy regions available")
        
        return random.choices(regions, weights=weights)[0]


# Global router instance
_router: Optional[RegionRouter] = None


def get_region_router() -> RegionRouter:
    """Get or create global region router."""
    global _router
    if _router is None:
        _router = RegionRouter()
    return _router


async def route_request(request: Request, user_id: Optional[str] = None) -> str:
    """
    Route a request to the appropriate regional endpoint.
    
    Args:
        request: FastAPI request
        user_id: Optional user ID for residency-based routing
        
    Returns:
        Regional endpoint URL
    """
    router = get_region_router()
    
    if user_id:
        # Use user's data residency requirements
        region = router.get_region_for_user(user_id)
    else:
        # Use geolocation-based routing
        region = router.get_client_region(request)
    
    return router.get_endpoint(region)
