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
import { NodeApiError, NodeConnectionTypes, NodeOperationError } from 'n8n-workflow';

import { ticketingApiRequest } from '../../transport/request';

type IssueActivityOperation = 'addComment' | 'updateComment' | 'addAttachment' | 'updateAttachment' | 'deleteAttachment';

const operationProperty: INodeProperties = {
	displayName: 'Operation',
	name: 'operation',
	type: 'options',
	default: 'addComment',
	noDataExpression: true,
	options: [
		{ name: 'Add Comment', value: 'addComment', action: 'Add comment to issue' },
		{ name: 'Update Comment', value: 'updateComment', action: 'Update issue comment' },
		{ name: 'Add Attachment', value: 'addAttachment', action: 'Add attachment to issue' },
		{ name: 'Update Attachment', value: 'updateAttachment', action: 'Update issue attachment' },
		{ name: 'Delete Attachment', value: 'deleteAttachment', action: 'Delete issue attachment' },
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

const commentIdProperty: INodeProperties = {
	displayName: 'Comment ID',
	name: 'commentId',
	type: 'number',
	default: 1,
	required: true,
	typeOptions: {
		minValue: 1,
		numberPrecision: 0,
	},
	displayOptions: {
		show: {
			operation: ['updateComment'],
		},
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
			operation: ['updateAttachment', 'deleteAttachment'],
		},
	},
};

const commentProperties: INodeProperties[] = [
	{
		displayName: 'Body',
		name: 'body',
		type: 'string',
		default: '',
		required: true,
		typeOptions: { rows: 5 },
		displayOptions: { show: { operation: ['addComment', 'updateComment'] } },
	},
	{
		displayName: 'Visibility',
		name: 'visibility',
		type: 'options',
		default: 'INTERNAL',
		options: [
			{ name: 'Internal', value: 'INTERNAL' },
			{ name: 'Customer Visible', value: 'CUSTOMER_VISIBLE' },
		],
		displayOptions: { show: { operation: ['addComment', 'updateComment'] } },
	},
	{
		displayName: 'Attachment Description',
		name: 'commentAttachmentDescription',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['addComment'] } },
		description: 'Optional description for the attachment uploaded with the comment.',
	},
	{
		displayName: 'Attachment Binary Property',
		name: 'commentAttachmentBinaryProperty',
		type: 'string',
		default: 'data',
		displayOptions: { show: { operation: ['addComment'] } },
		description: 'Optional input binary property to upload as attachment_file together with the comment.',
	},
];

const attachmentProperties: INodeProperties[] = [
	{
		displayName: 'Description',
		name: 'attachmentDescription',
		type: 'string',
		default: '',
		displayOptions: { show: { operation: ['addAttachment', 'updateAttachment'] } },
	},
	{
		displayName: 'Binary Property',
		name: 'attachmentBinaryProperty',
		type: 'string',
		default: 'data',
		required: true,
		displayOptions: { show: { operation: ['addAttachment'] } },
		description: 'Input binary property to upload as the attachment file.',
	},
	{
		displayName: 'Replace File',
		name: 'replaceFile',
		type: 'boolean',
		default: false,
		displayOptions: { show: { operation: ['updateAttachment'] } },
		description: 'Whether to replace the stored file content as part of the update.',
	},
	{
		displayName: 'Replacement Binary Property',
		name: 'replacementBinaryProperty',
		type: 'string',
		default: 'data',
		displayOptions: { show: { operation: ['updateAttachment'], replaceFile: [true] } },
		description: 'Input binary property to use when replacing the attachment file.',
	},
];

