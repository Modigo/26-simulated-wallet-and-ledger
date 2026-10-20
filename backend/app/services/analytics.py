from app.models.models import AnalyticsEvent
def record(db, event_type, user_id=None, session_id=None, props=None):
    # Analytics must never break money movement: caller wraps in try/except where needed.
    db.add(AnalyticsEvent(event_type=event_type,user_id=user_id,session_id=session_id,event_properties=props or {}))
