import type {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';
import { NodeApiError, NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';

import { apiPaths } from '../../transport/api.constants';
import { ticketingApiRequest, unwrapDataArrayResponse } from '../../transport/request';

type IssueOperation = 'list' | 'get' | 'create' | 'update' | 'archive' | 'move';
type ReferenceMatchField = 'name' | 'username';

type ReferenceLookupConfig = {
	apiPath: string;
	fieldLabel: string;
	matchField: ReferenceMatchField;
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
		default: 0,
		typeOptions: { minValue: 1, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
		description: 'Leave as 0 to resolve the collection by name instead.',
	},
	{
		displayName: 'Collection Name',
		name: 'collectionName',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional collection name used instead of Collection ID.',
	},
	{
		displayName: 'Category ID',
		name: 'categoryId',
		type: 'number',
		default: 0,
		typeOptions: { minValue: 1, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
		description: 'Leave as 0 to resolve the category by name or store no category.',
	},
	{
		displayName: 'Category Name',
		name: 'categoryName',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional category name used instead of Category ID.',
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
		description: 'Optional group identifier. Leave as 0 to use Group Name or store no group.',
	},
	{
		displayName: 'Group Name',
		name: 'groupName',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional group name used instead of Group ID.',
	},
	{
		displayName: 'User ID',
		name: 'userId',
		type: 'number',
		default: 0,
		typeOptions: { minValue: 0, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional assignee identifier. Leave as 0 to use Username or store no assignee.',
	},
	{
		displayName: 'Username',
		name: 'username',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['create'] } },
		description: 'Optional username used instead of User ID.',
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
				default: 0,
				typeOptions: { minValue: 0, numberPrecision: 0 },
				description: 'Leave as 0 to resolve the collection by name instead.',
			},
			{
				displayName: 'Collection Name',
				name: 'collectionName',
				type: 'string',
				default: '',
			},
			{
				displayName: 'Category ID',
				name: 'categoryId',
				type: 'number',
				default: 0,
				typeOptions: { minValue: 1, numberPrecision: 0 },
				description: 'Leave as 0 to resolve the category by name instead.',
			},
			{
				displayName: 'Category Name',
				name: 'categoryName',
				type: 'string',
				default: '',
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
				displayName: 'Group Name',
				name: 'groupName',
				type: 'string',
				default: '',
			},
			{
				displayName: 'User ID',
				name: 'userId',
				type: 'number',
				default: 0,
				typeOptions: { minValue: 0, numberPrecision: 0 },
				description: 'Set to 0 to clear the assignee.',
			},
			{
				displayName: 'Username',
				name: 'username',
				type: 'string',
				default: '',
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

function readNonEmptyString(value: unknown): string | undefined {
	if (typeof value !== 'string') {
		return undefined;
	}

	const trimmedValue = value.trim();
	return trimmedValue ? trimmedValue : undefined;
}

function readPositiveInteger(value: unknown): number | undefined {
	if (typeof value === 'number' && Number.isInteger(value) && value > 0) {
		return value;
	}

	if (typeof value === 'string' && value.trim()) {
		const parsedValue = Number.parseInt(value, 10);
		if (Number.isInteger(parsedValue) && parsedValue > 0) {
			return parsedValue;
		}
	}

	return undefined;
}

function isExplicitZeroValue(value: unknown): boolean {
	return value === 0 || value === '0';
}

function buildReferenceConflictError(
	context: IExecuteFunctions,
	itemIndex: number,
	fieldLabel: string,
): NodeOperationError {
	return new NodeOperationError(
		context.getNode(),
		`Provide either ${fieldLabel} ID or ${fieldLabel} Name, not both.`,
		{ itemIndex },
	);
}

async function resolveReferenceIdByName(
	context: IExecuteFunctions,
	itemIndex: number,
	name: string,
	config: ReferenceLookupConfig,
): Promise<number> {
	const response = await ticketingApiRequest(context, 'GET', config.apiPath);
	const records = unwrapDataArrayResponse(context, response, config.apiPath) as Array<Record<string, unknown>>;
	const normalizedName = name.toLocaleLowerCase();
	const matches = records.filter((record) => {
		const candidate = readNonEmptyString(record[config.matchField]);
		return candidate?.toLocaleLowerCase() === normalizedName;
	});

	if (matches.length === 0) {
		throw new NodeOperationError(
			context.getNode(),
			`${config.fieldLabel} name "${name}" was not found.`,
			{ itemIndex },
		);
	}

	if (matches.length > 1) {
		throw new NodeOperationError(
			context.getNode(),
			`${config.fieldLabel} name "${name}" matched multiple records. Use the numeric ID instead.`,
			{ itemIndex },
		);
	}

	const recordId = readPositiveInteger(matches[0].id);
	if (!recordId) {
		throw new NodeOperationError(
			context.getNode(),
			`${config.fieldLabel} name "${name}" resolved to a record without a valid numeric ID.`,
			{ itemIndex },
		);
	}

	return recordId;
}

async function resolveRequiredReferenceId(
	context: IExecuteFunctions,
	itemIndex: number,
	config: ReferenceLookupConfig,
	idValue: unknown,
	nameValue: unknown,
): Promise<number> {
	const referenceId = readPositiveInteger(idValue);
	const referenceName = readNonEmptyString(nameValue);

	if (referenceId && referenceName) {
		throw buildReferenceConflictError(context, itemIndex, config.fieldLabel);
	}

	if (referenceId) {
		return referenceId;
	}

	if (referenceName) {
		return resolveReferenceIdByName(context, itemIndex, referenceName, config);
	}

	throw new NodeOperationError(
		context.getNode(),
		`Provide either ${config.fieldLabel} ID or ${config.fieldLabel} Name.`,
		{ itemIndex },
	);
}

async function resolveOptionalReferenceValue(
	context: IExecuteFunctions,
	itemIndex: number,
	config: ReferenceLookupConfig,
	idValue: unknown,
	nameValue: unknown,
	returnNullWhenUnset: boolean,
): Promise<number | null | undefined> {
	const referenceId = readPositiveInteger(idValue);
	const referenceName = readNonEmptyString(nameValue);

	if (referenceId && referenceName) {
		throw buildReferenceConflictError(context, itemIndex, config.fieldLabel);
	}

	if (referenceId) {
		return referenceId;
	}

	if (referenceName) {
		return resolveReferenceIdByName(context, itemIndex, referenceName, config);
	}

	if (isExplicitZeroValue(idValue) || returnNullWhenUnset) {
		return null;
	}

	return undefined;
}

async function buildIssueMutationBody(context: IExecuteFunctions, itemIndex: number): Promise<IDataObject> {
	const [collectionId, categoryId, groupId, userId] = await Promise.all([
		resolveRequiredReferenceId(
			context,
			itemIndex,
			{ apiPath: apiPaths.collections, fieldLabel: 'Collection', matchField: 'name' },
			context.getNodeParameter('collectionId', itemIndex, 0),
			context.getNodeParameter('collectionName', itemIndex, ''),
		),
		resolveOptionalReferenceValue(
			context,
			itemIndex,
			{ apiPath: apiPaths.categories, fieldLabel: 'Category', matchField: 'name' },
			context.getNodeParameter('categoryId', itemIndex, 0),
			context.getNodeParameter('categoryName', itemIndex, ''),
			true,
		),
		resolveOptionalReferenceValue(
			context,
			itemIndex,
			{ apiPath: apiPaths.groups, fieldLabel: 'Group', matchField: 'name' },
			context.getNodeParameter('groupId', itemIndex, 0),
			context.getNodeParameter('groupName', itemIndex, ''),
			true,
		),
		resolveOptionalReferenceValue(
			context,
			itemIndex,
			{ apiPath: apiPaths.users, fieldLabel: 'User', matchField: 'username' },
			context.getNodeParameter('userId', itemIndex, 0),
			context.getNodeParameter('username', itemIndex, ''),
			true,
		),
	]);

	return {
		title: context.getNodeParameter('title', itemIndex) as string,
		description_markdown: context.getNodeParameter('descriptionMarkdown', itemIndex) as string,
		collection: collectionId,
		category: categoryId,
		priority: context.getNodeParameter('issuePriority', itemIndex) as string,
		group: groupId,
		user: userId,
		is_escalated: context.getNodeParameter('isEscalated', itemIndex) as boolean,
		workflow_state: context.getNodeParameter('workflowState', itemIndex) as string,
		transition_reason: context.getNodeParameter('transitionReason', itemIndex, '') as string,
	};
}

function hasAnyOwnProperty(source: IDataObject, propertyNames: string[]): boolean {
	return propertyNames.some((propertyName) => Object.prototype.hasOwnProperty.call(source, propertyName));
}

async function buildIssueUpdateBody(context: IExecuteFunctions, itemIndex: number): Promise<IDataObject> {
	const updateFields = (context.getNodeParameter('updateFields', itemIndex, {}) as IDataObject) ?? {};
	const body: IDataObject = {};

	if (Object.prototype.hasOwnProperty.call(updateFields, 'title')) {
		body.title = updateFields.title as string;
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'descriptionMarkdown')) {
		body.description_markdown = updateFields.descriptionMarkdown as string;
	}
	if (hasAnyOwnProperty(updateFields, ['collectionId', 'collectionName'])) {
		body.collection = await resolveRequiredReferenceId(
			context,
			itemIndex,
			{ apiPath: apiPaths.collections, fieldLabel: 'Collection', matchField: 'name' },
			updateFields.collectionId,
			updateFields.collectionName,
		);
	}
	if (hasAnyOwnProperty(updateFields, ['categoryId', 'categoryName'])) {
		body.category = await resolveRequiredReferenceId(
			context,
			itemIndex,
			{ apiPath: apiPaths.categories, fieldLabel: 'Category', matchField: 'name' },
			updateFields.categoryId,
			updateFields.categoryName,
		);
	}
	if (Object.prototype.hasOwnProperty.call(updateFields, 'issuePriority')) {
		body.priority = updateFields.issuePriority as string;
	}
	if (hasAnyOwnProperty(updateFields, ['groupId', 'groupName'])) {
		const groupValue = await resolveOptionalReferenceValue(
			context,
			itemIndex,
			{ apiPath: apiPaths.groups, fieldLabel: 'Group', matchField: 'name' },
			updateFields.groupId,
			updateFields.groupName,
			false,
		);
		if (groupValue !== undefined) {
			body.group = groupValue;
		}
	}
	if (hasAnyOwnProperty(updateFields, ['userId', 'username'])) {
		const userValue = await resolveOptionalReferenceValue(
			context,
			itemIndex,
			{ apiPath: apiPaths.users, fieldLabel: 'User', matchField: 'username' },
			updateFields.userId,
			updateFields.username,
			false,
		);
		if (userValue !== undefined) {
			body.user = userValue;
		}
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
): Promise<{ method: 'GET' | 'POST' | 'PUT'; qs?: IDataObject; body?: IDataObject }> {
	switch (operation) {
		case 'list':
			return Promise.resolve({
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
			});
		case 'get':
			return Promise.resolve({ method: 'GET' });
		case 'create':
			return buildIssueMutationBody(context, itemIndex).then((body) => ({ method: 'POST', body }));
		case 'update':
			return buildIssueUpdateBody(context, itemIndex).then((body) => ({ method: 'PUT', body }));
		case 'archive':
			return Promise.resolve({
				method: 'POST',
				body: {
					confirm_archive: context.getNodeParameter('confirmArchive', itemIndex) as boolean,
				},
			});
		case 'move':
			return Promise.resolve({
				method: 'POST',
				body: {
					target_state: context.getNodeParameter('targetState', itemIndex) as string,
					position_index: context.getNodeParameter('positionIndex', itemIndex) as number,
				},
			});
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
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
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
				const requestConfig = await buildIssueRequestConfig(this, operation, itemIndex);
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
