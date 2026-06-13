import type {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';
import { NodeApiError, NodeConnectionType, NodeOperationError } from 'n8n-workflow';

import { ticketingApiRequest, unwrapDataArrayResponse } from '../../transport/request';

type IssueOperation = 'list' | 'get' | 'create' | 'update' | 'archive' | 'move';

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

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'list',
	noDataExpression: true,
	options: [
		{ name: 'List', value: 'list', action: 'List issues', description: 'Return issues that match the supplied filters' },
		{ name: 'Get', value: 'get', action: 'Get issue', description: 'Return one issue with detail, history, comments, and attachments' },
		{ name: 'Create', value: 'create', action: 'Create issue', description: 'Create a new issue' },
		{ name: 'Update', value: 'update', action: 'Update issue', description: 'Update an existing issue' },
		{ name: 'Archive', value: 'archive', action: 'Archive issue', description: 'Archive an issue so it leaves active views' },
		{ name: 'Move', value: 'move', action: 'Move issue', description: 'Move an issue to another board state and position' },
	],
};

const issueIdProperty: INodeProperties = {
	displayName: 'Issue ID',
	name: 'issueId',
	type: 'number',
	default: 1,
	required: true,
	typeOptions: {
		minValue: 1,
		numberPrecision: 0,
	},
	displayOptions: {
		show: {
			operation: ['get', 'update', 'archive', 'move'],
		},
	},
};

const listFilterProperties: INodeProperties[] = [
	{
		displayName: 'Search',
		name: 'search',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['list'] } },
	},
	{
		displayName: 'Assignee',
		name: 'assignee',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['list'] } },
		description: 'Optional user identifier used to limit returned issues to one assignee.',
	},
	{
		displayName: 'Priority',
		name: 'priority',
		type: 'options',
		default: '',
		options: priorityFilterOptions,
		displayOptions: { show: { operation: ['list'] } },
	},
	{
		displayName: 'Collection',
		name: 'collection',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['list'] } },
	},
	{
		displayName: 'Category',
		name: 'category',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['list'] } },
	},
	{
		displayName: 'Workflow State',
		name: 'workflowStateFilter',
		type: 'options',
		default: '',
		options: workflowStateFilterOptions,
		displayOptions: { show: { operation: ['list'] } },
		description: 'Optional workflow state code, for example NEW or IN_PROGRESS.',
	},
	{
		displayName: 'Workflow State Label',
		name: 'workflowStateLabel',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['list'] } },
		description: 'Optional workflow state label, for example New or In Progress.',
	},
];

