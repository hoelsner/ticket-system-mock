const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeOperationError } = require('n8n-workflow');

const { ReferenceData } = require('../dist/nodes/ReferenceData/ReferenceData.node.js');

test('ReferenceData health operation requests the API health endpoint', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'health' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ status: 'ok' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Reference Data' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'ok' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/health');
	assert.equal(capturedRequest.requestOptions.method, 'GET');
	assert.equal(capturedRequest.requestOptions.qs, undefined);
});

test('ReferenceData list users operation forwards the optional group filter', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'listUsers', groupId: 12 };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ data: [{ id: 4, username: 'alice' }] });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Reference Data' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: [{ id: 4, username: 'alice' }], pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions.qs, { group_id: 12 });
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/users');
});

test('ReferenceData user profile operation encodes the username in the request path', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'userProfile', username: 'alice smith' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ username: 'alice smith' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Reference Data' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { username: 'alice smith' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/users/alice%20smith/profile');
});

test('ReferenceData get authenticated user operation requests the auth endpoint', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'authMe' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ username: 'alice' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Reference Data' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { username: 'alice' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/auth/me');
});

test('ReferenceData get my profile operation requests the profile endpoint', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'profileMe' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ display_name: 'Alice' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Reference Data' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { display_name: 'Alice' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/profile/me');
});

test('ReferenceData continueOnFail returns an error item for unexpected failures', async () => {
	const node = new ReferenceData();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'profileMe' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw new Error('profile endpoint failed');
			},
		},
		continueOnFail() { return true; },
		getNode() { return { name: 'TSM - Reference Data' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request GET /api/profile/me failed. profile endpoint failed' }, pairedItem: { item: 0 } }]]);
});

test('ReferenceData rethrows NodeOperationError instances unchanged', async () => {
	const node = new ReferenceData();
	const expectedError = new NodeOperationError({ name: 'TSM - Reference Data' }, 'already normalized');

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter() { return 'health'; },
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw expectedError;
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Reference Data' }; },
	};

	await assert.rejects(node.execute.call(context), (error) => error === expectedError);
});

test('ReferenceData list groups operation unwraps the REST data envelope', async () => {
	const node = new ReferenceData();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'listGroups' };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ data: [{ id: 3, name: 'Network Operations' }] });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Reference Data' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: [{ id: 3, name: 'Network Operations' }], pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/groups',
			method: 'GET',
			json: true,
			body: undefined,
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});
