from __future__ import annotations

from typing import Any

from .. import endpoints
from ..models import ArchiveResult, IssueAttachmentMutation, IssueCommentMutation, IssueDetail, IssueListResponse, IssueMutation, MoveResult
from ..transport import RequestConfig
from .helpers import clean_params, to_data


class SyncIssuesResource:
    def __init__(self, transport):
        self._transport = transport

    def list(self, **filters):
        response = self._transport.request("GET", endpoints.ISSUES, config=RequestConfig(params=clean_params(filters)))
        return IssueListResponse.from_dict(response).data

    def get(self, issue_id: int) -> IssueDetail:
        return IssueDetail.from_dict(self._transport.request("GET", endpoints.issue_detail(issue_id)))

    def create(self, *, files=None, **payload) -> IssueMutation:
        response = self._transport.request(
            "POST",
            endpoints.ISSUES,
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    def update(self, issue_id: int, *, files=None, **payload) -> IssueMutation:
        response = self._transport.request(
            "PUT",
            endpoints.issue_detail(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    def archive(self, issue_id: int, *, confirm_archive: bool = True) -> ArchiveResult:
        response = self._transport.request(
            "POST",
            endpoints.issue_archive(issue_id),
            config=RequestConfig(json={"confirm_archive": confirm_archive}),
        )
        return ArchiveResult.from_dict(response)

    def move(self, issue_id: int, *, target_state: str, position_index: int) -> MoveResult:
        response = self._transport.request(
            "POST",
            endpoints.issue_move(issue_id),
            config=RequestConfig(json={"target_state": target_state, "position_index": position_index}),
        )
        return MoveResult.from_dict(response)

    def add_comment(self, issue_id: int, *, files=None, **payload) -> IssueMutation:
        response = self._transport.request(
            "POST",
            endpoints.issue_comments(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    def update_comment(self, issue_id: int, comment_id: int, **payload) -> IssueCommentMutation:
        response = self._transport.request(
            "PUT",
            endpoints.issue_comment_detail(issue_id, comment_id),
            config=RequestConfig(json=payload),
        )
        return IssueCommentMutation.from_dict(response)

    def add_attachment(self, issue_id: int, *, files=None, **payload) -> IssueAttachmentMutation:
        response = self._transport.request(
            "POST",
            endpoints.issue_attachments(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueAttachmentMutation.from_dict(response)

    def update_attachment(self, issue_id: int, attachment_id: int, *, files=None, **payload) -> IssueAttachmentMutation:
        response = self._transport.request(
            "PUT",
            endpoints.issue_attachment_detail(issue_id, attachment_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueAttachmentMutation.from_dict(response)

    def delete_attachment(self, issue_id: int, attachment_id: int) -> dict[str, Any]:
        return self._transport.request("DELETE", endpoints.issue_attachment_detail(issue_id, attachment_id))

    def download_attachment(self, issue_id: int, attachment_id: int) -> bytes:
        return self._transport.request(
            "GET",
            endpoints.issue_attachment_download(issue_id, attachment_id),
            expect_json=False,
        )


class AsyncIssuesResource:
    def __init__(self, transport):
        self._transport = transport

    async def list(self, **filters):
        response = await self._transport.request(
            "GET",
            endpoints.ISSUES,
            config=RequestConfig(params=clean_params(filters)),
        )
        return IssueListResponse.from_dict(response).data

    async def get(self, issue_id: int) -> IssueDetail:
        return IssueDetail.from_dict(await self._transport.request("GET", endpoints.issue_detail(issue_id)))

    async def create(self, *, files=None, **payload) -> IssueMutation:
        response = await self._transport.request(
            "POST",
            endpoints.ISSUES,
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    async def update(self, issue_id: int, *, files=None, **payload) -> IssueMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.issue_detail(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    async def archive(self, issue_id: int, *, confirm_archive: bool = True) -> ArchiveResult:
        response = await self._transport.request(
            "POST",
            endpoints.issue_archive(issue_id),
            config=RequestConfig(json={"confirm_archive": confirm_archive}),
        )
        return ArchiveResult.from_dict(response)

    async def move(self, issue_id: int, *, target_state: str, position_index: int) -> MoveResult:
        response = await self._transport.request(
            "POST",
            endpoints.issue_move(issue_id),
            config=RequestConfig(json={"target_state": target_state, "position_index": position_index}),
        )
        return MoveResult.from_dict(response)

    async def add_comment(self, issue_id: int, *, files=None, **payload) -> IssueMutation:
        response = await self._transport.request(
            "POST",
            endpoints.issue_comments(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueMutation.from_dict(response)

    async def update_comment(self, issue_id: int, comment_id: int, **payload) -> IssueCommentMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.issue_comment_detail(issue_id, comment_id),
            config=RequestConfig(json=payload),
        )
        return IssueCommentMutation.from_dict(response)

    async def add_attachment(self, issue_id: int, *, files=None, **payload) -> IssueAttachmentMutation:
        response = await self._transport.request(
            "POST",
            endpoints.issue_attachments(issue_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueAttachmentMutation.from_dict(response)

    async def update_attachment(self, issue_id: int, attachment_id: int, *, files=None, **payload) -> IssueAttachmentMutation:
        response = await self._transport.request(
            "PUT",
            endpoints.issue_attachment_detail(issue_id, attachment_id),
            config=RequestConfig(data=to_data(payload), files=files),
        )
        return IssueAttachmentMutation.from_dict(response)

    async def delete_attachment(self, issue_id: int, attachment_id: int) -> dict[str, Any]:
        return await self._transport.request("DELETE", endpoints.issue_attachment_detail(issue_id, attachment_id))

    async def download_attachment(self, issue_id: int, attachment_id: int) -> bytes:
        return await self._transport.request(
            "GET",
            endpoints.issue_attachment_download(issue_id, attachment_id),
            expect_json=False,
        )