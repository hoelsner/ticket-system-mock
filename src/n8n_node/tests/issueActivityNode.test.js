const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeOperationError } = require('n8n-workflow');

const { IssueActivity } = require('../dist/nodes/IssueActivity/IssueActivity.node.js');

test('IssueActivity adds a comment and optional attachment to an issue', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{ binary: { attachment: { fileName: 'comment.txt', mimeType: 'text/plain' } } }];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'addComment',
				issueId: 11,
				body: 'Investigating the outage.',
				visibility: 'CUSTOMER_VISIBLE',
				commentAttachmentDescription: 'Customer summary',
				commentAttachmentBinaryProperty: 'attachment',
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
				assert.equal(propertyName, 'attachment');
				return { fileName: 'comment.txt', mimeType: 'text/plain' };
			},
			async getBinaryDataBuffer(itemIndex, propertyName) {
				assert.equal(itemIndex, 0);
				assert.equal(propertyName, 'attachment');
				return Buffer.from('comment attachment');
			},
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 8, body: 'Investigating the outage.' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Activity' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 8, body: 'Investigating the outage.' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/comments');
	assert.equal(capturedRequest.requestOptions.method, 'POST');
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Investigating the outage\./);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Customer summary/);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /comment\.txt/);
});

test('IssueActivity updates a comment body and visibility', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'updateComment',
				issueId: 11,
				commentId: 4,
				body: 'Updated customer note.',
				visibility: 'INTERNAL',
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
				return JSON.stringify({ id: 4, body: 'Updated customer note.' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Activity' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 4, body: 'Updated customer note.' }, pairedItem: { item: 0 } }]]);
	assert.deepEqual(capturedRequest.requestOptions.body, {
		body: 'Updated customer note.',
		visibility: 'INTERNAL',
	});
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/comments/4');
	assert.equal(capturedRequest.requestOptions.method, 'PUT');
	assert.equal(capturedRequest.requestOptions.formData, undefined);
});

test('IssueActivity adds an attachment to an issue', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{ binary: { upload: { fileName: 'switch-logs.txt', mimeType: 'text/plain' } } }];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'addAttachment',
				issueId: 11,
				attachmentDescription: 'Switch logs',
				attachmentBinaryProperty: 'upload',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			assertBinaryData(itemIndex, propertyName) {
				assert.equal(propertyName, 'upload');
				return { fileName: 'switch-logs.txt', mimeType: 'text/plain' };
			},
			async getBinaryDataBuffer() {
				return Buffer.from('logs');
			},
			requestWithAuthentication(credentialName, requestOptions) {
				capturedRequest = { credentialName, requestOptions };
				return JSON.stringify({ id: 12 });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Activity' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 12 }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments');
	assert.equal(capturedRequest.requestOptions.method, 'POST');
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Switch logs/);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /switch-logs\.txt/);
});

test('IssueActivity updates attachment metadata without replacing the file', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'updateAttachment',
				issueId: 11,
				attachmentId: 12,
				attachmentDescription: 'Normalized logs',
				replaceFile: false,
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
				return JSON.stringify({ id: 12, description: 'Normalized logs' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Activity' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { id: 12, description: 'Normalized logs' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments/12');
	assert.equal(capturedRequest.requestOptions.method, 'PUT');
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /Normalized logs/);
});

test('IssueActivity deletes an attachment from an issue', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{}];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'deleteAttachment',
				issueId: 11,
				attachmentId: 12,
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
				return JSON.stringify({ status: 'deleted' });
			},
		},
		continueOnFail() {
			return false;
		},
		getNode() {
			return { name: 'TSM - Issue Activity' };
		},
	};

	const result = await node.execute.call(context);

	assert.deepEqual(result, [[{ json: { status: 'deleted' }, pairedItem: { item: 0 } }]]);
	assert.equal(capturedRequest.requestOptions.url, 'http://example.test/api/issues/11/attachments/12');
	assert.equal(capturedRequest.requestOptions.method, 'DELETE');
	assert.equal(capturedRequest.requestOptions.formData, undefined);
});

test('IssueActivity requires a binary property when adding an attachment', async () => {
	const node = new IssueActivity();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'addAttachment',
				issueId: 11,
				attachmentDescription: 'Missing upload',
				attachmentBinaryProperty: '',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue Activity' }; },
	};

	await assert.rejects(node.execute.call(context), /Binary Property is required for Add Attachment/);
});

test('IssueActivity reports a missing binary input item when adding an attachment', async () => {
	const node = new IssueActivity();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'addAttachment',
				issueId: 11,
				attachmentDescription: 'Missing upload',
				attachmentBinaryProperty: 'upload',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue Activity' }; },
	};

	await assert.rejects(node.execute.call(context), /Binary property "upload" was not found/);
});

test('IssueActivity can replace an attachment file during update', async () => {
	const node = new IssueActivity();
	let capturedRequest;

	const context = {
		getInputData() {
			return [{ binary: { replacement: { fileName: 'capture.pcap', mimeType: 'application/vnd.tcpdump.pcap' } } }];
		},
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'updateAttachment',
				issueId: 11,
				attachmentId: 12,
				attachmentDescription: 'Replacement capture',
				replaceFile: true,
				replacementBinaryProperty: 'replacement',
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
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
				return JSON.stringify({ id: 12, description: 'Replacement capture' });
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue Activity' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { id: 12, description: 'Replacement capture' }, pairedItem: { item: 0 } }]]);
	assert.match(capturedRequest.requestOptions.formData.getBuffer().toString('utf8'), /capture\.pcap/);
});

test('IssueActivity continues on failure with a normalized error message', async () => {
	const node = new IssueActivity();

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter(name, itemIndex, defaultValue) {
			assert.equal(itemIndex, 0);
			const parameters = {
				operation: 'deleteAttachment',
				issueId: 11,
				attachmentId: 12,
			};
			return Object.prototype.hasOwnProperty.call(parameters, name) ? parameters[name] : defaultValue;
		},
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw new Error('activity delete failed');
			},
		},
		continueOnFail() { return true; },
		getNode() { return { name: 'TSM - Issue Activity' }; },
	};

	const result = await node.execute.call(context);
	assert.deepEqual(result, [[{ json: { error: 'Ticket System Mock API request DELETE /api/issues/11/attachments/12 failed. activity delete failed' }, pairedItem: { item: 0 } }]]);
});

test('IssueActivity rethrows NodeOperationError instances unchanged', async () => {
	const node = new IssueActivity();
	const expectedError = new NodeOperationError({ name: 'TSM - Issue Activity' }, 'already normalized');

	const context = {
		getInputData() { return [{}]; },
		getNodeParameter() { return 'deleteAttachment'; },
		async getCredentials() { return { baseUrl: 'http://example.test/' }; },
		helpers: {
			requestWithAuthentication() {
				throw expectedError;
			},
		},
		continueOnFail() { return false; },
		getNode() { return { name: 'TSM - Issue Activity' }; },
	};

	await assert.rejects(node.execute.call(context), (error) => error === expectedError);
});
