# Ubiquitous Language

## Issue Domain

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Issue** | A single work item that moves through the support workflow. | Ticket, case, item |
| **Collection** | A logical grouping of issues that shares one identifier prefix and one local sequence. | Queue prefix, ticket namespace |
| **Issue Description** | The large markdown body that captures the detailed content of an issue. | Long description, issue body |
| **Workflow State** | The authoritative lifecycle position of an issue. | Status, phase |
| **Rejected** | The exceptional workflow state used when an issue should not continue through the normal lifecycle. | Duplicate state, invalid ticket |
| **Priority** | The urgency level used to order or escalate work. | Severity |
| **Issue Category** | An admin-managed reference value that classifies an issue by type of work or request. | Category, type |
| **Issue Comment** | A note added to an issue during its lifecycle with explicit visibility. | Message, update |
| **Comment Mention** | A reference from an issue comment to a specific user using the `@username` pattern. | Mention, tagged user |
| **Comment Visibility** | The visibility level of an issue comment. | Comment type |
| **Issue State Transition** | A recorded change from one workflow state to another. | Status change, phase change |
| **Archive** | The soft-delete action that removes an issue from active views while retaining its history. | Delete, remove |
| **Escalation** | A flag on an issue that marks elevated handling without changing workflow state. | Escalated state |

## People and Ownership

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **User** | A Django `User` who can create, own, comment on, and transition issues. | Agent, login identity, assignee |
| **Group** | A Django `Group` used to dispatch and organize issue ownership. | Team, queue, department |
| **Group Membership** | A Django user's membership in a Django group. | Team membership, staffing, roster row |
| **Group Lead** | A role that monitors workload, assignment, and bottlenecks for a group. | Team lead, manager |
| **Demo Presenter** | A user of the product who demonstrates workflows and integrations. | Operator |
| **Personal Dashboard** | A user-specific read model that shows direct issue assignments and comment mentions for one user. | My work page, inbox |

## System and Integration

| Term | Definition | Aliases to avoid |
| --- | --- | --- |
| **Web Application** | The system of record that owns issues, workflow, and API contracts. | Backend |
| **REST API** | The external contract used to create, query, update, and transition issues. | Integration layer |
| **Integration System** | An external system that interacts with issues through the API. | Client, consumer |
| **Product Display Name** | The configurable name shown by the application from environment-backed settings. | App title |
| **Instance Kanban Board** | The user-facing board that groups issues by workflow state for operational visibility. | Kanban Board, dashboard, board state |
| **Issue Card** | The reusable summary component that presents an issue in list and board contexts. | Issue tile, summary card |

## Relationships

- An **Issue** has one current **Workflow State**.
- An **Issue** belongs to one **Collection** that determines its identifier prefix.
- An **Issue** has one **Issue Description** stored as markdown content.
- An **Issue** has one **Issue Category**.
- An **Issue** can be associated to zero or one **Group** for dispatching.
- An **Issue** can be associated to zero or one **User**.
- If an **Issue** is associated to a **User**, that **User** belongs to the associated **Group**.
- An **Issue Comment** can create zero or more **Comment Mention** records.
- An **Archive** changes an **Issue** into an archived, soft-deleted record
  without removing its history.
- A **Personal Dashboard** is derived from issues assigned to one **User** and
  **Comment Mention** records that point to that same **User**.
- A **User** can belong to many **Group** records through Django's built-in **Group Membership** relationship.
- The **Instance Kanban Board** is derived from **Issue** records and their current
  **Workflow State**.
- A **Collection** owns the next local issue sequence for its prefixed identifiers.
- The **Web Application** owns the **REST API** and remains the source of truth
  for the issue lifecycle.

## Example Dialogue

> **Dev:** "Should the Kanban column come from issue status or workflow phase?"
>
> **Domain expert:** "Use **Workflow State** as the single source of truth. The
> **Instance Kanban Board** groups **Issue** records by that state."
>
> **Dev:** "If an issue is routed to a group and then picked up by a user, how
> do we represent that?"
>
> **Domain expert:** "Associate the **Issue** to at most one **Group** for
> dispatch. If a **User** from that **Group** takes it, associate that
> **User** to the same **Issue**."
>
> **Dev:** "How do we represent `@` mentions in comments and the user's work
> overview?"
>
> **Domain expert:** "Keep the **Issue Comment** as the authored note, extract a
> **Comment Mention** for each referenced **User**, and build the
> **Personal Dashboard** from assigned **Issue** records plus those mentions."
>
> **Dev:** "If a user archives an issue from the board, do we delete it?"
>
> **Domain expert:** "No. **Archive** is a soft-delete action. The **Issue**
> stays stored for audit history even if active views stop showing it."
>
> **Dev:** "Should the specification keep separate actor terms like agent and
> team?"
>
> **Domain expert:** "No. Use Django's own terms directly. **User** is the
> canonical actor term and **Group** is the canonical dispatch term. Avoid
> **Agent** and **Team** in the specification."

## Flagged Ambiguities

- "ticket" and "issue" were both used for the primary work item. Prefer
  **Issue** as the canonical term.
- "status" and "phase" were both used for lifecycle state. Prefer
  **Workflow State** as the canonical term.
- "dashboard" could mean the **Instance Kanban Board** or a user-specific
  **Personal Dashboard**. Use the more precise term for each context.
- "delete" could mean hard deletion or **Archive**. Prefer **Archive** for the
  user-facing soft-delete behavior.
- "agent" and "user" were both used for the acting identity. Prefer
  **User** as the canonical term in the specification.
- "team" and "group" were both used for dispatch ownership. Prefer
  **Group** as the canonical term in the specification.
- "escalated" was previously treated as a workflow state. Prefer **Escalation**
  as a separate flag on an **Issue**.
- "duplicate" was previously treated as a workflow state. Prefer
  **Rejected** for the exceptional terminal state and avoid reintroducing a
  separate duplicate-specific workflow state.