import FormData from 'form-data';
import type {
	IBinaryData,
	IDataObject,
	IExecuteFunctions,
	INodeExecutionData,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
} from 'n8n-workflow';
import { NodeApiError, NodeConnectionType, NodeOperationError } from 'n8n-workflow';

import { ticketingApiRequest } from '../../transport/request';

type IssueAttachmentOperation = 'add' | 'update' | 'delete';

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'add',
	noDataExpression: true,
	options: [
		{ name: 'Add', value: 'add', action: 'Add attachment to issue' },
		{ name: 'Update', value: 'update', action: 'Update issue attachment' },
		{ name: 'Delete', value: 'delete', action: 'Delete issue attachment' },
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
};

const attachmentIdProperty: INodeProperties = {
	displayName: 'Attachment ID',
	name: 'attachmentId',
	type: 'number',
	default: 1,
	required: true,
	typeOptions: {
		minValue: 1,
		numberPrecision: 0,
	},
	displayOptions: {
		show: {
			operation: ['update', 'delete'],
		},
	},
};

const attachmentProperties: INodeProperties[] = [
	{
		displayName: 'Description',
		name: 'attachmentDescription',
		type: 'string',
		default: '',
		description: 'Attachment description to store on the issue.',
	},
	{
		displayName: 'Binary Property',
		name: 'attachmentBinaryProperty',
		type: 'string',
		default: 'data',
		required: true,
		displayOptions: { show: { operation: ['add'] } },
		description: 'Input binary property to upload as the attachment file.',
	},
	{
		displayName: 'Replace File',
		name: 'replaceFile',
		type: 'boolean',
		default: false,
		displayOptions: { show: { operation: ['update'] } },
		description: 'Whether to replace the stored file content as part of the update.',
	},
	{
		displayName: 'Replacement Binary Property',
		name: 'replacementBinaryProperty',
		type: 'string',
		default: 'data',
		displayOptions: { show: { operation: ['update'], replaceFile: [true] } },
		description: 'Input binary property to upload as the replacement file.',
	},
];

function buildIssueAttachmentPath(
	context: IExecuteFunctions,
	operation: IssueAttachmentOperation,
	itemIndex: number,
): string {
	const issueId = context.getNodeParameter('issueId', itemIndex) as number;
	if (operation === 'add') {
		return `/api/issues/${issueId}/attachments`;
	}

	const attachmentId = context.getNodeParameter('attachmentId', itemIndex) as number;
	return `/api/issues/${issueId}/attachments/${attachmentId}`;
}

function getInputBinary(
	context: IExecuteFunctions,
	itemIndex: number,
	propertyName: string,
): IBinaryData | undefined {
	if (!propertyName) {
		return undefined;
	}

	return context.getInputData()[itemIndex]?.binary?.[propertyName];
}

async function appendBinaryToFormData(
	context: IExecuteFunctions,
	itemIndex: number,
	propertyName: string,
	fieldName: string,
	formData: FormData,
): Promise<void> {
	const binaryData = context.helpers.assertBinaryData(itemIndex, propertyName);
	const buffer = await context.helpers.getBinaryDataBuffer(itemIndex, propertyName);
	const mimeType = binaryData.mimeType || 'application/octet-stream';
	const fileName = binaryData.fileName || `${fieldName}.bin`;

	formData.append(fieldName, buffer, { contentType: mimeType, filename: fileName });
}

async function buildIssueAttachmentFormData(
	context: IExecuteFunctions,
	operation: IssueAttachmentOperation,
	itemIndex: number,
): Promise<FormData> {
	const formData = new FormData();
	const description = context.getNodeParameter('attachmentDescription', itemIndex, '') as string;

	formData.append('description', description);

	if (operation === 'add') {
		const binaryPropertyName = context.getNodeParameter('attachmentBinaryProperty', itemIndex, '') as string;
		if (!binaryPropertyName) {
			throw new NodeOperationError(context.getNode(), 'Binary Property is required for Add.', {
				itemIndex,
			});
		}

		if (!getInputBinary(context, itemIndex, binaryPropertyName)) {
			throw new NodeOperationError(
				context.getNode(),
				`Binary property "${binaryPropertyName}" was not found on the input item.`,
				{ itemIndex },
			);
		}

		await appendBinaryToFormData(context, itemIndex, binaryPropertyName, 'file', formData);
		return formData;
	}

	if (operation === 'update') {
		const replaceFile = context.getNodeParameter('replaceFile', itemIndex, false) as boolean;
		const binaryPropertyName = replaceFile
			? (context.getNodeParameter('replacementBinaryProperty', itemIndex, '') as string)
			: '';

		if (!replaceFile) {
			return formData;
		}

		if (!binaryPropertyName) {
			throw new NodeOperationError(context.getNode(), 'Replacement Binary Property is required when Replace File is enabled.', {
				itemIndex,
			});
		}

		if (!getInputBinary(context, itemIndex, binaryPropertyName)) {
			throw new NodeOperationError(
				context.getNode(),
				`Binary property "${binaryPropertyName}" was not found on the input item.`,
				{ itemIndex },
			);
		}

		await appendBinaryToFormData(context, itemIndex, binaryPropertyName, 'file', formData);
	}

	return formData;
}

export class IssueAttachment implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Issue Attachment',
		name: 'issueAttachment',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Add, update, or delete attachments on a specified Ticket System Mock issue.',
		defaults: {
			name: 'TSM - Issue Attachment',
		},
		inputs: [NodeConnectionType.Main],
		outputs: [NodeConnectionType.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: [operationProperty, issueIdProperty, attachmentIdProperty, ...attachmentProperties],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as IssueAttachmentOperation;
				const response = await ticketingApiRequest(
					this,
					operation === 'add' ? 'POST' : operation === 'update' ? 'PUT' : 'DELETE',
					buildIssueAttachmentPath(this, operation, itemIndex),
					operation === 'delete' ? {} : { formData: await buildIssueAttachmentFormData(this, operation, itemIndex) },
				);

				returnData.push({ json: response as IDataObject, pairedItem: { item: itemIndex } });
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
