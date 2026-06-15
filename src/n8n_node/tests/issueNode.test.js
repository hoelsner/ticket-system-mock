const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeOperationError } = require('n8n-workflow');

const { Issue } = require('../dist/nodes/Issue/Issue.node.js');

test('Issue get operation requests one issue detail record', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'get', issueId: 42 };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 42, title: 'Router outage' });
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

	assert.deepEqual(result, [[{ json: { id: 42, title: 'Router outage' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/42');
	assert.equal(capturedRequest.requestOptions.method, 'GET');
});

test('Issue create operation sends the issue mutation body to the API', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'create',
				title: 'Edge router outage',
				descriptionMarkdown: 'Customers cannot reach the branch office.',
				collectionId: 2,
				categoryId: 8,
				issuePriority: 'CRITICAL',
				groupId: 0,
				userId: 23,
				isEscalated: true,
				workflowState: 'TRIAGE',
				transitionReason: 'Escalated during intake.',
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
				return JSON.stringify({ id: 77, title: 'Edge router outage' });
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

	assert.deepEqual(result, [[{ json: { id: 77, title: 'Edge router outage' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions, {
		url: 'http://example.test/api/issues',
		method: 'POST',
		json: true,
		body: {
			title: 'Edge router outage',
			description_markdown: 'Customers cannot reach the branch office.',
			collection: 2,
			category: 8,
			priority: 'CRITICAL',
			group: null,
			user: 23,
			is_escalated: true,
			workflow_state: 'TRIAGE',
			transition_reason: 'Escalated during intake.',
		},
		formData: undefined,
		headers: undefined,
		qs: undefined,
	});
});

test('Issue create operation resolves collection, category, group, and user names before sending the API request', async () => {
	const node = new Issue();
	const capturedRequests = [];

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'create',
				title: 'Edge router outage',
				descriptionMarkdown: 'Customers cannot reach the branch office.',
				collectionId: 0,
				collectionName: 'Infrastructure',
				categoryId: 0,
				categoryName: 'Network Incident',
				issuePriority: 'CRITICAL',
				groupId: 0,
				groupName: 'Network Operations',
				userId: 0,
				username: 'alice',
				isEscalated: true,
				workflowState: 'TRIAGE',
				transitionReason: 'Escalated during intake.',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequests.push({ credentialName, requestOptions });
				if (requestOptions.url.endsWith('/api/collections')) {
					return JSON.stringify({ data: [{ id: 2, name: 'Infrastructure' }] });
				}
				if (requestOptions.url.endsWith('/api/categories')) {
					return JSON.stringify({ data: [{ id: 8, name: 'Network Incident' }] });
				}
				if (requestOptions.url.endsWith('/api/groups')) {
					return JSON.stringify({ data: [{ id: 14, name: 'Network Operations' }] });
				}
				if (requestOptions.url.endsWith('/api/users')) {
					return JSON.stringify({ data: [{ id: 23, username: 'alice' }] });
				}
				return JSON.stringify({ id: 77, title: 'Edge router outage' });
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

	assert.deepEqual(result, [[{ json: { id: 77, title: 'Edge router outage' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequests.map(({ requestOptions }) => requestOptions.url), [
		'http://example.test/api/collections',
		'http://example.test/api/categories',
		'http://example.test/api/groups',
		'http://example.test/api/users',
		'http://example.test/api/issues',
	]);
	assert.deepEqual(capturedRequests.at(-1), {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/issues',
			method: 'POST',
			json: true,
			body: {
				title: 'Edge router outage',
				description_markdown: 'Customers cannot reach the branch office.',
				collection: 2,
				category: 8,
				priority: 'CRITICAL',
				group: 14,
				user: 23,
				is_escalated: true,
				workflow_state: 'TRIAGE',
				transition_reason: 'Escalated during intake.',
			},
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});

test('Issue create operation stores a null category when no category reference is supplied', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'create',
				title: 'Edge router outage',
				descriptionMarkdown: 'Customers cannot reach the branch office.',
				collectionId: 2,
				categoryId: 0,
				categoryName: '',
				issuePriority: 'CRITICAL',
				groupId: 0,
				userId: 0,
				isEscalated: false,
				workflowState: 'NEW',
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
				return JSON.stringify({ id: 77, title: 'Edge router outage', category: null });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue' };
		},
	};

	await node.execute.call(context);

	assert.equal(capturedRequest.requestOptions.body.category, null);
});

test('Issue archive operation sends the archive confirmation body', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'archive', issueId: 42, confirmArchive: true };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 42, archived: true });
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

	assert.deepEqual(result, [[{ json: { id: 42, archived: true }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions.body, { confirm_archive: true });
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/42/archive');
	assert.equal(capturedRequest.requestOptions.method, 'POST');
});

test('Issue move operation sends the target state and position to the API', async () => {
	const node = new Issue();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'move', issueId: 42, targetState: 'IN_PROGRESS', positionIndex: 3 };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 42, workflow_state: 'IN_PROGRESS' });
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

	assert.deepEqual(result, [[{ json: { id: 42, workflow_state: 'IN_PROGRESS' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions.body, {
		target_state: 'IN_PROGRESS',
		position_index: 3,
	});
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/42/move');
});

test('Issue continueOnFail returns an error item for unexpected failures', async () => {
	const node = new Issue();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'get', issueId: 42 };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw new Error('issue lookup failed');
			},
		},
		continueOnFail() { return true; },
		getNode() { return { name: 'TSM - Issue' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request GET /api/issues/42 failed. issue lookup failed' }, pairedItem: { item: 0 } }]]);
});

test('Issue rethrows NodeOperationError instances unchanged', async () => {
	const node = new Issue();
	const expectedError = new NodeOperationError({ name: 'TSM - Issue' }, 'already normalized');

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter() { return 'get'; },
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw expectedError;
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue' }; },
	};

	await assert.rejects(node.execute.call(context), (error) => error === expectedError);
});

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

test('Issue update operation resolves collection, category, group, and user names inside update fields', async () => {
	const node = new Issue();
	const capturedRequests = [];

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
					collectionName: 'Infrastructure',
					categoryName: 'Network Incident',
					groupName: 'Network Operations',
					username: 'alice',
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
				capturedRequests.push({ credentialName, requestOptions });
				if (requestOptions.url.endsWith('/api/collections')) {
					return JSON.stringify({ data: [{ id: 2, name: 'Infrastructure' }] });
				}
				if (requestOptions.url.endsWith('/api/categories')) {
					return JSON.stringify({ data: [{ id: 8, name: 'Network Incident' }] });
				}
				if (requestOptions.url.endsWith('/api/groups')) {
					return JSON.stringify({ data: [{ id: 14, name: 'Network Operations' }] });
				}
				if (requestOptions.url.endsWith('/api/users')) {
					return JSON.stringify({ data: [{ id: 23, username: 'alice' }] });
				}
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
	assert.deepEqual(capturedRequests.map(({ requestOptions }) => requestOptions.url), [
		'http://example.test/api/collections',
		'http://example.test/api/categories',
		'http://example.test/api/groups',
		'http://example.test/api/users',
		'http://example.test/api/issues/42',
	]);
	assert.deepEqual(capturedRequests.at(-1), {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/issues/42',
			method: 'PUT',
			json: true,
			body: {
				collection: 2,
				category: 8,
				group: 14,
				user: 23,
			},
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});
