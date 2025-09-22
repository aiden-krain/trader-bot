import os
from dotenv import load_dotenv
import requests
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

# Import structured response model
from models import NotificationResult

load_dotenv(override=True)

pushover_user = os.getenv("PUSHOVER_USER")
pushover_token = os.getenv("PUSHOVER_TOKEN")
pushover_url = "https://api.pushover.net/1/messages.json"


mcp = FastMCP("push_server")


class PushModelArgs(BaseModel):
    message: str = Field(description="A brief message to push")


@mcp.tool()
def push(args: PushModelArgs) -> NotificationResult:
    """Send a push notification with this brief message"""
    try:
        print(f"Push: {args.message}")
        payload = {"user": pushover_user, "token": pushover_token, "message": args.message}
        response = requests.post(pushover_url, data=payload)
        
        if response.status_code == 200:
            return NotificationResult(
                success=True,
                message="Push notification sent successfully",
                service="pushover",
                timestamp=None
            )
        else:
            return NotificationResult(
                success=False,
                message="Failed to send push notification",
                service="pushover",
                error=f"HTTP {response.status_code}: {response.text}"
            )
    except Exception as e:
        return NotificationResult(
            success=False,
            message="Push notification failed",
            service="pushover",
            error=str(e)
        )


if __name__ == "__main__":
    mcp.run(transport="stdio")
