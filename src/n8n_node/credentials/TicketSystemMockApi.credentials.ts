import type { IAuthenticateGeneric, ICredentialTestRequest, ICredentialType, INodeProperties } from 'n8n-workflow';

export class TicketSystemMockApi implements ICredentialType {
	name = 'ticketSystemMockApi';
	icon = {
		light: 'file:favicon.png' as const,
		dark: 'file:favicon.png' as const,
	};
	displayName = 'Ticket System Mock API';
	documentationUrl = 'https://docs.n8n.io/integrations/creating-nodes/build/reference/credentials-files/';
	properties: INodeProperties[] = [
		{
			displayName: 'Base URL',
			name: 'baseUrl',
			type: 'string',
			default: 'http://webapp:8000',
			placeholder: 'http://webapp:8000',
			required: true,
			description: 'Base URL of the Ticket System Mock web application. Use http://webapp:8000 in the local Docker development stack.',
		},
		{
			displayName: 'Username',
			name: 'username',
			type: 'string',
			default: '',
			required: true,
			description: 'Username used for HTTP Basic authentication.',
		},
		{
			displayName: 'Password',
			name: 'password',
			type: 'string',
			typeOptions: {
				password: true,
			},
			default: '',
			required: true,
			description: 'Password used for HTTP Basic authentication.',
		},
		{
			displayName: 'Disable SSL Certificate Validation',
			name: 'skipSslCertificateValidation',
			type: 'boolean',
			default: false,
			description: 'Disable HTTPS certificate validation for trusted development or internal instances that use self-signed certificates.',
		},
	];

	authenticate: IAuthenticateGeneric = {
		type: 'generic',
		properties: {
			auth: {
				username: '={{$credentials.username}}',
				password: '={{$credentials.password}}',
			},
			skipSslCertificateValidation: '={{$credentials.skipSslCertificateValidation}}',
		},
	};

	test: ICredentialTestRequest = {
		request: {
			url: '={{$credentials.baseUrl}}/api/health',
			method: 'GET',
			skipSslCertificateValidation: '={{$credentials.skipSslCertificateValidation}}',
		},
	};
}