const issueMutationProperties: INodeProperties[] = [
	{
		displayName: 'Title',
		name: 'title',
		type: 'string',
		default: '',
		required: true,
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Description Markdown',
		name: 'descriptionMarkdown',
		type: 'string',
		default: '',
		typeOptions: { rows: 5 },
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Collection ID',
		name: 'collectionId',
		type: 'number',
		default: 1,
		required: true,
		typeOptions: { minValue: 1, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Category ID',
		name: 'categoryId',
		type: 'number',
		default: 1,
		required: true,
		typeOptions: { minValue: 1, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Priority',
		name: 'issuePriority',
		type: 'options',
		default: 'MEDIUM',
		options: [
			{ name: 'Low', value: 'LOW' },
			{ name: 'Medium', value: 'MEDIUM' },
			{ name: 'High', value: 'HIGH' },
			{ name: 'Critical', value: 'CRITICAL' },
		],
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Group ID',
		name: 'groupId',
		type: 'number',
		default: 0,
		typeOptions: { minValue: 0, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional group identifier. Leave as 0 for no group.',
	},
	{
		displayName: 'User ID',
		name: 'userId',
		type: 'number',
		default: 0,
		typeOptions: { minValue: 0, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional assignee identifier. Leave as 0 for no assignee.',
	},
	{
		displayName: 'Is Escalated',
		name: 'isEscalated',
		type: 'boolean',
		default: false,
		displayOptions: { show: { operation: ['create'] } },
	},
	{
		displayName: 'Workflow State',
		name: 'workflowState',
		type: 'options',
		default: 'NEW',
		options: [
			{ name: 'New', value: 'NEW' },
			{ name: 'Triage', value: 'TRIAGE' },
			{ name: 'Assigned', value: 'ASSIGNED' },
			{ name: 'In Progress', value: 'IN_PROGRESS' },
			{ name: 'Waiting', value: 'WAITING' },
			{ name: 'Resolved', value: 'RESOLVED' },
			{ name: 'Closed', value: 'CLOSED' },
			{ name: 'Rejected', value: 'REJECTED' },
		],
		displayOptions: { show: { operation: ['create'] } },
		description: 'Workflow state to use at creation time or after update.',
	},
];

const issueUpdateProperties: INodeProperties[] = [
	{
		displayName: 'Update Fields',
		name: 'updateFields',
		type: 'collection',
		placeholder: 'Add Field',
		default: {},
		displayOptions: { show: { operation: ['update'] } },
		options: [
			{ displayName: 'Title', name: 'title', type: 'string', default: '' },
			{
				displayName: 'Description Markdown',
				name: 'descriptionMarkdown',
				type: 'string',
				default: '',
				typeOptions: { rows: 5 },
			},
			{
				displayName: 'Collection ID',
				name: 'collectionId',
				type: 'number',
				default: 1,
				typeOptions: { minValue: 1, numberPrecision: 0 },
			},
			{
				displayName: 'Category ID',
				name: 'categoryId',
				type: 'number',
				default: 1,
				typeOptions: { minValue: 1, numberPrecision: 0 },
			},
			{
				displayName: 'Priority',
				name: 'issuePriority',
				type: 'options',
				default: 'MEDIUM',
				options: [
					{ name: 'Low', value: 'LOW' },
					{ name: 'Medium', value: 'MEDIUM' },
					{ name: 'High', value: 'HIGH' },
					{ name: 'Critical', value: 'CRITICAL' },
				],
			},
			{
				displayName: 'Group ID',
				name: 'groupId',
				type: 'number',
				default: 0,
				typeOptions: { minValue: 0, numberPrecision: 0 },
				description: 'Set to 0 to clear the group assignment.',
			},
			{
				displayName: 'User ID',
				name: 'userId',
				type: 'number',
				default: 0,
				typeOptions: { minValue: 0, numberPrecision: 0 },
				description: 'Set to 0 to clear the assignee.',
			},
			{ displayName: 'Is Escalated', name: 'isEscalated', type: 'boolean', default: false },
			{
				displayName: 'Workflow State',
				name: 'workflowState',
				type: 'options',
				default: 'NEW',
				options: [
					{ name: 'New', value: 'NEW' },
					{ name: 'Triage', value: 'TRIAGE' },
					{ name: 'Assigned', value: 'ASSIGNED' },
					{ name: 'In Progress', value: 'IN_PROGRESS' },
					{ name: 'Waiting', value: 'WAITING' },
					{ name: 'Resolved', value: 'RESOLVED' },
					{ name: 'Closed', value: 'CLOSED' },
					{ name: 'Rejected', value: 'REJECTED' },
				],
			},
			{
				displayName: 'Transition Reason',
				name: 'transitionReason',
				type: 'string',
				default: '',
				description: 'Optional reason recorded when the workflow state changes.',
			},
		],
	},
];

const archiveProperties: INodeProperties[] = [
	{
		displayName: 'Confirm Archive',
		name: 'confirmArchive',
		type: 'boolean',
		default: false,
		required: true,
		displayOptions: { show: { operation: ['archive'] } },
		description: 'Must be true to archive the issue.',
	},
];

const moveProperties: INodeProperties[] = [
	{
		displayName: 'Target State',
		name: 'targetState',
		type: 'options',
		default: 'NEW',
		options: [
			{ name: 'New', value: 'NEW' },
			{ name: 'Triage', value: 'TRIAGE' },
			{ name: 'Assigned', value: 'ASSIGNED' },
			{ name: 'In Progress', value: 'IN_PROGRESS' },
			{ name: 'Waiting', value: 'WAITING' },
			{ name: 'Resolved', value: 'RESOLVED' },
			{ name: 'Closed', value: 'CLOSED' },
			{ name: 'Rejected', value: 'REJECTED' },
		],
		displayOptions: { show: { operation: ['move'] } },
	},
	{
		displayName: 'Position Index',
		name: 'positionIndex',
		type: 'number',
		default: 0,
		typeOptions: { minValue: 0, numberPrecision: 0 },
		displayOptions: { show: { operation: ['move'] } },
		description: 'Target position within the destination column.',
	},
];

function buildIssuePath(context: IExecuteFunctions, operation: IssueOperation, itemIndex: number): string {
	switch (operation) {
		case 'list':
		case 'create':
			return '/api/issues';
		case 'get':
		case 'update':
		case 'archive':
		case 'move': {
			const issueId = context.getNodeParameter('issueId', itemIndex) as number;
			if (operation === 'get' || operation === 'update') {
				return `/api/issues/${issueId}`;
			}
			if (operation === 'archive') {
				return `/api/issues/${issueId}/archive`;
			}
			return `/api/issues/${issueId}/move`;
		}
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
}

function buildIssueMutationBody(context: IExecuteFunctions, itemIndex: number): IDataObject {
	const groupId = context.getNodeParameter('groupId', itemIndex) as number;
	const userId = context.getNodeParameter('userId', itemIndex) as number;

	return {
		title: context.getNodeParameter('title', itemIndex) as string,
		description_markdown: context.getNodeParameter('descriptionMarkdown', itemIndex) as string,
		collection: context.getNodeParameter('collectionId', itemIndex) as number,
		category: context.getNodeParameter('categoryId', itemIndex) as number,
		priority: context.getNodeParameter('issuePriority', itemIndex) as string,
		group: groupId > 0 ? groupId : null,
		user: userId > 0 ? userId : null,
		is_escalated: context.getNodeParameter('isEscalated', itemIndex) as boolean,
		workflow_state: context.getNodeParameter('workflowState', itemIndex) as string,
		transition_reason: context.getNodeParameter('transitionReason', itemIndex, '') as string,
	};
}

function buildIssueUpdateBody(context: IExecuteFunctions, itemIndex: number): IDataObject {
	const updateFields = (context.getNodeParameter('updateFields', itemIndex, {}) as IDataObject) ?? {};
	const body: IDataObject = {};

	if (Object.prototype.hasOwnProperty.call(updateFields, 'title')) {
		body.title = updateFields.title as string;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'descriptionMarkdown')) {
		body.description_markdown = updateFields.descriptionMarkdown as string;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'collectionId')) {
		body.collection = updateFields.collectionId as number;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'categoryId')) {
		body.category = updateFields.categoryId as number;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'issuePriority')) {
		body.priority = updateFields.issuePriority as string;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'groupId')) {
		const groupId = updateFields.groupId as number;
		body.group = groupId > 0 ? groupId : null;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'userId')) {
		const userId = updateFields.userId as number;
		body.user = userId > 0 ? userId : null;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'isEscalated')) {
		body.is_escalated = updateFields.isEscalated as boolean;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'workflowState')) {
		body.workflow_state = updateFields.workflowState as string;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'transitionReason')) {
		body.transition_reason = updateFields.transitionReason as string;
	}

	return body;
}

