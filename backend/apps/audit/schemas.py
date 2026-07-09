import uuid
from datetime import datetime
from typing import Optional, Any
from ninja import Schema


class AuditLogOut(Schema):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    action: str
    table_name: str
    record_id: Optional[str] = None
    old_values: Optional[Any] = None
    new_values: Optional[Any] = None
    ip_address: Optional[str] = None
    created_at: datetime
