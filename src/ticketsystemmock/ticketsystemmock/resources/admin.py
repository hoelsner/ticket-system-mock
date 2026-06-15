from __future__ import annotations

from .. import endpoints
from ..models import (
    GroupDeletion,
    GroupMutation,
    InstanceResetResult,
    ManagedGroup,
    ManagedUser,
    UserDeactivation,
    UserMutation,
    WorkflowStateAutoAssignmentRule,
    WorkflowStateAutoAssignmentRuleDeletion,
    WorkflowStateAutoAssignmentRuleListResponse,
    WorkflowStateAutoAssignmentRuleMutation,
)
from ..transport import RequestConfig


class SyncAdminUsersResource:
    def __init__(self, transport):
        self._transport = transport

    def create(self, **payload) -> UserMutation:
        return UserMutation.from_dict(
            self._transport.request("POST", endpoints.USERS, config=RequestConfig(json=payload))
        )

    def get(self, user_id: int) -> ManagedUser:
        return ManagedUser.from_dict(self._transport.request("GET", endpoints.user_detail(user_id)))

    def update(self, user_id: int, **payload) -> UserMutation:
        return UserMutation.from_dict(
            self._transport.request("PUT", endpoints.user_detail(user_id), config=RequestConfig(json=payload))
        )

    def deactivate(self, user_id: int) -> UserDeactivation:
        return UserDeactivation.from_dict(self._transport.request("DELETE", endpoints.user_detail(user_id)))


class AsyncAdminUsersResource:
    def __init__(self, transport):
        self._transport = transport

    async def create(self, **payload) -> UserMutation:
        return UserMutation.from_dict(
            await self._transport.request("POST", endpoints.USERS, config=RequestConfig(json=payload))
        )

    async def get(self, user_id: int) -> ManagedUser:
        return ManagedUser.from_dict(await self._transport.request("GET", endpoints.user_detail(user_id)))

    async def update(self, user_id: int, **payload) -> UserMutation:
        return UserMutation.from_dict(
            await self._transport.request("PUT", endpoints.user_detail(user_id), config=RequestConfig(json=payload))
        )

    async def deactivate(self, user_id: int) -> UserDeactivation:
        return UserDeactivation.from_dict(await self._transport.request("DELETE", endpoints.user_detail(user_id)))


class SyncAdminGroupsResource:
    def __init__(self, transport):
        self._transport = transport

    def create(self, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            self._transport.request("POST", endpoints.GROUPS, config=RequestConfig(json=payload))
        )

    def get(self, group_id: int) -> ManagedGroup:
        return ManagedGroup.from_dict(self._transport.request("GET", endpoints.group_detail(group_id)))

    def update(self, group_id: int, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            self._transport.request("PUT", endpoints.group_detail(group_id), config=RequestConfig(json=payload))
        )

    def delete(self, group_id: int) -> GroupDeletion:
        return GroupDeletion.from_dict(self._transport.request("DELETE", endpoints.group_detail(group_id)))


class AsyncAdminGroupsResource:
    def __init__(self, transport):
        self._transport = transport

    async def create(self, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            await self._transport.request("POST", endpoints.GROUPS, config=RequestConfig(json=payload))
        )

    async def get(self, group_id: int) -> ManagedGroup:
        return ManagedGroup.from_dict(await self._transport.request("GET", endpoints.group_detail(group_id)))

    async def update(self, group_id: int, **payload) -> GroupMutation:
        return GroupMutation.from_dict(
            await self._transport.request("PUT", endpoints.group_detail(group_id), config=RequestConfig(json=payload))
        )

    async def delete(self, group_id: int) -> GroupDeletion:
        return GroupDeletion.from_dict(await self._transport.request("DELETE", endpoints.group_detail(group_id)))


