import FormData from 'form-data';
import type {
	ICredentialDataDecryptedObject,
	IDataObject,
	IExecuteFunctions,
	IHookFunctions,
	IHttpRequestMethods,
	ILoadOptionsFunctions,
	IPollFunctions,
	IRequestOptions,
} from 'n8n-workflow';
import { NodeApiError, NodeOperationError } from 'n8n-workflow';

type RequestContext = IExecuteFunctions | IHookFunctions | ILoadOptionsFunctions | IPollFunctions;

type RequestErrorShape = {
	address?: string;
	code?: string;
	cause?: unknown;
	description?: string;
	error?: unknown;
	errno?: string;
	host?: string;
	httpCode?: number | string;
	message?: string;
	port?: number;
	response?: {
		body?: unknown;
		statusCode?: number;
	};
	status?: number;
	statusCode?: number;
	statusMessage?: string;
};

type DataArrayResponse = {
	data: unknown[];
};

function getNodeContext(context: RequestContext): RequestContext & { getNode: () => object } {
	return context as RequestContext & { getNode: () => object };
}

function normalizeBaseUrl(context: RequestContext, rawBaseUrl: unknown): string {
	const baseUrl = String(rawBaseUrl ?? '').trim();
	if (!baseUrl) {
		throw new NodeOperationError(
			getNodeContext(context).getNode(),
			'Ticket System Mock API credentials are missing a Base URL. Enter an absolute URL such as http://webapp:8000 or https://ticket-system.example.com.',
		);
	}

	let parsedUrl: URL;
	try {
		parsedUrl = new URL(baseUrl);
	} catch {
		throw new NodeOperationError(
			getNodeContext(context).getNode(),
			`Ticket System Mock API Base URL "${baseUrl}" is not a valid absolute URL. Use a full http:// or https:// address.`,
		);
	}

	if (parsedUrl.protocol !== 'http:' && parsedUrl.protocol !== 'https:') {
		throw new NodeOperationError(
			getNodeContext(context).getNode(),
			`Ticket System Mock API Base URL "${baseUrl}" must start with http:// or https://.`,
		);
	}

	return baseUrl.replace(/\/$/, '');
}

function readString(value: unknown): string | undefined {
	if (typeof value !== 'string') {
		return undefined;
	}

	const trimmedValue = value.trim();
	return trimmedValue ? trimmedValue : undefined;
}

function extractErrorDetail(value: unknown): string | undefined {
	const stringValue = readString(value);
	if (stringValue) {
		return stringValue;
	}

	if (!value || typeof value !== 'object') {
		return undefined;
	}

	const objectValue = value as Record<string, unknown>;
	for (const key of ['detail', 'message', 'error', 'title']) {
		const candidate = readString(objectValue[key]);
		if (candidate) {
			return candidate;
		}
	}

	return undefined;
}

function getStatusCode(error: RequestErrorShape): number | undefined {
	const rawStatusCode = error.statusCode ?? error.status ?? error.response?.statusCode ?? error.httpCode;
	if (typeof rawStatusCode === 'number') {
		return rawStatusCode;
	}

	if (typeof rawStatusCode === 'string') {
		const parsedStatusCode = Number.parseInt(rawStatusCode, 10);
		return Number.isNaN(parsedStatusCode) ? undefined : parsedStatusCode;
	}

	return undefined;
}

function getErrorCode(error: RequestErrorShape): string | undefined {
	return error.code ?? error.errno ?? ((error.cause as RequestErrorShape | undefined)?.code);
}

