import uuid
from datetime import datetime
from typing import Optional
from ninja import Schema


class NotificationOut(Schema):
    id: uuid.UUID
    type: str
    titre: str
    message: str
    is_read: bool
    reference_id: Optional[str] = None
    created_at: datetime