function buildIssueActivityPath(context: IExecuteFunctions, operation: IssueActivityOperation, itemIndex: number): string {
	const issueId = context.getNodeParameter('issueId', itemIndex) as number;

	switch (operation) {
		case 'addComment':
			return `/api/issues/${issueId}/comments`;
		case 'updateComment': {
			const commentId = context.getNodeParameter('commentId', itemIndex) as number;
			return `/api/issues/${issueId}/comments/${commentId}`;
		}
		case 'addAttachment':
			return `/api/issues/${issueId}/attachments`;
		case 'updateAttachment':
		case 'deleteAttachment': {
			const attachmentId = context.getNodeParameter('attachmentId', itemIndex) as number;
			return `/api/issues/${issueId}/attachments/${attachmentId}`;
		}
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
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

async function buildCommentCreateFormData(context: IExecuteFunctions, itemIndex: number): Promise<FormData> {
	const formData = new FormData();
	const attachmentBinaryProperty = context.getNodeParameter(
		'commentAttachmentBinaryProperty',
		itemIndex,
		'',
	) as string;
	const attachmentDescription = context.getNodeParameter('commentAttachmentDescription', itemIndex, '') as string;

	formData.append('body', context.getNodeParameter('body', itemIndex) as string);
	formData.append('visibility', context.getNodeParameter('visibility', itemIndex) as string);

	if (attachmentDescription) {
		formData.append('attachment_description', attachmentDescription);
	}

	if (getInputBinary(context, itemIndex, attachmentBinaryProperty)) {
		await appendBinaryToFormData(context, itemIndex, attachmentBinaryProperty, 'attachment_file', formData);
	}

	return formData;
}

async function buildAttachmentFormData(
	context: IExecuteFunctions,
	itemIndex: number,
	options: { binaryPropertyName?: string; requireFile: boolean },
): Promise<FormData> {
	const formData = new FormData();
	const description = context.getNodeParameter('attachmentDescription', itemIndex, '') as string;
	const binaryPropertyName = options.binaryPropertyName ?? '';

	formData.append('description', description);

	if (binaryPropertyName) {
		if (!getInputBinary(context, itemIndex, binaryPropertyName) && options.requireFile) {
			throw new NodeOperationError(
				context.getNode(),
				`Binary property "${binaryPropertyName}" was not found on the input item.`,
				{ itemIndex },
			);
		}

		if (getInputBinary(context, itemIndex, binaryPropertyName)) {
			await appendBinaryToFormData(context, itemIndex, binaryPropertyName, 'file', formData);
		}
	} else if (options.requireFile) {
		throw new NodeOperationError(context.getNode(), 'Binary Property is required for Add Attachment.', {
			itemIndex,
		});
	}

	return formData;
}

async function buildIssueActivityRequestConfig(
	context: IExecuteFunctions,
	operation: IssueActivityOperation,
	itemIndex: number,
): Promise<{ method: 'POST' | 'PUT' | 'DELETE'; body?: IDataObject; formData?: FormData }> {
	switch (operation) {
		case 'addComment':
			return {
				method: 'POST',
				formData: await buildCommentCreateFormData(context, itemIndex),
			};
		case 'updateComment':
			return {
				method: 'PUT',
				body: {
					body: context.getNodeParameter('body', itemIndex) as string,
					visibility: context.getNodeParameter('visibility', itemIndex) as string,
				},
			};
		case 'addAttachment':
			return {
				method: 'POST',
				formData: await buildAttachmentFormData(context, itemIndex, {
					binaryPropertyName: context.getNodeParameter('attachmentBinaryProperty', itemIndex) as string,
					requireFile: true,
				}),
			};
		case 'updateAttachment': {
			const replaceFile = context.getNodeParameter('replaceFile', itemIndex, false) as boolean;

			return {
				method: 'PUT',
				formData: await buildAttachmentFormData(context, itemIndex, {
					binaryPropertyName: replaceFile
						? (context.getNodeParameter('replacementBinaryProperty', itemIndex) as string)
						: '',
					requireFile: false,
				}),
			};
		}
		case 'deleteAttachment':
			return { method: 'DELETE' };
		default:
			throw new Error(`Unsupported operation: ${operation satisfies never}`);
	}
}

export class IssueActivity implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Issue Activity',
		name: 'issueActivity',
		icon: 'file:ticketsystemmock.svg',
		group: ['transform'],
		version: 1,
		description: 'Mutate issue comments and attachments in Ticket System Mock.',
		defaults: {
			name: 'TSM - Issue Activity',
		},
		inputs: [NodeConnectionTypes.Main],
		outputs: [NodeConnectionTypes.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		properties: [
			operationProperty,
			issueIdProperty,
			commentIdProperty,
			attachmentIdProperty,
			...commentProperties,
			...attachmentProperties,
		],
	};

	async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
		const items = this.getInputData();
		const returnData: INodeExecutionData[] = [];

		for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
			try {
				const operation = this.getNodeParameter('operation', itemIndex) as IssueActivityOperation;
				const requestConfig = await buildIssueActivityRequestConfig(this, operation, itemIndex);
				const response = await ticketingApiRequest(
					this,
					requestConfig.method,
					buildIssueActivityPath(this, operation, itemIndex),
					{ body: requestConfig.body, formData: requestConfig.formData },
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
