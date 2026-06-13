const assert = require('node:assert/strict');
const test = require('node:test');
const { NodeApiError } = require('n8n-workflow');

const { ticketingApiRequest, unwrapDataArrayResponse } = require('../dist/transport/request.js');

function createRequestContext(baseUrl, responder) {
	let capturedCall;

	const context = {
		getNode() {
			return { name: 'Ticket System Mock API' };
		},
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl };
		},
		helpers: {
			requestWithAuthentication: function requestWithAuthentication(credentialName, requestOptions) {
				capturedCall = {
					thisValue: this,
					credentialName,
					requestOptions,
				};
				return responder(requestOptions);
			},
		},
	};

	return {
		context,
		getCapturedCall() {
			return capturedCall;
		},
	};
}

test('ticketingApiRequest builds the authenticated request and parses JSON strings', async () => {
	const { context, getCapturedCall } = createRequestContext('http://example.test/', async () => '{"ok":true}');

	const response = await ticketingApiRequest(context, 'POST', '/api/issues', {
		body: { title: 'Example' },
		headers: { 'x-test-header': 'value' },
		qs: { priority: 'high' },
	});

	assert.deepEqual(response, { ok: true });

	const capturedCall = getCapturedCall();
	assert.equal(capturedCall.thisValue, context);
	assert.equal(capturedCall.credentialName, 'ticketSystemMockApi');
	assert.deepEqual(capturedCall.requestOptions, {
		url: 'http://example.test/api/issues',
		method: 'POST',
		json: true,
		body: { title: 'Example' },
		formData: undefined,
		headers: { 'x-test-header': 'value' },
		qs: { priority: 'high' },
	});
});

test('ticketingApiRequest returns raw string responses that are not JSON', async () => {
	const { context } = createRequestContext('http://example.test', async () => 'plain-text');

	const response = await ticketingApiRequest(context, 'GET', '/api/health', { json: false });

	assert.equal(response, 'plain-text');
});

test('unwrapDataArrayResponse returns the data array from wrapped list responses', () => {
	const { context } = createRequestContext('http://example.test', async () => ({}));

	const response = unwrapDataArrayResponse(context, { data: [{ id: 1 }] }, '/api/issues');

	assert.deepEqual(response, [{ id: 1 }]);
});

test('unwrapDataArrayResponse rejects malformed wrapped list responses', async () => {
	const { context } = createRequestContext('http://example.test', async () => ({}));

	assert.throws(
		() => unwrapDataArrayResponse(context, [{ id: 1 }], '/api/issues'),
		(error) => {
			assert.match(error.message, /object with a data array/i);
			return true;
		},
	);
});

test('ticketingApiRequest rejects an invalid base URL with actionable guidance', async () => {
	const { context, getCapturedCall } = createRequestContext('webapp:8000', async () => {
		throw new Error('request should not be attempted');
	});

	await assert.rejects(
		ticketingApiRequest(context, 'GET', '/api/issues'),
		(error) => {
			assert.match(error.message, /Base URL "webapp:8000" must start with http:\/\/ or https:\/\//);
			assert.match(error.message, /http:\/\/ or https:\/\//);
			return true;
		},
	);

	assert.equal(getCapturedCall(), undefined);
});

test('ticketingApiRequest explains connection refused failures', async () => {
	const { context } = createRequestContext('http://webapp:8000', async () => {
		const error = new Error('connect ECONNREFUSED 172.18.0.3:8000');
		error.code = 'ECONNREFUSED';
		return Promise.reject(error);
	});

	await assert.rejects(
		ticketingApiRequest(context, 'GET', '/api/issues'),
		(error) => {
			assert.match(error.message, /could not connect to http:\/\/webapp:8000/i);
			assert.match(error.message, /server refused the connection/i);
			assert.match(error.message, /reachable from n8n/i);
			return true;
		},
	);
});

test('ticketingApiRequest explains unauthorized responses', async () => {
	const { context } = createRequestContext('http://example.test', async () => {
		throw {
			statusCode: 401,
			response: {
				statusCode: 401,
				body: { detail: 'Invalid credentials' },
			},
		};
	});

	await assert.rejects(
		ticketingApiRequest(context, 'GET', '/api/issues'),
		(error) => {
			assert.match(error.message, /401 Unauthorized/);
			assert.match(error.message, /username and password/i);
			return true;
		},
	);
});

test('ticketingApiRequest explains forbidden responses', async () => {
	const { context } = createRequestContext('http://example.test', async () => {
		throw {
			statusCode: 403,
			response: {
				statusCode: 403,
				body: { detail: 'You do not have permission to perform this action.' },
			},
		};
	});

	await assert.rejects(
		ticketingApiRequest(context, 'POST', '/api/issues'),
		(error) => {
			assert.match(error.message, /403 Forbidden/);
			assert.match(error.message, /does not have permission/i);
			return true;
		},
	);
});

test('ticketingApiRequest surfaces server-side API details', async () => {
	const { context } = createRequestContext('http://example.test', async () => {
		throw {
			statusCode: 500,
			response: {
				statusCode: 500,
				body: { detail: 'Database temporarily unavailable' },
			},
		};
	});

	await assert.rejects(
		ticketingApiRequest(context, 'GET', '/api/issues'),
		(error) => {
			assert.match(error.message, /failed with 500/);
			assert.match(error.message, /Database temporarily unavailable/);
			return true;
		},
	);
});

test('ticketingApiRequest rewrites NodeApiError permission failures with clearer guidance', async () => {
	const { context } = createRequestContext('http://example.test', async () => {
		throw new NodeApiError(
			context.getNode(),
			{
				httpCode: '403',
				description: 'The authenticated user cannot access this resource.',
				message: 'Forbidden',
			},
		);
	});

	await assert.rejects(
		ticketingApiRequest(context, 'GET', '/api/issues'),
		(error) => {
			assert.match(error.message, /403 Forbidden/);
			assert.match(error.message, /does not have permission/i);
			return true;
		},
	);
});