class SyncAdminWorkflowStateAutoAssignmentRulesResource:
    def __init__(self, transport):
        self._transport = transport

    def list(self) -> list[WorkflowStateAutoAssignmentRule]:
        response = self._transport.request("GET", endpoints.WORKFLOW_STATE_AUTO_ASSIGNMENT_RULES)
        return WorkflowStateAutoAssignmentRuleListResponse.from_dict(response).data

    def create(self, **payload) -> WorkflowStateAutoAssignmentRuleMutation:
        return WorkflowStateAutoAssignmentRuleMutation.from_dict(
            self._transport.request(
                "POST",
                endpoints.WORKFLOW_STATE_AUTO_ASSIGNMENT_RULES,
                config=RequestConfig(json=payload),
            )
        )

    def get(self, rule_id: int) -> WorkflowStateAutoAssignmentRule:
        return WorkflowStateAutoAssignmentRule.from_dict(
            self._transport.request("GET", endpoints.workflow_state_auto_assignment_rule_detail(rule_id))
        )

    def update(self, rule_id: int, **payload) -> WorkflowStateAutoAssignmentRuleMutation:
        return WorkflowStateAutoAssignmentRuleMutation.from_dict(
            self._transport.request(
                "PUT",
                endpoints.workflow_state_auto_assignment_rule_detail(rule_id),
                config=RequestConfig(json=payload),
            )
        )

    def delete(self, rule_id: int) -> WorkflowStateAutoAssignmentRuleDeletion:
        return WorkflowStateAutoAssignmentRuleDeletion.from_dict(
            self._transport.request("DELETE", endpoints.workflow_state_auto_assignment_rule_detail(rule_id))
        )


class AsyncAdminWorkflowStateAutoAssignmentRulesResource:
    def __init__(self, transport):
        self._transport = transport

    async def list(self) -> list[WorkflowStateAutoAssignmentRule]:
        response = await self._transport.request("GET", endpoints.WORKFLOW_STATE_AUTO_ASSIGNMENT_RULES)
        return WorkflowStateAutoAssignmentRuleListResponse.from_dict(response).data

    async def create(self, **payload) -> WorkflowStateAutoAssignmentRuleMutation:
        return WorkflowStateAutoAssignmentRuleMutation.from_dict(
            await self._transport.request(
                "POST",
                endpoints.WORKFLOW_STATE_AUTO_ASSIGNMENT_RULES,
                config=RequestConfig(json=payload),
            )
        )

    async def get(self, rule_id: int) -> WorkflowStateAutoAssignmentRule:
        return WorkflowStateAutoAssignmentRule.from_dict(
            await self._transport.request("GET", endpoints.workflow_state_auto_assignment_rule_detail(rule_id))
        )

    async def update(self, rule_id: int, **payload) -> WorkflowStateAutoAssignmentRuleMutation:
        return WorkflowStateAutoAssignmentRuleMutation.from_dict(
            await self._transport.request(
                "PUT",
                endpoints.workflow_state_auto_assignment_rule_detail(rule_id),
                config=RequestConfig(json=payload),
            )
        )

    async def delete(self, rule_id: int) -> WorkflowStateAutoAssignmentRuleDeletion:
        return WorkflowStateAutoAssignmentRuleDeletion.from_dict(
            await self._transport.request("DELETE", endpoints.workflow_state_auto_assignment_rule_detail(rule_id))
        )


class SyncAdminResource:
    def __init__(self, transport):
        self._transport = transport
        self.users = SyncAdminUsersResource(transport)
        self.groups = SyncAdminGroupsResource(transport)
        self.workflow_state_auto_assignment_rules = SyncAdminWorkflowStateAutoAssignmentRulesResource(transport)

    def reset_instance(self, *, confirm_reset: bool) -> InstanceResetResult:
        return InstanceResetResult.from_dict(
            self._transport.request(
                "POST",
                endpoints.RESET_INSTANCE,
                config=RequestConfig(json={"confirm_reset": confirm_reset}),
            )
        )


class AsyncAdminResource:
    def __init__(self, transport):
        self._transport = transport
        self.users = AsyncAdminUsersResource(transport)
        self.groups = AsyncAdminGroupsResource(transport)
        self.workflow_state_auto_assignment_rules = AsyncAdminWorkflowStateAutoAssignmentRulesResource(transport)

    async def reset_instance(self, *, confirm_reset: bool) -> InstanceResetResult:
        return InstanceResetResult.from_dict(
            await self._transport.request(
                "POST",
                endpoints.RESET_INSTANCE,
                config=RequestConfig(json={"confirm_reset": confirm_reset}),
            )
        )
