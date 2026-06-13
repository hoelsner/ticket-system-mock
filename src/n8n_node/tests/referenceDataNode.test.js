const assert = require('node:assert/strict');
const test = require('node:test');

const { ReferenceData } = require('../dist/nodes/ReferenceData/ReferenceData.node.js');

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
