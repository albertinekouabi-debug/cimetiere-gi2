from typing import List
from django.shortcuts import get_object_or_404
from ninja import Router
from apps.accounts.auth import jwt_auth
from .models import Notification
from .schemas import NotificationOut

router = Router(tags=["Notifications"], auth=jwt_auth)


@router.get("/", response=List[NotificationOut])
def list_notifications(request):
    return list(Notification.objects.filter(user=request.auth)[:50])


@router.get("/unread-count")
def unread_count(request):
    return {"count": Notification.objects.filter(user=request.auth, is_read=False).count()}


@router.post("/{notification_id}/read", response=NotificationOut)
def mark_read(request, notification_id: str):
    notif = get_object_or_404(Notification, id=notification_id, user=request.auth)
    notif.is_read = True
    notif.save(update_fields=["is_read", "updated_at"])
    return notif


@router.post("/read-all")
def mark_all_read(request):
    Notification.objects.filter(user=request.auth, is_read=False).update(is_read=True)
    return {"detail": "Toutes les notifications ont été marquées comme lues."}
