const assert = require('node:assert/strict');
const test = require('node:test');

const { Issue } = require('../dist/nodes/Issue/Issue.node.js');

test('Issue list schema exposes priority and workflow state as select fields', () => {
	const node = new Issue();
	const properties = node.description.properties;
	const priorityProperty = properties.find((property) => property.name === 'priority');
	const workflowStateProperty = properties.find((property) => property.name === 'workflowStateFilter');

	assert.equal(priorityProperty?.type, 'options');
	assert.deepEqual(priorityProperty?.options?.map((option) => option.value), ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
	assert.equal(workflowStateProperty?.type, 'options');
	assert.deepEqual(workflowStateProperty?.options?.map((option) => option.value), [
		'',
		'NEW',
		'TRIAGE',
		'ASSIGNED',
		'IN_PROGRESS',
		'WAITING',
		'RESOLVED',
		'CLOSED',
		'REJECTED',
	]);
});

test('Issue list operation forwards workflow state filters to the API', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'list',
				search: 'uplink',
				assignee: '12',
				priority: 'HIGH',
				collection: '3',
				category: '8',
				workflowStateFilter: 'IN_PROGRESS',
				workflowStateLabel: 'In Progress',
			};
			return parameters[name];
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ data: [{ id: 1 }] });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: [{ id: 1 }], pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/issues',
			method: 'GET',
			json: true,
			body: undefined,
			formData: undefined,
			headers: undefined,
			qs: {
				search: 'uplink',
				assignee: '12',
				priority: 'HIGH',
				collection: '3',
				category: '8',
				workflow_state: 'IN_PROGRESS',
				workflow_state_label: 'In Progress',
			},
		},
	});
});

test('Issue update operation sends only explicitly selected fields in the PUT body', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'update',
				issueId: 42,
				updateFields: {
					title: 'Updated issue title',
					workflowState: 'ASSIGNED',
					transitionReason: 'Triaged and dispatched.',
					groupId: 0,
				},
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 42, status: 'updated' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 42, status: 'updated' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/issues/42',
			method: 'PUT',
			json: true,
			body: {
				title: 'Updated issue title',
				workflow_state: 'ASSIGNED',
				transition_reason: 'Triaged and dispatched.',
				group: null,
			},
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});
