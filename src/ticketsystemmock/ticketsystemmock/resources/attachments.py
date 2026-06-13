from __future__ import annotations


class SyncAttachmentsResource:
    def __init__(self, issues_resource):
        self._issues = issues_resource

    def add(self, issue_id: int, *, files=None, **payload):
        return self._issues.add_attachment(issue_id, files=files, **payload)

    def update(self, issue_id: int, attachment_id: int, *, files=None, **payload):
        return self._issues.update_attachment(issue_id, attachment_id, files=files, **payload)

    def delete(self, issue_id: int, attachment_id: int):
        return self._issues.delete_attachment(issue_id, attachment_id)

    def download(self, issue_id: int, attachment_id: int) -> bytes:
        return self._issues.download_attachment(issue_id, attachment_id)


class AsyncAttachmentsResource:
    def __init__(self, issues_resource):
        self._issues = issues_resource

    async def add(self, issue_id: int, *, files=None, **payload):
        return await self._issues.add_attachment(issue_id, files=files, **payload)

    async def update(self, issue_id: int, attachment_id: int, *, files=None, **payload):
        return await self._issues.update_attachment(issue_id, attachment_id, files=files, **payload)

    async def delete(self, issue_id: int, attachment_id: int):
        return await self._issues.delete_attachment(issue_id, attachment_id)

    async def download(self, issue_id: int, attachment_id: int) -> bytes:
        return await self._issues.download_attachment(issue_id, attachment_id)