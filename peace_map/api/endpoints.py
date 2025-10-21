"""
API endpoints for Peace Map
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, File, UploadFile
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from .models import Event, RiskIndex, Supplier, Alert
from .validation import (
    EventCreate, EventUpdate, EventFilters, EventType, EventStatus,
    SupplierCreate, SupplierUpdate, SupplierFilters,
    AlertCreate, AlertUpdate, AlertFilters, AlertStatus,
    PaginationParams, DateRangeParams, RiskIndexFilters, RiskLevel
)
from .auth import require_auth, require_write_permission, require_read_permission, get_permission_checker
from .errors import NotFoundError, ValidationError, ConflictError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# Event endpoints
@router.get("/projects/{project_id}/events", response_model=Dict[str, Any])
async def list_events(
    project_id: int = Path(..., description="Project ID"),
    filters: EventFilters = Depends(),
    pagination: PaginationParams = Depends(),
    date_range: DateRangeParams = Depends(),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """List events for a project with filtering and pagination"""
    
    try:
        # Build query
        query = Event.query.filter_by(project_id=project_id)
        
        # Apply filters
        if filters.event_type:
            query = query.filter_by(event_type=filters.event_type.value)
        
        if filters.status:
            query = query.filter_by(status=filters.status.value)
        
        if filters.source_confidence:
            query = query.filter(Event.source_confidence >= filters.source_confidence)
        
        if filters.keywords:
            for keyword in filters.keywords:
                query = query.filter(Event.title.contains(keyword) | Event.description.contains(keyword))
        
        if filters.sentiment:
            query = query.filter_by(sentiment=filters.sentiment)
        
        # Apply date range
        if date_range.start_date:
            query = query.filter(Event.published_at >= date_range.start_date)
        
        if date_range.end_date:
            query = query.filter(Event.published_at <= date_range.end_date)
        
        # Apply pagination
        total = query.count()
        events = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size).all()
        
        return {
            "success": True,
            "data": [event.to_dict() for event in events],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
                "pages": (total + pagination.size - 1) // pagination.size
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/projects/{project_id}/events/{event_id}", response_model=Dict[str, Any])
async def get_event(
    project_id: int = Path(..., description="Project ID"),
    event_id: int = Path(..., description="Event ID"),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """Get a specific event"""
    
    try:
        event = Event.query.filter_by(id=event_id, project_id=project_id).first()
        if not event:
            raise NotFoundError("Event not found")
        
        return {
            "success": True,
            "data": event.to_dict()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/projects/{project_id}/events", response_model=Dict[str, Any])
async def create_event(
    project_id: int = Path(..., description="Project ID"),
    event_data: EventCreate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Create a new event"""
    
    try:
        # Create event
        event = Event(
            project_id=project_id,
            title=event_data.title,
            description=event_data.description,
            event_type=event_data.event_type.value,
            location=event_data.location,
            latitude=event_data.latitude,
            longitude=event_data.longitude,
            source=event_data.source,
            source_confidence=event_data.source_confidence,
            published_at=event_data.published_at or datetime.utcnow(),
            tags=event_data.tags or []
        )
        
        # Save to database
        event.save()
        
        return {
            "success": True,
            "data": event.to_dict(),
            "message": "Event created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/projects/{project_id}/events/{event_id}", response_model=Dict[str, Any])
