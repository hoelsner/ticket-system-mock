const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeOperationError } = require('n8n-workflow');

const { Category } = require('../dist/nodes/Category/Category.node.js');

test('Category list operation unwraps the REST data envelope', async () => {
	const node = new Category();
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
				return JSON.stringify({ data: [{ id: 9, name: 'Network' }] });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Category' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: [{ id: 9, name: 'Network' }], pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/categories',
			method: 'GET',
			json: true,
			body: undefined,
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});

test('Category create operation forwards category mutation fields to the API', async () => {
	const node = new Category();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'create',
				categoryName: 'Access',
				categoryCode: 'ACCESS',
				categoryDescription: 'Access requests',
				categoryIsActive: true,
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
				return JSON.stringify({ id: 10, code: 'ACCESS' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Category' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 10, code: 'ACCESS' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions, {
		url: 'http://example.test/api/categories',
		method: 'POST',
		json: true,
		body: {
			name: 'Access',
			code: 'ACCESS',
			description: 'Access requests',
			is_active: true,
		},
		formData: undefined,
		headers: undefined,
		qs: undefined,
	});
});

test('Category continueOnFail returns an error item for unexpected failures', async () => {
	const node = new Category();

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
				throw new Error('network broke');
			},
		},
		continueOnFail() { return true; },
		getNode() { return { name: 'TSM - Category' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request GET /api/categories failed. network broke' }, pairedItem: { item: 0 } }]]);
});

test('Category rethrows NodeOperationError instances unchanged', async () => {
	const node = new Category();
	const expectedError = new NodeOperationError({ name: 'TSM - Category' }, 'already normalized');

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
		getNode() { return { name: 'TSM - Category' }; },
	};

	await assert.rejects(node.execute.call(context), (error) => error === expectedError);
});

test('Category update operation forwards category mutation fields to the API', async () => {
	const node = new Category();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'update',
				categoryId: 4,
				categoryName: 'Security Operations',
				categoryCode: 'SECURITY',
				categoryDescription: 'Updated security issues',
				categoryIsActive: false,
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
				return JSON.stringify({ status: 'updated', category: { id: 4 } });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Category' }; },
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'updated', category: { id: 4 } }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest, {
		credentialName: 'ticketSystemMockApi',
		requestOptions: {
			url: 'http://example.test/api/categories/4',
			method: 'PUT',
			json: true,
			body: {
				name: 'Security Operations',
				code: 'SECURITY',
				description: 'Updated security issues',
				is_active: false,
			},
			formData: undefined,
			headers: undefined,
			qs: undefined,
		},
	});
});
