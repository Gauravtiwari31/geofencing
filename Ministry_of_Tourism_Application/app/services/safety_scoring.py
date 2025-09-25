"""
Safety scoring algorithm for tourists
"""
import logging
from typing import Dict, Any, List
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def calculate_safety_score(tourist_data: Dict[str, Any]) -> int:
    """
    Calculate safety score (0-100) based on tourist telemetry and context.
    
    Args:
        tourist_data: Dictionary containing:
            - in_red_zone: bool
            - red_zone_distance_m: float or None
            - health: dict with heart_rate, fall_detected, battery
            - sos: dict with active flag
            - violations: list of geofence violations
    
    Returns:
        Safety score between 0 and 100
    """
    try:
        base_score = settings.default_safety_score  # 100
        
        # SOS Active - Immediate critical safety score
        sos_data = tourist_data.get("sos", {})
        if sos_data.get("active", False):
            logger.warning("SOS active - setting safety score to 0")
            return 0
        
        # Red Zone Penalties
        if tourist_data.get("in_red_zone", False):
            penalty = settings.red_zone_penalty  # 40 points
            base_score -= penalty
            logger.info(f"In red zone - penalty: {penalty}")
        
        # Distance-based reduction for proximity to red zones
        red_zone_distance = tourist_data.get("red_zone_distance_m")
        if red_zone_distance is not None and red_zone_distance < 500:
            # Linear penalty: 30 points at 0m, reducing to 0 at 500m
            distance_penalty = max(0, 30 - (red_zone_distance / 500 * 30))
            base_score -= distance_penalty
            logger.info(f"Near red zone ({red_zone_distance}m) - penalty: {distance_penalty:.1f}")
        
        # Health indicators
        health_data = tourist_data.get("health", {})
        
        # Heart rate anomalies
        heart_rate = health_data.get("heart_rate")
        if heart_rate is not None:
            if heart_rate > 120 or heart_rate < 50:
                base_score -= 15
                logger.info(f"Abnormal heart rate ({heart_rate}) - penalty: 15")
            elif heart_rate > 100 or heart_rate < 60:
                base_score -= 5
                logger.info(f"Elevated heart rate ({heart_rate}) - penalty: 5")
        
        # Fall detection
        if health_data.get("fall_detected", False):
            base_score -= 25
            logger.warning("Fall detected - penalty: 25")
        
        # Battery level
        battery = health_data.get("battery", 1.0)
        if battery < 0.1:
            base_score -= 20
            logger.warning(f"Critical battery ({battery*100:.1f}%) - penalty: 20")
        elif battery < 0.2:
            base_score -= 15
            logger.info(f"Low battery ({battery*100:.1f}%) - penalty: 15")
        elif battery < 0.3:
            base_score -= 5
            logger.info(f"Medium battery ({battery*100:.1f}%) - penalty: 5")
        
        # Geofence violations
        violations = tourist_data.get("violations", [])
        for violation in violations:
            severity = violation.get("severity", 1)
            zone_type = violation.get("zone_type", "unknown")
            
            if zone_type == "red_zone":
                penalty = min(40, severity * 8)
            elif zone_type == "restricted":
                penalty = min(25, severity * 5)
            elif zone_type == "caution":
                penalty = min(10, severity * 2)
            else:
                penalty = severity
            
            base_score -= penalty
            logger.info(f"Geofence violation ({zone_type}, severity {severity}) - penalty: {penalty}")
        
        # Environmental factors (can be extended)
        # Time of day, weather, crowd density, etc.
        
        # Clamp score to valid range
        final_score = max(0, min(100, int(base_score)))
        
        logger.info(f"Final safety score: {final_score}")
        return final_score
        
    except Exception as e:
        logger.error(f"Error calculating safety score: {str(e)}")
        # Return a conservative score on error
        return 50


def get_safety_level(score: int) -> str:
    """
    Get textual safety level based on score.
    
    Args:
        score: Safety score (0-100)
    
    Returns:
        Safety level string
    """
    if score >= 90:
        return "EXCELLENT"
    elif score >= 75:
        return "GOOD"
    elif score >= 50:
        return "MODERATE"
    elif score >= 25:
        return "POOR"
    else:
        return "CRITICAL"


