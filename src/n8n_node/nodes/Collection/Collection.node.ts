import type {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';
import { NodeApiError, NodeConnectionType, NodeOperationError } from 'n8n-workflow';

import { apiPaths } from '../../transport/api.constants';
import { ticketingApiRequest, unwrapDataArrayResponse } from '../../transport/request';

type CollectionOperation = 'list' | 'create' | 'update';

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'list',
	noDataExpression: true,
	options: [
		{ name: 'List', value: 'list', description: 'Return active collections', action: 'List collections' },
		{ name: 'Create', value: 'create', description: 'Create a new collection', action: 'Create collection' },
		{ name: 'Update', value: 'update', description: 'Update an existing collection', action: 'Update collection' },
	],
};

const collectionIdProperty: INodeProperties = {
	displayName: 'Collection ID',
	name: 'collectionId',
	type: 'number',
	default: 1,
	required: true,
	typeOptions: {
		minValue: 1,
		numberPrecision: 0,
	},
	displayOptions: { show: { operation: ['update'] } },
	description: 'Identifier of the collection to update.',
};

const collectionMutationProperties: INodeProperties[] = [
	{ displayName: 'Name', name: 'collectionName', type: 'string', default: '', required: true, displayOptions: { show: { operation: ['create', 'update'] } } },
	{
		displayName: 'Prefix',
		name: 'collectionPrefix',
		type: 'string',
		default: '',
		required: true,
		displayOptions: { show: { operation: ['create', 'update'] } },
		description: 'Identifier prefix used when generating issue numbers.',
	},
	{
		displayName: 'Description',
		name: 'collectionDescription',
		type: 'string',
		default: '',
		typeOptions: { rows: 3 },
		displayOptions: { show: { operation: ['create', 'update'] } },
	},
	{
		displayName: 'Is Active',
		name: 'collectionIsActive',
		type: 'boolean',
		default: true,
		displayOptions: { show: { operation: ['create', 'update'] } },
	},
	{
		displayName: 'Next Issue Sequence',
		name: 'nextIssueSequence',
		type: 'number',
		default: 1,
		typeOptions: { minValue: 1, numberPrecision: 0 },
		displayOptions: { show: { operation: ['create', 'update'] } },
		description: 'Next issue number sequence value for the collection.',
	},
];

function getCollectionPath(context: IExecuteFunctions, operation: CollectionOperation, itemIndex: number): string {
	if (operation === 'update') {
		const collectionId = context.getNodeParameter('collectionId', itemIndex) as number;
		return `${apiPaths.collections}/${collectionId}`;
	}

	return apiPaths.collections;
}

function getCollectionRequestConfig(
	context: IExecuteFunctions,
	operation: CollectionOperation,
	itemIndex: number,
): { method: 'GET' | 'POST' | 'PUT'; body?: IDataObject } {
	if (operation === 'list') {
		return { method: 'GET' };
	}

	return {
		method: operation === 'create' ? 'POST' : 'PUT',
		body: {
			name: context.getNodeParameter('collectionName', itemIndex) as string,
			prefix: context.getNodeParameter('collectionPrefix', itemIndex) as string,
			description: context.getNodeParameter('collectionDescription', itemIndex) as string,
			is_active: context.getNodeParameter('collectionIsActive', itemIndex) as boolean,
			next_issue_sequence: context.getNodeParameter('nextIssueSequence', itemIndex) as number,
		},
	};
}

export class Collection implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Collection',
		name: 'collection',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Read and mutate collection reference data in Ticket System Mock.',
		defaults: { name: 'TSM - Collection' },
		inputs: [NodeConnectionType.Main],
		outputs: [NodeConnectionType.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: [operationProperty, collectionIdProperty, ...collectionMutationProperties],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as CollectionOperation;
				const requestConfig = getCollectionRequestConfig(this, operation, itemIndex);
				const response = await ticketingApiRequest(
					this,
					requestConfig.method,
					getCollectionPath(this, operation, itemIndex),
					{ body: requestConfig.body },
				);
				const output = operation === 'list'
					? unwrapDataArrayResponse(this, response, '/api/collections')
					: response;

				returnData.push({ json: output as IDataObject, pairedItem: { item: itemIndex } });
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({ json: { error: error instanceof Error ? error.message : 'Unknown error' }, pairedItem: { item: itemIndex } });
					continue;
				}

				if (error instanceof NodeApiError || error instanceof NodeOperationError) {
					throw error;
				}

				throw new NodeOperationError(this.getNode(), error instanceof Error ? error.message : 'Unknown error', { itemIndex });
			}
		}

		return [returnData];
	}
}
