const assert = require('node:assert/strict');
const test = require('node:test');

const { IssueWebhookTrigger } = require('../dist/nodes/IssueWebhookTrigger/IssueWebhookTrigger.node.js');

test('IssueWebhookTrigger lifecycle webhook methods return static defaults', async () => {
	const node = new IssueWebhookTrigger();
	assert.equal(await node.webhookMethods.default.checkExists(), false);
	assert.equal(await node.webhookMethods.default.create(), true);
	assert.equal(await node.webhookMethods.default.delete(), true);
});

test('IssueWebhookTrigger emits accepted webhook payloads and header metadata', async () => {
	const trigger = new IssueWebhookTrigger();
	const response = await trigger.webhook.call({
		getBodyData() {
			return { event: 'issue.updated', data: { id: 42, title: 'Issue updated' } };
		},
		getHeaderData() {
			return {
				'x-webhook-event': 'issue.updated',
				'x-webhook-event-id': 'evt-1',
				'x-webhook-timestamp': '2026-06-10T12:00:00Z',
			};
		},
		getNodeParameter(name) {
			if (name === 'acceptedEventTypes') {
				return ['issue.updated'];
			}

			throw new Error(`Unexpected parameter: ${name}`);
		},
	});

	assert.deepEqual(response, {
		workflowData: [[{
			json: {
				event: 'issue.updated',
				data: { id: 42, title: 'Issue updated' },
				webhook_metadata: {
					event: 'issue.updated',
					event_id: 'evt-1',
					timestamp: '2026-06-10T12:00:00Z',
				},
			},
		}]],
		webhookResponse: {
			status: 200,
			body: { accepted: true },
		},
	});
});

test('IssueWebhookTrigger filters unmatched event types', async () => {
	const trigger = new IssueWebhookTrigger();
	const response = await trigger.webhook.call({
		getBodyData() {
			return { event: 'issue.closed' };
		},
		getHeaderData() {
			return {};
		},
		getNodeParameter(name) {
			if (name === 'acceptedEventTypes') {
				return ['issue.updated'];
			}

			throw new Error(`Unexpected parameter: ${name}`);
		},
	});

	assert.deepEqual(response, {
		webhookResponse: {
			status: 202,
			body: { accepted: false, reason: 'event type filtered' },
		},
	});
});

test('IssueWebhookTrigger can resolve event type and metadata from lowercase headers', async () => {
	const trigger = new IssueWebhookTrigger();
	const response = await trigger.webhook.call({
		getBodyData() {
			return { data: { id: 7 } };
		},
		getHeaderData() {
			return {
				'x-webhook-event': 'issue.updated',
				'x-webhook-event-id': 'evt-2',
				'x-webhook-timestamp': '2026-06-14T12:00:00Z',
			};
		},
		getNodeParameter(name) {
			if (name === 'acceptedEventTypes') {
				return ['issue.updated'];
			}

			throw new Error(`Unexpected parameter: ${name}`);
		},
	});

	assert.equal(response.workflowData[0][0].json.webhook_metadata.event, 'issue.updated');
	assert.equal(response.workflowData[0][0].json.webhook_metadata.event_id, 'evt-2');
	assert.equal(response.workflowData[0][0].json.webhook_metadata.timestamp, '2026-06-14T12:00:00Z');
});
