#!/usr/bin/env python3

from __future__ import annotations

import click

from ticketsystemmock import AvatarType, TicketSystemClient, WorkflowState

GROUP_DEFINITIONS = [
    {"name": "IT Operations"},
    {"name": "Agent Escalation (HITL)"},
    {"name": "Agents > Triage"},
]

USER_DEFINITIONS = [
    {
        "username": "demo",
        "password": "demo1234",
        "first_name": "Demo",
        "last_name": "User",
        "group_name": "IT Operations",
        "avatar_type": AvatarType.INITIALS.value,
        "is_system_user": False,
    },
    {
        "username": "user",
        "password": "user1234",
        "first_name": "Escalation",
        "last_name": "User",
        "group_name": "Agent Escalation (HITL)",
        "avatar_type": AvatarType.INITIALS.value,
        "is_system_user": False,
    },
    {
        "username": "triage_agent",
        "password": "triage1234",
        "first_name": "Triage",
        "last_name": "Agent",
        "group_name": "Agents > Triage",
        "avatar_type": AvatarType.IMAGE.value,
        "is_system_user": True,
    },
]

COLLECTION_DEFINITIONS = [
    {
        "name": "Infrastructure Operations",
        "prefix": "ITOPS",
        "description": "Collection for infrastructure operations and monitoring.",
        "is_active": True,
        "next_issue_sequence": 1,
    },
    {
        "name": "Test",
        "prefix": "TEST",
        "description": "Collection for testing and development.",
        "is_active": True,
        "next_issue_sequence": 1,
    },
]

CATEGORY_DEFINITIONS = [
    {
        "name": "Unknown/Unassigned",
        "code": "UNKNOWN",
        "description": "Issues that are not assigned to a specific category.",
        "is_active": True,
    },
    {
        "name": "IT Operations > General",
        "code": "IT-GENERAL",
        "description": "General and unknown issues related to IT operations.",
        "is_active": True,
    },
    {
        "name": "IT Operations > DDI",
        "code": "IT-DDI",
        "description": "Issues related to DDI (DNS, DHCP, and IP).",
        "is_active": True,
    },
    {
        "name": "Enterprise Network > General",
        "code": "EN-GENERAL",
        "description": "General and unknown issues related to the enterprise network.",
        "is_active": True,
    },
    {
        "name": "Enterprise Network > Cisco Catalyst Center",
        "code": "EN-CATCENTER",
        "description": "Issues related to the Cisco Catalyst Center.",
        "is_active": True,
    },
    {
        "name": "Enterprise Network > WLAN",
        "code": "EN-WLAN",
        "description": "Issues related to the WLAN.",
        "is_active": True,
    },
    {
        "name": "Data Center > General",
        "code": "DC-GENERAL",
        "description": "General and unknown issues related to the data center.",
        "is_active": True,
    },
    {
        "name": "Data Center > Cisco Nexus",
        "code": "DC-NEXUS",
        "description": "Issues related to the Cisco Nexus.",
        "is_active": True,
    },
    {
        "name": "Data Center > Cisco ACI",
        "code": "DC-ACI",
        "description": "Issues related to the Cisco ACI.",
        "is_active": True,
    },
    {
        "name": "Endpoint Management > General",
        "code": "EP-GENERAL",
        "description": "General and unknown issues related to endpoint management.",
        "is_active": True,
    },
    {
        "name": "Endpoint Management > Onboarding",
        "code": "EP-ONBOARD",
        "description": "Issues related to endpoint onboarding.",
        "is_active": True,
    },
]


def collect_instance_summary(client: TicketSystemClient) -> dict[str, int]:
    return {
        "groups": len(client.reference.list_groups()),
        "users": len(client.reference.list_users()),
        "collections": len(client.reference.list_collections()),
        "categories": len(client.reference.list_categories()),
        "workflow_rules": len(client.admin.workflow_state_auto_assignment_rules.list()),
        "issues": len(client.issues.list()),
    }


def print_instance_summary(summary: dict[str, int], username: str) -> None:
    click.echo(f"Authenticated superuser: {username}")
    click.echo("Existing instance data slated for deletion:")
    for key, value in summary.items():
        click.echo(f"- {key}: {value}")
    click.echo("The authenticated superuser account will be preserved.")


