const assert = require('node:assert/strict');
const test = require('node:test');

const { IssuePollTrigger } = require('../dist/nodes/IssuePollTrigger/IssuePollTrigger.node.js');

test('IssuePollTrigger schema exposes priority and workflow state as select fields', () => {
	const trigger = new IssuePollTrigger();
	const properties = trigger.description.properties;
	const priorityProperty = properties.find((property) => property.name === 'priority');
	const workflowStateProperty = properties.find((property) => property.name === 'workflowStateFilter');

	assert.equal(priorityProperty?.type, 'options');
	assert.deepEqual(priorityProperty?.options?.map((option) => option.value), ['', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']);
	assert.equal(workflowStateProperty?.type, 'options');
	assert.deepEqual(workflowStateProperty?.options?.map((option) => option.value), [
		'',
		'NEW',
		'TRIAGE',
		'ASSIGNED',
		'IN_PROGRESS',
		'WAITING',
		'RESOLVED',
		'CLOSED',
		'REJECTED',
	]);
});

function createPollContext(options) {
	const staticData = options.staticData ?? {};
	const requestLog = [];

	const context = {
		async getCredentials(name) {
			assert.equal(name, 'ticketSystemMockApi');
			return { baseUrl: 'http://example.test/' };
		},
		helpers: {
			requestWithAuthentication: async function requestWithAuthentication(_credentialName, requestOptions) {
				requestLog.push(requestOptions);
				return options.requestHandler(requestOptions);
			},
		},
		getWorkflowStaticData(scope) {
			assert.equal(scope, 'node');
			return staticData;
		},
		getNodeParameter(name, defaultValue) {
			return Object.prototype.hasOwnProperty.call(options.parameters, name)
				? options.parameters[name]
				: defaultValue;
		},
		getNode() {
			return { name: 'TSM - Issue Poll Trigger' };
		},
	};

	return { context, staticData, requestLog };
}

test('IssuePollTrigger emits matching issues on the first poll by default', async () => {
	const trigger = new IssuePollTrigger();
	const issues = [
		{ id: 5, updated_at: '2026-06-10T10:00:00Z' },
		{ id: 9, updated_at: '2026-06-10T10:00:00Z' },
	];
	const { context, staticData, requestLog } = createPollContext({
		parameters: {
			search: '',
			assignee: '',
			priority: '',
			collection: '',
			category: '',
			workflowStateFilter: '',
			workflowStateLabel: '',
			loadFullIssueDetail: false,
		},
		requestHandler(requestOptions) {
			assert.equal(requestOptions.url, 'http://example.test/api/issues');
			assert.deepEqual(requestOptions.qs, {
				search: '',
				assignee: '',
				priority: '',
				collection: '',
				category: '',
				workflow_state: '',
				workflow_state_label: '',
			});
			return { data: issues };
		},
	});

	const response = await trigger.poll.call(context);

	assert.deepEqual(response, [[
		{ json: { id: 5, updated_at: '2026-06-10T10:00:00Z' } },
		{ json: { id: 9, updated_at: '2026-06-10T10:00:00Z' } },
	]]);
	assert.equal(requestLog.length, 1);
	assert.equal(staticData.lastUpdatedAt, '2026-06-10T10:00:00Z');
	assert.deepEqual(staticData.lastIssueIds, [5, 9]);
});

test('IssuePollTrigger can still suppress existing issues on the first poll when configured', async () => {
	const trigger = new IssuePollTrigger();
	const issues = [
		{ id: 5, updated_at: '2026-06-10T10:00:00Z' },
		{ id: 9, updated_at: '2026-06-10T10:00:00Z' },
	];
	const { context, staticData, requestLog } = createPollContext({
		parameters: {
			search: '',
			assignee: '',
			priority: '',
			collection: '',
			category: '',
			workflowStateFilter: 'ASSIGNED',
			workflowStateLabel: 'Assigned',
			emitExistingOnFirstPoll: false,
			loadFullIssueDetail: false,
		},
		requestHandler(requestOptions) {
			assert.equal(requestOptions.url, 'http://example.test/api/issues');
			assert.deepEqual(requestOptions.qs, {
				search: '',
				assignee: '',
				priority: '',
				collection: '',
				category: '',
				workflow_state: 'ASSIGNED',
				workflow_state_label: 'Assigned',
			});
			return { data: issues };
		},
	});

	const response = await trigger.poll.call(context);

	assert.equal(response, null);
	assert.equal(requestLog.length, 1);
	assert.equal(staticData.lastUpdatedAt, '2026-06-10T10:00:00Z');
	assert.deepEqual(staticData.lastIssueIds, [5, 9]);
});

test('IssuePollTrigger emits newly changed issues and can load full issue detail', async () => {
	const trigger = new IssuePollTrigger();
	const { context, staticData, requestLog } = createPollContext({
		staticData: {
			lastUpdatedAt: '2026-06-10T10:00:00Z',
			lastIssueIds: [5],
		},
		parameters: {
			search: '',
			assignee: '',
			priority: '',
			collection: '',
			category: '',
			workflowStateFilter: '',
			workflowStateLabel: '',
			emitExistingOnFirstPoll: false,
			loadFullIssueDetail: true,
		},
		requestHandler(requestOptions) {
			if (requestOptions.url === 'http://example.test/api/issues') {
				return { data: [
					{ id: 5, updated_at: '2026-06-10T10:00:00Z' },
					{ id: 6, updated_at: '2026-06-10T10:00:00Z' },
					{ id: 7, updated_at: '2026-06-10T11:00:00Z' },
				] };
			}

			if (requestOptions.url === 'http://example.test/api/issues/6') {
				return { id: 6, number: 'OPS-6' };
			}

			if (requestOptions.url === 'http://example.test/api/issues/7') {
				return { id: 7, number: 'OPS-7' };
			}

			throw new Error(`Unexpected URL: ${requestOptions.url}`);
		},
	});

	const response = await trigger.poll.call(context);

	assert.deepEqual(response, [[
		{ json: { id: 6, number: 'OPS-6' } },
		{ json: { id: 7, number: 'OPS-7' } },
	]]);
	assert.equal(requestLog.length, 3);
	assert.equal(staticData.lastUpdatedAt, '2026-06-10T11:00:00Z');
	assert.deepEqual(staticData.lastIssueIds, [7]);
});
