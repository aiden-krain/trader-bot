"""
Pydantic models for notification-related MCP tool responses.
"""

from pydantic import BaseModel, Field
from typing import Optional

class NotificationResult(BaseModel):
    """Model for push notification result"""
    success: bool = Field(description="Whether notification was sent successfully")
    message: str = Field(description="Notification result message")
    service: str = Field(default="pushover", description="Notification service used")
    timestamp: Optional[str] = Field(None, description="Notification timestamp")
    error: Optional[str] = Field(None, description="Error message if notification failed")
