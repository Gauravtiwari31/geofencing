"""
Settings API endpoints
Application configuration and settings management
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from models.database import get_db
from models.models import Setting
from models.schemas import SettingResponse, SettingCreate, SettingUpdate
from api.auth import get_current_user_dependency, UserInfo

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[SettingResponse])
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Get all application settings
    
    Returns all configuration settings for the application.
    Requires authentication.
    """
    try:
        from sqlalchemy import select
        
        query = select(Setting).order_by(Setting.key)
        result = await db.execute(query)
        settings = result.scalars().all()
        
        setting_responses = [
            SettingResponse(
                key=setting.key,
                value=setting.value,
                updated_at=setting.updated_at
            )
            for setting in settings
        ]
        
        logger.info("Settings retrieved", count=len(setting_responses), user=current_user.user_id)
        return setting_responses
        
    except Exception as e:
        logger.error("Failed to get settings", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings"
        )


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Get a specific setting by key
    
    Returns the value and metadata for a specific configuration setting.
    """
    try:
        setting_value = await Setting.get_value(db, key)
        
        if setting_value is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        from sqlalchemy import select
        query = select(Setting).where(Setting.key == key)
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        setting_response = SettingResponse(
            key=setting.key,
            value=setting.value,
            updated_at=setting.updated_at
        )
        
        logger.info("Setting retrieved", key=key, user=current_user.user_id)
        return setting_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get setting", key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve setting"
        )


@router.post("/", response_model=SettingResponse)
async def create_setting(
    setting_data: SettingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Create a new setting
    
    Creates a new configuration setting with the provided key and value.
    """
    try:
        # Check if setting already exists
        existing_value = await Setting.get_value(db, setting_data.key)
        if existing_value is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Setting '{setting_data.key}' already exists"
            )
        
        # Create new setting
        setting = await Setting.set_value(db, setting_data.key, setting_data.value or "")
        await db.commit()
        await db.refresh(setting)
        
        setting_response = SettingResponse(
            key=setting.key,
            value=setting.value,
            updated_at=setting.updated_at
        )
        
        logger.info("Setting created", key=setting_data.key, user=current_user.user_id)
        return setting_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create setting", key=setting_data.key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create setting"
        )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    setting_update: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Update an existing setting
    
    Updates the value of an existing configuration setting.
    """
    try:
        # Update setting (this will create if not exists)
        setting = await Setting.set_value(db, key, setting_update.value)
        await db.commit()
        await db.refresh(setting)
        
        setting_response = SettingResponse(
            key=setting.key,
            value=setting.value,
            updated_at=setting.updated_at
        )
        
        logger.info("Setting updated", key=key, user=current_user.user_id)
        return setting_response
        
    except Exception as e:
        logger.error("Failed to update setting", key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update setting"
        )


@router.delete("/{key}")
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Delete a setting
    
    Removes a configuration setting from the system.
    """
    try:
        from sqlalchemy import select, delete
        
        # Check if setting exists
        query = select(Setting).where(Setting.key == key)
        result = await db.execute(query)
        setting = result.scalar_one_or_none()
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Delete setting
        delete_query = delete(Setting).where(Setting.key == key)
        await db.execute(delete_query)
        await db.commit()
        
        logger.info("Setting deleted", key=key, user=current_user.user_id)
        return {"message": f"Setting '{key}' deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete setting", key=key, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete setting"
        )


@router.get("/system/info")
async def get_system_info(
    current_user: UserInfo = Depends(get_current_user_dependency)
):
    """
    Get system information and status
    
    Returns general system information for monitoring and debugging.
    """
    try:
        from config import settings
        import platform
        import sys
        
        system_info = {
            "application": {
                "name": "Police SEDI",
                "version": "1.0.0",
                "debug_mode": settings.debug,
                "port": settings.port
            },
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": sys.version,
                "architecture": platform.machine()
            },
            "configuration": {
                "database_configured": bool(settings.database_url),
                "oidc_configured": bool(settings.oidc_issuer_url),
                "mod_core_configured": bool(settings.mod_core_url)
            },
            "timestamp": "2025-09-25T14:00:00Z"
        }
        
        logger.info("System info retrieved", user=current_user.user_id)
        return system_info
        
    except Exception as e:
        logger.error("Failed to get system info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )
