import type {
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';
import { NodeApiError, NodeOperationError } from 'n8n-workflow';
import { NodeConnectionType } from 'n8n-workflow';

import { apiPaths, type ReferenceDataOperation } from '../../transport/api.constants';
import { ticketingApiRequest, unwrapDataArrayResponse } from '../../transport/request';

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'health',
	noDataExpression: true,
	options: [
		{
			name: 'Health',
			value: 'health',
			description: 'Confirm that the authenticated REST API surface is reachable',
			action: 'Check API health',
		},
		{
			name: 'Get Authenticated User',
			value: 'authMe',
			description: 'Return the currently authenticated user',
			action: 'Get authenticated user',
		},
		{
			name: 'Get My Profile',
			value: 'profileMe',
			description: 'Return the authenticated user profile',
			action: 'Get my profile',
		},
		{
			name: 'Get User Profile',
			value: 'userProfile',
			description: 'Return the public profile for one user',
			action: 'Get user profile',
		},
		{
			name: 'List Groups',
			value: 'listGroups',
			description: 'Return assignable groups',
			action: 'List groups',
		},
		{
			name: 'List Users',
			value: 'listUsers',
			description: 'Return assignable users, optionally filtered by group',
			action: 'List users',
		},
	],
};

const usernameProperty: INodeProperties = {
	displayName: 'Username',
	name: 'username',
	type: 'string',
	default: '',
	required: true,
	displayOptions: {
		show: {
			operation: ['userProfile'],
		},
	},
	description: 'Username used to resolve the public profile.',
};

const groupIdProperty: INodeProperties = {
	displayName: 'Group ID',
	name: 'groupId',
	type: 'number',
	default: 0,
	typeOptions: {
		minValue: 0,
		numberPrecision: 0,
	},
	displayOptions: {
		show: {
			operation: ['listUsers'],
		},
	},
	description: 'Optional group identifier used to limit returned users. Leave as 0 to return all users.',
};

function getPath(operation: ReferenceDataOperation, itemIndex: number, context: IExecuteFunctions): string {
	switch (operation) {
		case 'health':
			return apiPaths.health;
		case 'authMe':
			return apiPaths.authMe;
		case 'profileMe':
			return apiPaths.profileMe;
		case 'userProfile': {
			const username = context.getNodeParameter('username', itemIndex) as string;
			return `${apiPaths.users}/${encodeURIComponent(username)}/profile`;
		}
		case 'listGroups':
			return apiPaths.groups;
		case 'listUsers':
			return apiPaths.users;
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
}

function getRequestConfig(
	context: IExecuteFunctions,
	operation: ReferenceDataOperation,
	itemIndex: number,
): { method: 'GET' | 'POST' | 'PUT'; body?: IDataObject; qs?: IDataObject } {
	switch (operation) {
		case 'health':
		case 'authMe':
		case 'profileMe':
		case 'userProfile':
		case 'listGroups':
			return { method: 'GET' };
		case 'listUsers': {
			const groupId = context.getNodeParameter('groupId', itemIndex) as number;
			return groupId > 0 ? { method: 'GET', qs: { group_id: groupId } } : { method: 'GET' };
		}
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
}

export class ReferenceData implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Reference Data',
		name: 'referenceData',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Read basic REST API reference and system data from Ticket System Mock.',
		defaults: {
			name: 'TSM - Reference Data',
		},
		inputs: [NodeConnectionType.Main],
		outputs: [NodeConnectionType.Main],
		credentials: [
			{
				name: 'ticketSystemMockApi',
				required: true,
			},
		],
		properties: [
			operationProperty,
			usernameProperty,
			groupIdProperty,
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as ReferenceDataOperation;
				const requestConfig = getRequestConfig(this, operation, itemIndex);
				const response = await ticketingApiRequest(
					this,
					requestConfig.method,
					getPath(operation, itemIndex, this),
					{
						body: requestConfig.body,
						qs: requestConfig.qs,
					},
				);
				const output = operation === 'listGroups' || operation === 'listUsers'
					? unwrapDataArrayResponse(this, response, getPath(operation, itemIndex, this))
					: response;

				returnData.push({
					json: output as IDataObject,
					pairedItem: { item: itemIndex },
				});
			} catch (error) {
				if (this.continueOnFail()) {
					returnData.push({
						json: {
							error: error instanceof Error ? error.message : 'Unknown error',
						},
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
