const assert = require('node:assert/strict');
const test = require('node:test');

const { Category } = require('../dist/nodes/Category/Category.node.js');

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
