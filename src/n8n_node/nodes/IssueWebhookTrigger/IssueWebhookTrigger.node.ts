import type {
	IDataObject,
	INodeProperties,
	INodeType,
	INodeTypeDescription,
	IWebhookFunctions,
	IWebhookResponseData,
} from 'n8n-workflow';
import { NodeConnectionTypes } from 'n8n-workflow';

const eventTypeOptions = [
	{ name: 'Issue Created', value: 'issue.created' },
	{ name: 'Issue Updated', value: 'issue.updated' },
	{ name: 'Issue Queue Assigned', value: 'issue.queue_assigned' },
	{ name: 'Issue Commented', value: 'issue.commented' },
	{ name: 'Issue Closed', value: 'issue.closed' },
];

const properties: INodeProperties[] = [
	{
		displayName: 'Webhook Path',
		name: 'webhookPath',
		type: 'string',
		default: 'ticketsystemmock',
		required: true,
		description: 'Path segment used by n8n for the receive-only webhook endpoint.',
	},
	{
		displayName: 'Accepted Event Types',
		name: 'acceptedEventTypes',
		type: 'multiOptions',
		default: eventTypeOptions.map((option) => option.value),
		options: eventTypeOptions,
		description: 'Only emit webhook deliveries whose event type matches one of these values.',
	},
];

function getHeaderValue(headers: IDataObject, key: string): string {
	const value = headers[key] ?? headers[key.toLowerCase()];
	return typeof value === 'string' ? value : '';
}

export class IssueWebhookTrigger implements INodeType {
	description: INodeTypeDescription = {
		displayName: 'TSM - Issue Webhook Trigger',
		name: 'issueWebhookTrigger',
		icon: 'file:ticketsystemmock.svg',
		group: ['trigger'],
		version: 1,
		description: 'Receive outbound Ticket System Mock webhook deliveries in n8n.',
		defaults: {
			name: 'TSM - Issue Webhook Trigger',
		},
		inputs: [],
		outputs: [NodeConnectionTypes.Main],
		credentials: [{ name: 'ticketSystemMockApi', required: true }],
		webhooks: [
			{
				name: 'default',
				httpMethod: 'POST',
				responseMode: 'onReceived',
				path: '={{$parameter["webhookPath"]}}',
			},
		],
		properties,
	};

	webhookMethods = {
		default: {
			async checkExists() {
				return false;
			},
			async create() {
				return true;
			},
			async delete() {
				return true;
			},
		},
	};

	async webhook(this: IWebhookFunctions): Promise<IWebhookResponseData> {
		const body = this.getBodyData();
		const headers = this.getHeaderData() as IDataObject;
		const acceptedEventTypes = this.getNodeParameter('acceptedEventTypes', []) as string[];
		const eventType = typeof body.event === 'string'
			? body.event
			: typeof body.event_type === 'string'
				? body.event_type
				: getHeaderValue(headers, 'x-webhook-event');

		if (acceptedEventTypes.length > 0 && !acceptedEventTypes.includes(eventType)) {
			return {
				webhookResponse: {
					status: 202,
					body: { accepted: false, reason: 'event type filtered' },
				},
			};
		}

		const item: IDataObject = {
			...(body as IDataObject),
			webhook_metadata: {
				event: eventType,
				event_id: getHeaderValue(headers, 'x-webhook-event-id'),
				timestamp: getHeaderValue(headers, 'x-webhook-timestamp'),
			},
		};

		return {
			workflowData: [[{ json: item }]],
			webhookResponse: {
				status: 200,
				body: { accepted: true },
			},
		};
	}
}
