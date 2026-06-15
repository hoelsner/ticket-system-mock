from __future__ import annotations


class SyncCommentsResource:
    def __init__(self, issues_resource):
        self._issues = issues_resource

    def add(self, issue_id: int, *, files=None, **payload):
        return self._issues.add_comment(issue_id, files=files, **payload)

    def update(self, issue_id: int, comment_id: int, **payload):
        return self._issues.update_comment(issue_id, comment_id, **payload)


class AsyncCommentsResource:
    def __init__(self, issues_resource):
        self._issues = issues_resource

    async def add(self, issue_id: int, *, files=None, **payload):
        return await self._issues.add_comment(issue_id, files=files, **payload)

    async def update(self, issue_id: int, comment_id: int, **payload):
        return await self._issues.update_comment(issue_id, comment_id, **payload)
