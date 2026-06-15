from .admin import AsyncAdminResource, SyncAdminResource
from .attachments import AsyncAttachmentsResource, SyncAttachmentsResource
from .auth import AsyncAuthResource, SyncAuthResource
from .board import AsyncBoardResource, SyncBoardResource
from .comments import AsyncCommentsResource, SyncCommentsResource
from .dashboard import AsyncDashboardResource, SyncDashboardResource
from .issues import AsyncIssuesResource, SyncIssuesResource
from .profiles import AsyncProfilesResource, SyncProfilesResource
from .reference import AsyncReferenceResource, SyncReferenceResource
from .system import AsyncSystemResource, SyncSystemResource

__all__ = [
    "AsyncAdminResource",
    "AsyncAttachmentsResource",
    "AsyncAuthResource",
    "AsyncBoardResource",
    "AsyncCommentsResource",
    "AsyncDashboardResource",
    "AsyncIssuesResource",
    "AsyncProfilesResource",
    "AsyncReferenceResource",
    "AsyncSystemResource",
    "SyncAdminResource",
    "SyncAttachmentsResource",
    "SyncAuthResource",
    "SyncBoardResource",
    "SyncCommentsResource",
    "SyncDashboardResource",
    "SyncIssuesResource",
    "SyncProfilesResource",
    "SyncReferenceResource",
    "SyncSystemResource",
]
