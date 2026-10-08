"""
Route Optimization Module using TSP/Greedy Heuristics.
"""
from typing import List
from sqlalchemy.orm import Session
from app.models import SmartBin, SensorReading, CollectionRoute, RouteStatus
from geopy.distance import geodesic
import json

def get_bins_needing_collection(db: Session, threshold_fill: float = 75.0, temp_warning: float = 40.0) -> List[SmartBin]:
    """
    Identify bins that require collection based on fill level or high temperature.
    """
    bins = db.query(SmartBin).filter(SmartBin.status == 'active').all()
    target_bins = []
    
    for b in bins:
        latest = db.query(SensorReading).filter(SensorReading.bin_id == b.id).order_by(SensorReading.timestamp.desc()).first()
        if latest:
            if latest.fill_level >= threshold_fill or latest.temperature >= temp_warning:
                target_bins.append(b)
                
    return target_bins

def optimize_route(db: Session, route_name: str, zone: str = None, depot_coords: tuple = (13.0, 80.2)) -> CollectionRoute:
    """
    Generate an optimized route using a greedy Nearest Neighbor heuristic.
    Starts at depot_coords, visits all targeted bins, and returns.
    """
    bins = get_bins_needing_collection(db)
    if zone:
        bins = [b for b in bins if b.zone == zone]
        
    if not bins:
        return None
        
    unvisited = bins.copy()
    current_location = depot_coords
    ordered_bin_ids = []
    total_distance = 0.0
    
    while unvisited:
        # Find nearest unvisited bin
        nearest_bin = None
        min_dist = float('inf')
        
        for b in unvisited:
            dist = geodesic(current_location, (b.location_lat, b.location_lon)).kilometers
            if dist < min_dist:
                min_dist = dist
                nearest_bin = b
                
        ordered_bin_ids.append(nearest_bin.bin_id)
        total_distance += min_dist
        current_location = (nearest_bin.location_lat, nearest_bin.location_lon)
        unvisited.remove(nearest_bin)
        
    # Return to depot
    total_distance += geodesic(current_location, depot_coords).kilometers
    
    # Create Route record
    route = CollectionRoute(
        route_name=route_name,
        zone=zone,
        bin_sequence=json.dumps(ordered_bin_ids),
        total_distance_km=round(total_distance, 2),
        estimated_time_min=round(total_distance * 2.5), # Rough estimate 2.5 min per km
        status=RouteStatus.PENDING,
        optimized=True
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return route
