const assert = require('node:assert/strict');
const test = require('node:test');

const { IssueAttachment } = require('../dist/nodes/IssueAttachment/IssueAttachment.node.js');

test('IssueAttachment adds an issue attachment with the selected binary property', async () => {
	const node = new IssueAttachment();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{ binary: { data: { fileName: 'switch-logs.txt', mimeType: 'text/plain' } } }];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'add',
				issueId: 11,
				attachmentDescription: 'Switch logs',
				attachmentBinaryProperty: 'data',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			assertBinaryData(itemIndex, propertyName) {
				assert.equal(itemIndex, 0);
				assert.equal(propertyName, 'data');
				return { fileName: 'switch-logs.txt', mimeType: 'text/plain' };
			},
			async getBinaryDataBuffer(itemIndex, propertyName) {
				assert.equal(itemIndex, 0);
				assert.equal(propertyName, 'data');
				return Buffer.from('uplink timed out');
			},
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ status: 'created', attachment: { id: 7 } });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'created', attachment: { id: 7 } }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.credentialName, 'ticketSystemMockApi');
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments');
	assert.equal(capturedRequest.requestOptions.method, 'POST');
	assert.equal(capturedRequest.requestOptions.json, true);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Switch logs/);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /switch-logs\.txt/);
});

test('IssueAttachment updates an issue attachment and can replace the file', async () => {
	const node = new IssueAttachment();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{ binary: { replacement: { fileName: 'capture.pcap', mimeType: 'application/vnd.tcpdump.pcap' } } }];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'update',
				issueId: 11,
				attachmentId: 7,
				attachmentDescription: 'Updated packet capture',
				replaceFile: true,
				replacementBinaryProperty: 'replacement',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			assertBinaryData(itemIndex, propertyName) {
				assert.equal(itemIndex, 0);
				assert.equal(propertyName, 'replacement');
				return { fileName: 'capture.pcap', mimeType: 'application/vnd.tcpdump.pcap' };
			},
			async getBinaryDataBuffer(itemIndex, propertyName) {
				assert.equal(itemIndex, 0);
				assert.equal(propertyName, 'replacement');
				return Buffer.from('pcap-bytes');
			},
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ status: 'updated', attachment: { id: 7 } });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'updated', attachment: { id: 7 } }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.credentialName, 'ticketSystemMockApi');
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments/7');
	assert.equal(capturedRequest.requestOptions.method, 'PUT');
	assert.equal(capturedRequest.requestOptions.json, true);
	assert.equal(capturedRequest.requestOptions.body, undefined);
	assert.equal(capturedRequest.requestOptions.headers, undefined);
	assert.equal(capturedRequest.requestOptions.qs, undefined);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Updated packet capture/);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /capture\.pcap/);
});

test('IssueAttachment deletes an issue attachment', async () => {
	const node = new IssueAttachment();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'delete',
				issueId: 11,
				attachmentId: 7,
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
				return JSON.stringify({ status: 'deleted', filename: 'capture.pcap' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'deleted', filename: 'capture.pcap' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.credentialName, 'ticketSystemMockApi');
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments/7');
	assert.equal(capturedRequest.requestOptions.method, 'DELETE');
	assert.equal(capturedRequest.requestOptions.json, true);
	assert.equal(capturedRequest.requestOptions.formData, undefined);
});

test('IssueAttachment requires a binary property when adding an attachment', async () => {
	const node = new IssueAttachment();

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'add',
				issueId: 11,
				attachmentDescription: 'Missing file',
				attachmentBinaryProperty: '',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() {
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	await assert.rejects(node.execute.call(context), /Binary Property is required for Add/);
});

test('IssueAttachment requires a replacement binary property when replacing a file', async () => {
	const node = new IssueAttachment();

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'update',
				issueId: 11,
				attachmentId: 7,
				attachmentDescription: 'Updated capture',
				replaceFile: true,
				replacementBinaryProperty: '',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() {
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	await assert.rejects(node.execute.call(context), /Replacement Binary Property is required/);
});

test('IssueAttachment continueOnFail returns an error item for unexpected failures', async () => {
	const node = new IssueAttachment();

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = { operation: 'delete', issueId: 11, attachmentId: 7 };
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() {
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication() {
				throw new Error('delete failed');
			},
		},
		continueOnFail() {
			return true;
		},
		getNode() {
			return { name: 'TSM - Issue Attachment' };
		},
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request DELETE /api/issues/11/attachments/7 failed. delete failed' }, pairedItem: { item: 0 } }]]);
});

test('IssueAttachment reports a missing binary input item when adding', async () => {
	const node = new IssueAttachment();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'add',
				issueId: 11,
				attachmentDescription: 'Missing file',
				attachmentBinaryProperty: 'data',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue Attachment' }; },
	};

	await assert.rejects(node.execute.call(context), /Binary property "data" was not found/);
});
