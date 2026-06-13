API_PREFIX = "/api"

HEALTH = f"{API_PREFIX}/health"
AUTH_ME = f"{API_PREFIX}/auth/me"
PROFILE_ME = f"{API_PREFIX}/profile/me"
USERS = f"{API_PREFIX}/users"
GROUPS = f"{API_PREFIX}/groups"
COLLECTIONS = f"{API_PREFIX}/collections"
CATEGORIES = f"{API_PREFIX}/categories"
BOARD = f"{API_PREFIX}/board"
DASHBOARD = f"{API_PREFIX}/dashboard"
ISSUES = f"{API_PREFIX}/issues"


def user_detail(user_id: int) -> str:
    return f"{USERS}/{user_id}"


def user_profile(username: str) -> str:
    return f"{USERS}/{username}/profile"


def group_detail(group_id: int) -> str:
    return f"{GROUPS}/{group_id}"


def collection_detail(collection_id: int) -> str:
    return f"{COLLECTIONS}/{collection_id}"


def category_detail(category_id: int) -> str:
    return f"{CATEGORIES}/{category_id}"


def issue_detail(issue_id: int) -> str:
    return f"{ISSUES}/{issue_id}"


def issue_archive(issue_id: int) -> str:
    return f"{issue_detail(issue_id)}/archive"


def issue_move(issue_id: int) -> str:
    return f"{issue_detail(issue_id)}/move"


def issue_comments(issue_id: int) -> str:
    return f"{issue_detail(issue_id)}/comments"


def issue_comment_detail(issue_id: int, comment_id: int) -> str:
    return f"{issue_comments(issue_id)}/{comment_id}"


def issue_attachments(issue_id: int) -> str:
    return f"{issue_detail(issue_id)}/attachments"


def issue_attachment_detail(issue_id: int, attachment_id: int) -> str:
    return f"{issue_attachments(issue_id)}/{attachment_id}"


def issue_attachment_download(issue_id: int, attachment_id: int) -> str:
    return f"{issue_attachment_detail(issue_id, attachment_id)}/download"