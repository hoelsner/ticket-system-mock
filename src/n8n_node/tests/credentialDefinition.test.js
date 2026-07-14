const assert = require('node:assert/strict');
const test = require('node:test');

const { TicketSystemMockApi } = require('../dist/credentials/TicketSystemMockApi.credentials.js');

test('TicketSystemMockApi uses a parser-safe test URL expression', () => {
	const credential = new TicketSystemMockApi();

	assert.equal(credential.name, 'ticketSystemMockApi');
	assert.equal(credential.displayName, 'Ticket System Mock API');
	assert.deepEqual(credential.icon, {
		light: 'file:favicon.png',
		dark: 'file:favicon.png',
	});
	assert.deepEqual(credential.authenticate, {
		type: 'generic',
		properties: {
			auth: {
				username: '={{$credentials.username}}',
				password: '={{$credentials.password}}',
			},
			skipSslCertificateValidation: '={{$credentials.skipSslCertificateValidation}}',
		},
	});
	assert.deepEqual(credential.test, {
		request: {
			url: '={{$credentials.baseUrl}}/api/health',
			method: 'GET',
			skipSslCertificateValidation: '={{$credentials.skipSslCertificateValidation}}',
		},
	});

	const sslToggle = credential.properties.find((property) => property.name === 'skipSslCertificateValidation');
	assert.deepEqual(sslToggle, {
		displayName: 'Disable SSL Certificate Validation',
		name: 'skipSslCertificateValidation',
		type: 'boolean',
		default: false,
		description: 'Disable HTTPS certificate validation for trusted development or internal instances that use self-signed certificates.',
	});
});