def require_confirmation() -> None:
    confirmation = click.prompt("Type RESET to delete existing instance data and continue")
    if confirmation != "RESET":
        raise click.ClickException("Reset cancelled.")


def seed_groups(client: TicketSystemClient) -> dict[str, int]:
    group_ids: dict[str, int] = {}
    for group_definition in GROUP_DEFINITIONS:
        created_group = client.admin.groups.create(name=group_definition["name"])
        group_ids[group_definition["name"]] = created_group.group.id
        click.echo(f"Created group {group_definition['name']} ({created_group.group.id})")
    return group_ids


def seed_users(client: TicketSystemClient, group_ids: dict[str, int]) -> dict[str, int]:
    user_ids: dict[str, int] = {}
    for user_definition in USER_DEFINITIONS:
        created_user = client.admin.users.create(
            username=user_definition["username"],
            password=user_definition["password"],
            first_name=user_definition["first_name"],
            last_name=user_definition["last_name"],
            is_active=True,
            is_staff=False,
            is_superuser=False,
            avatar_type=user_definition["avatar_type"],
            is_system_user=user_definition["is_system_user"],
            group_ids=[group_ids[user_definition["group_name"]]],
        )
        user_ids[user_definition["username"]] = created_user.user.id
        click.echo(f"Created user {user_definition['username']} ({created_user.user.id})")
    return user_ids


def seed_collections(client: TicketSystemClient) -> None:
    for collection_definition in COLLECTION_DEFINITIONS:
        created_collection = client.reference.create_collection(**collection_definition)
        click.echo(f"Created collection {created_collection.collection.name} ({created_collection.collection.id})")


def seed_categories(client: TicketSystemClient) -> None:
    for category_definition in CATEGORY_DEFINITIONS:
        created_category = client.reference.create_category(**category_definition)
        click.echo(f"Created category {created_category.category.code} ({created_category.category.id})")


def seed_workflow_rule(client: TicketSystemClient, group_ids: dict[str, int], user_ids: dict[str, int]) -> None:
    created_rule = client.admin.workflow_state_auto_assignment_rules.create(
        workflow_state=WorkflowState.NEW,
        group=group_ids["Agents > Triage"],
        user=user_ids["triage_agent"],
        is_active=True,
    )
    click.echo(
        "Created workflow rule",
        nl=False,
    )
    click.echo(
        f" {created_rule.rule.workflow_state} -> {created_rule.rule.group.name} / {created_rule.rule.user.username}"
    )


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--base-url",
    default="http://webapp:8000",
    envvar="TSM_BASE_URL",
    show_default=True,
    show_envvar=True,
    help="Ticket System Mock base URL.",
)
@click.option(
    "--username",
    default="admin",
    envvar="TSM_USERNAME",
    show_default=True,
    show_envvar=True,
    help="Superuser username.",
)
@click.option(
    "--password",
    envvar="TSM_PASSWORD",
    hide_input=True,
    help="Superuser password. Prompts securely when omitted.",
)
def main(base_url: str, username: str, password: str | None) -> None:
    """Reset and seed the issue triage with n8n scenario through the Ticket System Mock Python SDK."""

    if not password:
        password = click.prompt("Superuser password", hide_input=True)

    with TicketSystemClient(base_url, username, password) as client:
        authenticated_user = client.auth.me()
        if not authenticated_user.is_superuser:
            raise click.ClickException("The scenario seeding account must be a superuser.")

        summary = collect_instance_summary(client)
        print_instance_summary(summary, authenticated_user.username)
        require_confirmation()

        reset_result = client.admin.reset_instance(confirm_reset=True)
        click.echo("Reset completed.")
        for key, value in reset_result.deleted_counts.items():
            if value:
                click.echo(f"- deleted {key}: {value}")

        group_ids = seed_groups(client)
        user_ids = seed_users(client, group_ids)
        seed_collections(client)
        seed_categories(client)
        seed_workflow_rule(client, group_ids, user_ids)

    click.echo("Scenario seeding completed successfully.")


if __name__ == "__main__":
    main()