function buildHttpErrorMessage(method: IHttpRequestMethods, url: string, statusCode: number, detail?: string): string {
	const requestLabel = `${method} ${url}`;

	if (statusCode === 401) {
		return `Ticket System Mock API request ${requestLabel} failed with 401 Unauthorized. Check the username and password configured in the Ticket System Mock API credentials.`;
	}

	if (statusCode === 403) {
		return `Ticket System Mock API request ${requestLabel} failed with 403 Forbidden. The configured user is authenticated but does not have permission to perform this operation.`;
	}

	if (statusCode === 404) {
		return `Ticket System Mock API request ${requestLabel} failed with 404 Not Found. Check the Base URL and confirm that the target Ticket System Mock instance exposes this API endpoint.`;
	}

	if (statusCode >= 500) {
		return detail
			? `Ticket System Mock API request ${requestLabel} failed with ${statusCode}. The server reported: ${detail}`
			: `Ticket System Mock API request ${requestLabel} failed with ${statusCode}. The Ticket System Mock server returned an internal error.`;
	}

	return detail
		? `Ticket System Mock API request ${requestLabel} failed with ${statusCode}. ${detail}`
		: `Ticket System Mock API request ${requestLabel} failed with ${statusCode}.`;
}

function buildTransportErrorMessage(baseUrl: string, method: IHttpRequestMethods, url: string, error: RequestErrorShape): string {
	const requestLabel = `${method} ${url}`;
	const errorCode = getErrorCode(error);
	const errorDetail =
		extractErrorDetail(error.response?.body) ??
		extractErrorDetail(error.error) ??
		readString(error.description) ??
		readString(error.message) ??
		readString((error.cause as RequestErrorShape | undefined)?.message);
	const targetHost = error.host ?? error.address ?? new URL(baseUrl).host;

	if (errorCode === 'ENOTFOUND' || errorCode === 'EAI_AGAIN') {
		return `Ticket System Mock API request ${requestLabel} could not resolve host "${targetHost}". Check that the Base URL points to a host name reachable from the n8n container.`;
	}

	if (errorCode === 'ECONNREFUSED') {
		return `Ticket System Mock API request ${requestLabel} could not connect to ${baseUrl}. The server refused the connection. Check that the Ticket System Mock instance is running and reachable from n8n.`;
	}

	if (errorCode === 'ETIMEDOUT' || errorCode === 'ESOCKETTIMEDOUT') {
		return `Ticket System Mock API request ${requestLabel} timed out while contacting ${baseUrl}. Check network reachability and whether the Ticket System Mock instance is responding.`;
	}

	const statusCode = getStatusCode(error);
	if (typeof statusCode === 'number') {
		return buildHttpErrorMessage(method, url, statusCode, errorDetail);
	}

	return errorDetail
		? `Ticket System Mock API request ${requestLabel} failed. ${errorDetail}`
		: `Ticket System Mock API request ${requestLabel} failed for an unknown reason.`;
}

export async function ticketingApiRequest(
	context: RequestContext,
	method: IHttpRequestMethods,
	url: string,
	options: {
		body?: IDataObject;
		formData?: FormData;
		headers?: IDataObject;
		qs?: IDataObject;
		json?: boolean;
	} = {},
): Promise<unknown> {
	const credentials = (await context.getCredentials('ticketSystemMockApi')) as ICredentialDataDecryptedObject;
	const baseUrl = normalizeBaseUrl(context, credentials.baseUrl);
	const requestOptions: IRequestOptions = {
		url: `${baseUrl}${url}`,
		method,
		json: options.json ?? true,
		body: options.body,
		formData: options.formData as IDataObject | FormData | undefined,
		headers: options.headers,
		qs: options.qs,
	};
	let response: unknown;
	try {
		response = await context.helpers.requestWithAuthentication.call(
			context,
			'ticketSystemMockApi',
			requestOptions,
		);
	} catch (error) {
		if (error instanceof NodeOperationError && !(error instanceof NodeApiError)) {
			throw error;
		}

		throw new NodeOperationError(
			getNodeContext(context).getNode(),
			buildTransportErrorMessage(baseUrl, method, url, error as RequestErrorShape),
		);
	}

	if (typeof response === 'string') {
		try {
			return JSON.parse(response) as unknown;
		} catch {
			return response;
		}
	}

	return response;
}

export function unwrapDataArrayResponse(context: RequestContext, response: unknown, endpoint: string): unknown[] {
	if (!response || typeof response !== 'object' || !Array.isArray((response as DataArrayResponse).data)) {
		throw new NodeOperationError(
			getNodeContext(context).getNode(),
			`Expected ${endpoint} to return an object with a data array.`,
		);
	}

	return (response as DataArrayResponse).data;
}