def get_safety_recommendations(tourist_data: Dict[str, Any], score: int) -> List[str]:
    """
    Get safety recommendations based on tourist data and score.
    
    Args:
        tourist_data: Tourist telemetry data
        score: Current safety score
    
    Returns:
        List of safety recommendations
    """
    recommendations = []
    
    try:
        # SOS specific
        if tourist_data.get("sos", {}).get("active", False):
            recommendations.extend([
                "Emergency services have been notified",
                "Stay calm and wait for assistance",
                "Try to move to a safe, visible location if possible"
            ])
            return recommendations
        
        # Red zone warnings
        if tourist_data.get("in_red_zone", False):
            recommendations.append("Exit the restricted area immediately for your safety")
        
        red_zone_distance = tourist_data.get("red_zone_distance_m")
        if red_zone_distance is not None and red_zone_distance < 200:
            recommendations.append("You are very close to a restricted area - maintain safe distance")
        elif red_zone_distance is not None and red_zone_distance < 500:
            recommendations.append("Approaching restricted area - be aware of your surroundings")
        
        # Health recommendations
        health_data = tourist_data.get("health", {})
        
        if health_data.get("fall_detected", False):
            recommendations.extend([
                "Fall detected - check for injuries",
                "If you need help, activate SOS immediately"
            ])
        
        heart_rate = health_data.get("heart_rate")
        if heart_rate and heart_rate > 120:
            recommendations.extend([
                "High heart rate detected - take a rest",
                "Find shade and hydrate if possible"
            ])
        
        battery = health_data.get("battery", 1.0)
        if battery < 0.2:
            recommendations.append("Device battery critical - charge immediately")
        elif battery < 0.4:
            recommendations.append("Device battery low - find charging option soon")
        
        # Score-based recommendations
        if score < 50:
            recommendations.extend([
                "Multiple safety concerns detected",
                "Consider returning to a safe area",
                "Stay alert and follow local guidelines"
            ])
        elif score < 75:
            recommendations.extend([
                "Be cautious and aware of your surroundings",
                "Follow safety guidelines and stay connected"
            ])
        
        # General safety tips
        if len(recommendations) == 0:
            recommendations.extend([
                "Stay on marked paths and follow local guidelines",
                "Keep your device charged and connected",
                "Be aware of weather and environmental conditions"
            ])
        
        return recommendations[:5]  # Limit to 5 recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        return ["Stay safe and follow local guidelines"]


def calculate_risk_factors(tourist_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate detailed risk factors for analytics.
    
    Args:
        tourist_data: Tourist telemetry data
    
    Returns:
        Dictionary with risk factor details
    """
    risk_factors = {
        "location_risk": 0,
        "health_risk": 0,
        "device_risk": 0,
        "environmental_risk": 0,
        "total_risk": 0
    }
    
    try:
        # Location risk
        if tourist_data.get("in_red_zone", False):
            risk_factors["location_risk"] += 40
        
        red_zone_distance = tourist_data.get("red_zone_distance_m")
        if red_zone_distance is not None and red_zone_distance < 500:
            risk_factors["location_risk"] += (500 - red_zone_distance) / 500 * 30
        
        # Health risk
        health_data = tourist_data.get("health", {})
        
        if health_data.get("fall_detected", False):
            risk_factors["health_risk"] += 25
        
        heart_rate = health_data.get("heart_rate")
        if heart_rate:
            if heart_rate > 120 or heart_rate < 50:
                risk_factors["health_risk"] += 15
            elif heart_rate > 100 or heart_rate < 60:
                risk_factors["health_risk"] += 5
        
        # Device risk
        battery = health_data.get("battery", 1.0)
        if battery < 0.1:
            risk_factors["device_risk"] += 20
        elif battery < 0.2:
            risk_factors["device_risk"] += 15
        elif battery < 0.3:
            risk_factors["device_risk"] += 5
        
        # Calculate total risk
        risk_factors["total_risk"] = sum([
            risk_factors["location_risk"],
            risk_factors["health_risk"],
            risk_factors["device_risk"],
            risk_factors["environmental_risk"]
        ])
        
        # Normalize to 0-100 scale
        for key in risk_factors:
            risk_factors[key] = min(100, max(0, int(risk_factors[key])))
        
        return risk_factors
        
    except Exception as e:
        logger.error(f"Error calculating risk factors: {str(e)}")
        return risk_factors
