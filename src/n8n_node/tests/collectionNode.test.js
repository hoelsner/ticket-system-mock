const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeOperationError } = require('n8n-workflow');

const { Collection } = require('../dist/nodes/Collection/Collection.node.js');

test('Collection create operation forwards collection mutation fields to the API', async () => {
	const node = new Collection();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'create',
				collectionName: 'Service Desk',
				collectionPrefix: 'SRV',
				collectionDescription: 'Service desk issues',
				collectionIsActive: true,
				nextIssueSequence: 18,
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
				return JSON.stringify({ id: 5, prefix: 'SRV' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Collection' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 5, prefix: 'SRV' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions, {
		url: 'http://example.test/api/collections',
		method: 'POST',
		json: true,
		body: {
			name: 'Service Desk',
			prefix: 'SRV',
			description: 'Service desk issues',
			is_active: true,
			next_issue_sequence: 18,
		},
		formData: undefined,
		headers: undefined,
		qs: undefined,
	});
});

test('Collection update operation forwards collection mutation fields to the API', async () => {
	const node = new Collection();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'update',
				collectionId: 5,
				collectionName: 'Platform Operations',
				collectionPrefix: 'PLT',
				collectionDescription: 'Platform issues',
				collectionIsActive: false,
				nextIssueSequence: 42,
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
				return JSON.stringify({ id: 5, prefix: 'PLT' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Collection' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 5, prefix: 'PLT' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions, {
		url: 'http://example.test/api/collections/5',
		method: 'PUT',
		json: true,
		body: {
			name: 'Platform Operations',
			prefix: 'PLT',
			description: 'Platform issues',
			is_active: false,
			next_issue_sequence: 42,
		},
		formData: undefined,
		headers: undefined,
		qs: undefined,
	});
});

test('Collection continueOnFail returns an error item for unexpected failures', async () => {
	const node = new Collection();

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter() {
			return 'list';
		},
		async getCredentials() {
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication() {
				throw new Error('backend unavailable');
			},
		},
		continueOnFail() { return true; },
		getNode() { return { name: 'TSM - Collection' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request GET /api/collections failed. backend unavailable' }, pairedItem: { item: 0 } }]]);
});

test('Collection rethrows NodeOperationError instances unchanged', async () => {
	const node = new Collection();
	const expectedError = new NodeOperationError({ name: 'TSM - Collection' }, 'already normalized');

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter() { return 'list'; },
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw expectedError;
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Collection' }; },
	};

	await assert.rejects(node.execute.call(context), (error) => error === expectedError);
});

test('Collection list operation requests active collections', async () => {
	const node = new Collection();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'list' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ data: [{ id: 1, prefix: 'TASK' }] });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Collection' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: [{ id: 1, prefix: 'TASK' }], pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/collections',
			method: 'GET',
			json: true,
			body: undefined,
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});
