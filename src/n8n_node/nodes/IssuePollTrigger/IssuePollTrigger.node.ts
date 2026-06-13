import type {
	IDataObject,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
	IPollFunctions,
} from 'n8n-workflow';
import { NodeApiError, NodeConnectionType, NodeOperationError } from 'n8n-workflow';

import { ticketingApiRequest, unwrapDataArrayResponse } from '../../transport/request';

type PollIssueSummary = IDataObject & {
	id: number;
	updated_at: string;
};

const priorityFilterOptions = [
	{ name: 'Any', value: '' },
	{ name: 'Low', value: 'LOW' },
	{ name: 'Medium', value: 'MEDIUM' },
	{ name: 'High', value: 'HIGH' },
	{ name: 'Critical', value: 'CRITICAL' },
];

const workflowStateFilterOptions = [
	{ name: 'Any', value: '' },
	{ name: 'New', value: 'NEW' },
	{ name: 'Triage', value: 'TRIAGE' },
	{ name: 'Assigned', value: 'ASSIGNED' },
	{ name: 'In Progress', value: 'IN_PROGRESS' },
	{ name: 'Waiting', value: 'WAITING' },
	{ name: 'Resolved', value: 'RESOLVED' },
	{ name: 'Closed', value: 'CLOSED' },
	{ name: 'Rejected', value: 'REJECTED' },
];

const filterProperties: INodeProperties[] = [
	{
		displayName: 'Search',
		name: 'search',
		type: 'string',
		default: '',
	},
	{
		displayName: 'Assignee',
		name: 'assignee',
		type: 'string',
		default: '',
		description: 'Optional user identifier used to limit returned issues to one assignee.',
	},
	{
		displayName: 'Priority',
		name: 'priority',
		type: 'options',
		default: '',
		options: priorityFilterOptions,
	},
	{
		displayName: 'Collection',
		name: 'collection',
		type: 'string',
		default: '',
	},
	{
		displayName: 'Category',
		name: 'category',
		type: 'string',
		default: '',
	},
	{
		displayName: 'Workflow State',
		name: 'workflowStateFilter',
		type: 'options',
		default: '',
		options: workflowStateFilterOptions,
		description: 'Optional workflow state code, for example NEW or IN_PROGRESS.',
	},
	{
		displayName: 'Workflow State Label',
		name: 'workflowStateLabel',
		type: 'string',
		default: '',
		description: 'Optional workflow state label, for example New or In Progress.',
	},
	{
		displayName: 'Load Full Issue Detail',
		name: 'loadFullIssueDetail',
		type: 'boolean',
		default: false,
		description: 'Whether to request `/api/issues/{id}` for each newly detected issue before emitting it.',
	},
	{
		displayName: 'Emit Existing Issues On First Poll',
		name: 'emitExistingOnFirstPoll',
		type: 'boolean',
		default: true,
		description: 'Whether to emit currently matching issues the first time the poller runs instead of only setting the watermark.',
	},
];

function getIssueTimestamp(issue: PollIssueSummary): number {
	return Date.parse(String(issue.updated_at));
}

function sortIssues(issues: PollIssueSummary[]): PollIssueSummary[] {
	return [...issues].sort((left, right) => {
		const timestampDifference = getIssueTimestamp(left) - getIssueTimestamp(right);
		if (timestampDifference !== 0) {
			return timestampDifference;
		}

		return Number(left.id) - Number(right.id);
	});
}

function readStaticIssueIds(value: unknown): Set<number> {
	if (!Array.isArray(value)) {
		return new Set<number>();
	}

	return new Set(value.map((entry) => Number(entry)).filter((entry) => Number.isInteger(entry)));
}

function updateWatermark(staticData: IDataObject, issues: PollIssueSummary[]): void {
	if (issues.length === 0) {
		return;
	}

	const sortedIssues = sortIssues(issues);
	const latestTimestamp = String(sortedIssues[sortedIssues.length - 1].updated_at);
	const latestIssueIds = sortedIssues
		.filter((issue) => String(issue.updated_at) === latestTimestamp)
		.map((issue) => Number(issue.id));

	staticData.lastUpdatedAt = latestTimestamp;
	staticData.lastIssueIds = latestIssueIds;
}

function isNewIssue(issue: PollIssueSummary, lastUpdatedAt: string, lastIssueIds: Set<number>): boolean {
	const issueTimestamp = String(issue.updated_at);
	if (issueTimestamp > lastUpdatedAt) {
		return true;
	}

	if (issueTimestamp < lastUpdatedAt) {
		return false;
	}

	return !lastIssueIds.has(Number(issue.id));
}

export class IssuePollTrigger implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Issue Poll Trigger',
		name: 'issuePollTrigger',
		icon: 'file:ticketsystemmock.svg',
		group: ['trigger'],
		version: 1,
		description: 'Poll the Ticket System Mock issue list and emit newly updated issues.',
		defaults: {
			name: 'TSM - Issue Poll Trigger',
		},
		inputs: [],
		outputs: [NodeConnectionType.Main],
		polling: true,
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: filterProperties,
	};

	async poll(this: IPollFunctions): Promise<INodeExecutionData[][] | null> {
		try {
			const staticData = this.getWorkflowStaticData('node');
			const issuesResponse = await ticketingApiRequest(this, 'GET', '/api/issues', {
				qs: {
					search: this.getNodeParameter('search', '') as string,
					assignee: this.getNodeParameter('assignee', '') as string,
					priority: this.getNodeParameter('priority', '') as string,
					collection: this.getNodeParameter('collection', '') as string,
					category: this.getNodeParameter('category', '') as string,
					workflow_state: this.getNodeParameter('workflowStateFilter', '') as string,
					workflow_state_label: this.getNodeParameter('workflowStateLabel', '') as string,
				},
			});

			const issuesResponseData = unwrapDataArrayResponse(this, issuesResponse, '/api/issues');

			const issues = sortIssues(issuesResponseData as PollIssueSummary[]);
			const lastUpdatedAt = typeof staticData.lastUpdatedAt === 'string' ? staticData.lastUpdatedAt : '';
			const lastIssueIds = readStaticIssueIds(staticData.lastIssueIds);
			const emitExistingOnFirstPoll = this.getNodeParameter('emitExistingOnFirstPoll', true) as boolean;

			if (!lastUpdatedAt && !emitExistingOnFirstPoll) {
				updateWatermark(staticData, issues);
				return null;
			}

			const matchingIssues = !lastUpdatedAt
				? issues
				: issues.filter((issue) => isNewIssue(issue, lastUpdatedAt, lastIssueIds));

			updateWatermark(staticData, issues);

			if (matchingIssues.length === 0) {
				return null;
			}

			const loadFullIssueDetail = this.getNodeParameter('loadFullIssueDetail', false) as boolean;
			const emittedIssues = loadFullIssueDetail
				? await Promise.all(
						matchingIssues.map(async (issue) => {
							return (await ticketingApiRequest(this, 'GET', `/api/issues/${issue.id}`)) as IDataObject;
						}),
				  )
				: matchingIssues;

			return [
				emittedIssues.map((issue) => ({
					json: issue,
				})),
			];
		} catch (error) {
			if (error instanceof NodeApiError || error instanceof NodeOperationError) {
				throw error;
			}

			throw new NodeOperationError(
				this.getNode(),
				error instanceof Error ? error.message : 'Unknown error',
			);
		}
	}
}