async def update_event(
    project_id: int = Path(..., description="Project ID"),
    event_id: int = Path(..., description="Event ID"),
    event_data: EventUpdate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Update an event"""
    
    try:
        event = Event.query.filter_by(id=event_id, project_id=project_id).first()
        if not event:
            raise NotFoundError("Event not found")
        
        # Update fields
        if event_data.title is not None:
            event.title = event_data.title
        if event_data.description is not None:
            event.description = event_data.description
        if event_data.event_type is not None:
            event.event_type = event_data.event_type.value
        if event_data.location is not None:
            event.location = event_data.location
        if event_data.latitude is not None:
            event.latitude = event_data.latitude
        if event_data.longitude is not None:
            event.longitude = event_data.longitude
        if event_data.source is not None:
            event.source = event_data.source
        if event_data.source_confidence is not None:
            event.source_confidence = event_data.source_confidence
        if event_data.published_at is not None:
            event.published_at = event_data.published_at
        if event_data.tags is not None:
            event.tags = event_data.tags
        
        # Save changes
        event.save()
        
        return {
            "success": True,
            "data": event.to_dict(),
            "message": "Event updated successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/projects/{project_id}/events/{event_id}", response_model=Dict[str, Any])
async def delete_event(
    project_id: int = Path(..., description="Project ID"),
    event_id: int = Path(..., description="Event ID"),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Delete an event"""
    
    try:
        event = Event.query.filter_by(id=event_id, project_id=project_id).first()
        if not event:
            raise NotFoundError("Event not found")
        
        # Delete event
        event.delete()
        
        return {
            "success": True,
            "message": "Event deleted successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Risk index endpoints
@router.get("/risk-index", response_model=Dict[str, Any])
async def get_risk_index(
    filters: RiskIndexFilters = Depends(),
    pagination: PaginationParams = Depends(),
    date_range: DateRangeParams = Depends(),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """Get risk index data with filtering and pagination"""
    
    try:
        # Build query
        query = RiskIndex.query
        
        # Apply filters
        if filters.region:
            query = query.filter_by(region=filters.region)
        
        if filters.risk_level:
            query = query.filter_by(risk_level=filters.risk_level.value)
        
        if filters.min_score:
            query = query.filter(RiskIndex.composite_score >= filters.min_score)
        
        if filters.max_score:
            query = query.filter(RiskIndex.composite_score <= filters.max_score)
        
        # Apply date range
        if date_range.start_date:
            query = query.filter(RiskIndex.date >= date_range.start_date)
        
        if date_range.end_date:
            query = query.filter(RiskIndex.date <= date_range.end_date)
        
        # Apply pagination
        total = query.count()
        risk_indices = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size).all()
        
        return {
            "success": True,
            "data": [risk_index.to_dict() for risk_index in risk_indices],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
                "pages": (total + pagination.size - 1) // pagination.size
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting risk index: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Supplier endpoints
@router.get("/suppliers", response_model=Dict[str, Any])
async def list_suppliers(
    filters: SupplierFilters = Depends(),
    pagination: PaginationParams = Depends(),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """List suppliers with filtering and pagination"""
    
    try:
        # Build query
        query = Supplier.query
        
        # Apply filters
        if filters.name:
            query = query.filter(Supplier.name.contains(filters.name))
        
        if filters.location:
            query = query.filter(Supplier.location.contains(filters.location))
        
        if filters.risk_level:
            query = query.filter_by(risk_level=filters.risk_level.value)
        
        if filters.min_risk_score:
            query = query.filter(Supplier.risk_score >= filters.min_risk_score)
        
        if filters.max_risk_score:
            query = query.filter(Supplier.risk_score <= filters.max_risk_score)
        
        # Apply pagination
        total = query.count()
        suppliers = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size).all()
        
        return {
            "success": True,
            "data": [supplier.to_dict() for supplier in suppliers],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
                "pages": (total + pagination.size - 1) // pagination.size
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/suppliers/{supplier_id}", response_model=Dict[str, Any])
async def get_supplier(
    supplier_id: int = Path(..., description="Supplier ID"),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """Get a specific supplier"""
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        return {
            "success": True,
            "data": supplier.to_dict()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/suppliers", response_model=Dict[str, Any])
async def create_supplier(
    supplier_data: SupplierCreate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Create a new supplier"""
    
    try:
        # Create supplier
        supplier = Supplier(
            name=supplier_data.name,
            location=supplier_data.location,
            latitude=supplier_data.latitude,
            longitude=supplier_data.longitude,
            contact_email=supplier_data.contact_email,
            contact_phone=supplier_data.contact_phone,
            website=supplier_data.website,
            description=supplier_data.description,
            tags=supplier_data.tags or []
        )
        
        # Save to database
        supplier.save()
        
        return {
            "success": True,
            "data": supplier.to_dict(),
            "message": "Supplier created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/suppliers/{supplier_id}", response_model=Dict[str, Any])
async def update_supplier(
    supplier_id: int = Path(..., description="Supplier ID"),
    supplier_data: SupplierUpdate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Update a supplier"""
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        # Update fields
        if supplier_data.name is not None:
            supplier.name = supplier_data.name
        if supplier_data.location is not None:
            supplier.location = supplier_data.location
        if supplier_data.latitude is not None:
            supplier.latitude = supplier_data.latitude
        if supplier_data.longitude is not None:
            supplier.longitude = supplier_data.longitude
        if supplier_data.contact_email is not None:
            supplier.contact_email = supplier_data.contact_email
        if supplier_data.contact_phone is not None:
            supplier.contact_phone = supplier_data.contact_phone
        if supplier_data.website is not None:
            supplier.website = supplier_data.website
        if supplier_data.description is not None:
            supplier.description = supplier_data.description
        if supplier_data.tags is not None:
            supplier.tags = supplier_data.tags
        
        # Save changes
        supplier.save()
        
        return {
            "success": True,
            "data": supplier.to_dict(),
            "message": "Supplier updated successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/suppliers/{supplier_id}", response_model=Dict[str, Any])
async def delete_supplier(
    supplier_id: int = Path(..., description="Supplier ID"),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Delete a supplier"""
    
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        # Delete supplier
        supplier.delete()
        
        return {
            "success": True,
            "message": "Supplier deleted successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting supplier: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/suppliers/upload", response_model=Dict[str, Any])
async def upload_suppliers(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Upload suppliers from CSV file"""
    
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise ValidationError("File must be a CSV file")
        
        # Read file content
        content = await file.read()
        
        # Process CSV (this would be implemented in the supply chain manager)
        # For now, return a placeholder response
        return {
            "success": True,
            "message": "Suppliers uploaded successfully",
            "data": {
                "filename": file.filename,
                "size": len(content)
            }
        }
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Error uploading suppliers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Alert endpoints
@router.get("/alerts", response_model=Dict[str, Any])
async def list_alerts(
    filters: AlertFilters = Depends(),
    pagination: PaginationParams = Depends(),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """List alerts with filtering and pagination"""
    
    try:
        # Build query
        query = Alert.query
        
        # Apply filters
        if filters.status:
            query = query.filter_by(status=filters.status.value)
        
        if filters.risk_level:
            query = query.filter_by(risk_level=filters.risk_level.value)
        
        if filters.supplier_id:
            query = query.filter_by(supplier_id=filters.supplier_id)
        
        if filters.min_risk_score:
            query = query.filter(Alert.risk_score >= filters.min_risk_score)
        
        if filters.max_risk_score:
            query = query.filter(Alert.risk_score <= filters.max_risk_score)
        
        # Apply pagination
        total = query.count()
        alerts = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size).all()
        
        return {
            "success": True,
            "data": [alert.to_dict() for alert in alerts],
            "pagination": {
                "page": pagination.page,
                "size": pagination.size,
                "total": total,
                "pages": (total + pagination.size - 1) // pagination.size
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/alerts/{alert_id}", response_model=Dict[str, Any])
async def get_alert(
    alert_id: int = Path(..., description="Alert ID"),
    user: Dict[str, Any] = Depends(require_read_permission)
):
    """Get a specific alert"""
    
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        
        return {
            "success": True,
            "data": alert.to_dict()
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/alerts", response_model=Dict[str, Any])
async def create_alert(
    alert_data: AlertCreate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Create a new alert"""
    
    try:
        # Verify supplier exists
        supplier = Supplier.query.get(alert_data.supplier_id)
        if not supplier:
            raise NotFoundError("Supplier not found")
        
        # Create alert
        alert = Alert(
            supplier_id=alert_data.supplier_id,
            risk_threshold=alert_data.risk_threshold,
            notification_email=alert_data.notification_email,
            notification_phone=alert_data.notification_phone,
            description=alert_data.description,
            tags=alert_data.tags or []
        )
        
        # Save to database
        alert.save()
        
        return {
            "success": True,
            "data": alert.to_dict(),
            "message": "Alert created successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/alerts/{alert_id}", response_model=Dict[str, Any])
async def update_alert(
    alert_id: int = Path(..., description="Alert ID"),
    alert_data: AlertUpdate = Body(...),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Update an alert"""
    
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        
        # Update fields
        if alert_data.risk_threshold is not None:
            alert.risk_threshold = alert_data.risk_threshold
        if alert_data.notification_email is not None:
            alert.notification_email = alert_data.notification_email
        if alert_data.notification_phone is not None:
            alert.notification_phone = alert_data.notification_phone
        if alert_data.description is not None:
            alert.description = alert_data.description
        if alert_data.tags is not None:
            alert.tags = alert_data.tags
        
        # Save changes
        alert.save()
        
        return {
            "success": True,
            "data": alert.to_dict(),
            "message": "Alert updated successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error updating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/alerts/{alert_id}", response_model=Dict[str, Any])
async def delete_alert(
    alert_id: int = Path(..., description="Alert ID"),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Delete an alert"""
    
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        
        # Delete alert
        alert.delete()
        
        return {
            "success": True,
            "message": "Alert deleted successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/alerts/{alert_id}/acknowledge", response_model=Dict[str, Any])
async def acknowledge_alert(
    alert_id: int = Path(..., description="Alert ID"),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Acknowledge an alert"""
    
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        
        # Update status
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.save()
        
        return {
            "success": True,
            "data": alert.to_dict(),
            "message": "Alert acknowledged successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/alerts/{alert_id}/resolve", response_model=Dict[str, Any])
async def resolve_alert(
    alert_id: int = Path(..., description="Alert ID"),
    user: Dict[str, Any] = Depends(require_write_permission)
):
    """Resolve an alert"""
    
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            raise NotFoundError("Alert not found")
        
        # Update status
        alert.status = AlertStatus.RESOLVED.value
        alert.save()
        
        return {
            "success": True,
            "data": alert.to_dict(),
            "message": "Alert resolved successfully"
        }
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