function buildIssueRequestConfig(
	context: IExecuteFunctions,
	operation: IssueOperation,
	itemIndex: number,
): { method: 'GET' | 'POST' | 'PUT'; qs?: IDataObject; body?: IDataObject } {
	switch (operation) {
		case 'list':
			return {
				method: 'GET',
				qs: {
					search: context.getNodeParameter('search', itemIndex) as string,
					assignee: context.getNodeParameter('assignee', itemIndex) as string,
					priority: context.getNodeParameter('priority', itemIndex) as string,
					collection: context.getNodeParameter('collection', itemIndex) as string,
					category: context.getNodeParameter('category', itemIndex) as string,
					workflow_state: context.getNodeParameter('workflowStateFilter', itemIndex) as string,
					workflow_state_label: context.getNodeParameter('workflowStateLabel', itemIndex) as string,
				},
			};
		case 'get':
			return { method: 'GET' };
		case 'create':
			return { method: 'POST', body: buildIssueMutationBody(context, itemIndex) };
		case 'update':
			return { method: 'PUT', body: buildIssueUpdateBody(context, itemIndex) };
		case 'archive':
			return {
				method: 'POST',
				body: {
					confirm_archive: context.getNodeParameter('confirmArchive', itemIndex) as boolean,
				},
			};
		case 'move':
			return {
				method: 'POST',
				body: {
					target_state: context.getNodeParameter('targetState', itemIndex) as string,
					position_index: context.getNodeParameter('positionIndex', itemIndex) as number,
				},
			};
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
}

export class Issue implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Issue',
		name: 'issue',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Read and mutate issues in Ticket System Mock.',
		defaults: {
			name: 'TSM - Issue',
		},
		inputs: [NodeConnectionType.Main],
		outputs: [NodeConnectionType.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: [
			operationProperty,
			issueIdProperty,
			...listFilterProperties,
			...issueMutationProperties,
			...issueUpdateProperties,
			...archiveProperties,
			...moveProperties,
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as IssueOperation;
				const requestConfig = buildIssueRequestConfig(this, operation, itemIndex);
				const response = await ticketingApiRequest(
					this,
					requestConfig.method,
					buildIssuePath(this, operation, itemIndex),
					{ body: requestConfig.body, qs: requestConfig.qs },
				);
				const output = operation === 'list'
					? unwrapDataArrayResponse(this, response, '`/api/issues`')
					: response;

				returnData.push({ json: output as IDataObject, pairedItem: { item: itemIndex } });
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: { error: error instanceof Error ? error.message : 'Unknown error' },
						pairedItem: { item: itemIndex },
					});
					continue;
				}

				if (error instanceof NodeApiError || error instanceof NodeOperationError) {
					throw error;
				}

				throw new NodeOperationError(
					this.getNode(),
					error instanceof Error ? error.message : 'Unknown error',
					{ itemIndex },
				);
			}
		}

		return [returnData];
	}
}
