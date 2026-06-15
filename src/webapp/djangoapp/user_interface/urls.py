from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve

from .views import (
    AttachmentSuggestionView,
    BoardColumnStateView,
    BoardEventStreamView,
    BoardFragmentView,
    DashboardView,
    DraftAttachmentSuggestionView,
    DraftAttachmentUploadView,
    HomeView,
    IntegrationsView,
    IssueArchiveView,
    IssueAttachmentDeleteView,
    IssueBoardMoveView,
    IssueCommentCreateView,
    IssueCreateView,
    IssueDescriptionUpdateView,
    IssueDetailView,
    IssueMarkdownPreviewView,
    IssueSuggestionView,
    IssueUpdateView,
    MarkdownPreviewView,
    N8nNodePackageDownloadView,
    PythonSdkPackageDownloadView,
    UserProfileDetailView,
    UserProfileSettingsView,
    UserSuggestionView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("board/fragment/", BoardFragmentView.as_view(), name="board-fragment"),
    path("board/events/", BoardEventStreamView.as_view(), name="board-events"),
    path("board/column-state/", BoardColumnStateView.as_view(), name="board-column-state"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("integrations/", IntegrationsView.as_view(), name="integrations"),
    path("integrations/n8n-node/download/", N8nNodePackageDownloadView.as_view(), name="integrations-n8n-download"),
    path(
        "integrations/python-sdk/download/",
        PythonSdkPackageDownloadView.as_view(),
        name="integrations-python-sdk-download",
    ),
    path("profile/", UserProfileSettingsView.as_view(), name="profile-settings"),
    path("users/<str:username>/", UserProfileDetailView.as_view(), name="user-profile-detail"),
    path("issues/create/", IssueCreateView.as_view(), name="issue-create"),
    path("issues/<int:pk>/", IssueDetailView.as_view(), name="issue-detail"),
    path("issues/<int:pk>/description/", IssueDescriptionUpdateView.as_view(), name="issue-description-update"),
    path("issues/<int:pk>/edit/", IssueUpdateView.as_view(), name="issue-update"),
    path("issues/<int:pk>/move/", IssueBoardMoveView.as_view(), name="issue-move"),
    path("issues/<int:pk>/archive/", IssueArchiveView.as_view(), name="issue-archive"),
    path(
        "issues/<int:pk>/attachments/<int:attachment_pk>/delete/",
        IssueAttachmentDeleteView.as_view(),
        name="issue-attachment-delete",
    ),
    path("issues/<int:pk>/comments/add/", IssueCommentCreateView.as_view(), name="issue-comment-create"),
    path("issues/<int:pk>/markdown-preview/", IssueMarkdownPreviewView.as_view(), name="issue-markdown-preview"),
    path("issues/<int:pk>/editor/attachments/", AttachmentSuggestionView.as_view(), name="attachment-suggestions"),
    path("editor/attachments/drafts/", DraftAttachmentSuggestionView.as_view(), name="draft-attachment-suggestions"),
    path("editor/attachments/upload/", DraftAttachmentUploadView.as_view(), name="draft-attachment-upload"),
    path("editor/markdown-preview/", MarkdownPreviewView.as_view(), name="markdown-preview"),
    path("editor/users/", UserSuggestionView.as_view(), name="user-suggestions"),
    path("editor/issues/", IssueSuggestionView.as_view(), name="issue-suggestions"),
]

urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
