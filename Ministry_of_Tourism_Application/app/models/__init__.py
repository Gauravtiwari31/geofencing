# Database models - Import all models to ensure proper registration

from .tourist import Tourist, DigitalId, Device, Location, Consent
from .alert import Alert, AlertAcknowledgment, IncidentReport, AuditLog
from .geofence import Geofence

__all__ = [
    "Tourist", "DigitalId", "Device", "Location", "Consent",
    "Alert", "AlertAcknowledgment", "IncidentReport", "AuditLog", 
    "Geofence"
]
