const assert = require('node:assert/strict');
const test = require('node:test');

const { Collection } = require('../dist/nodes/Collection/Collection.node.js');

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
