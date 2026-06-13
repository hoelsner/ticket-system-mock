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

type CategoryOperation = 'list' | 'create' | 'update';

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'list',
	noDataExpression: true,
	options: [
		{ name: 'List', value: 'list', description: 'Return active issue categories', action: 'List categories' },
		{ name: 'Create', value: 'create', description: 'Create a new issue category', action: 'Create category' },
		{ name: 'Update', value: 'update', description: 'Update an existing issue category', action: 'Update category' },
	],
};

const categoryIdProperty: INodeProperties = {
	displayName: 'Category ID',
	name: 'categoryId',
	type: 'number',
	default: 1,
	required: true,
	typeOptions: { minValue: 1, numberPrecision: 0 },
	displayOptions: { show: { operation: ['update'] } },
	description: 'Identifier of the category to update.',
};

const categoryMutationProperties: INodeProperties[] = [
	{ displayName: 'Name', name: 'categoryName', type: 'string', default: '', required: true, displayOptions: { show: { operation: ['create', 'update'] } } },
	{ displayName: 'Code', name: 'categoryCode', type: 'string', default: '', required: true, displayOptions: { show: { operation: ['create', 'update'] } } },
	{
		displayName: 'Description',
		name: 'categoryDescription',
		type: 'string',
		default: '',
		typeOptions: { rows: 3 },
		displayOptions: { show: { operation: ['create', 'update'] } },
	},
	{
		displayName: 'Is Active',
		name: 'categoryIsActive',
		type: 'boolean',
		default: true,
		displayOptions: { show: { operation: ['create', 'update'] } },
	},
];

function getCategoryPath(context: IExecuteFunctions, operation: CategoryOperation, itemIndex: number): string {
	if (operation === 'update') {
		const categoryId = context.getNodeParameter('categoryId', itemIndex) as number;
		return `${apiPaths.categories}/${categoryId}`;
	}

	return apiPaths.categories;
}

function getCategoryRequestConfig(
	context: IExecuteFunctions,
	operation: CategoryOperation,
	itemIndex: number,
): { method: 'GET' | 'POST' | 'PUT'; body?: IDataObject } {
	if (operation === 'list') {
		return { method: 'GET' };
	}

	return {
		method: operation === 'create' ? 'POST' : 'PUT',
		body: {
			name: context.getNodeParameter('categoryName', itemIndex) as string,
			code: context.getNodeParameter('categoryCode', itemIndex) as string,
			description: context.getNodeParameter('categoryDescription', itemIndex) as string,
			is_active: context.getNodeParameter('categoryIsActive', itemIndex) as boolean,
		},
	};
}

export class Category implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Category',
		name: 'category',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Read and mutate issue category reference data in Ticket System Mock.',
		defaults: { name: 'TSM - Category' },
		inputs: [NodeConnectionType.Main],
		outputs: [NodeConnectionType.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: [operationProperty, categoryIdProperty, ...categoryMutationProperties],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as CategoryOperation;
				const requestConfig = getCategoryRequestConfig(this, operation, itemIndex);
				const response = await ticketingApiRequest(
					this,
					requestConfig.method,
					getCategoryPath(this, operation, itemIndex),
					{ body: requestConfig.body },
				);
				const output = operation === 'list'
					? unwrapDataArrayResponse(this, response, '/api/categories')
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
