const fs = require('node:fs');
const path = require('node:path');

const nodeAssetDirectories = [
	path.join(__dirname, '..', 'dist', 'nodes', 'ReferenceData'),
	path.join(__dirname, '..', 'dist', 'nodes', 'Collection'),
	path.join(__dirname, '..', 'dist', 'nodes', 'Category'),
	path.join(__dirname, '..', 'dist', 'nodes', 'Issue'),
	path.join(__dirname, '..', 'dist', 'nodes', 'IssueAttachment'),
	path.join(__dirname, '..', 'dist', 'nodes', 'IssueActivity'),
	path.join(__dirname, '..', 'dist', 'nodes', 'IssuePollTrigger'),
	path.join(__dirname, '..', 'dist', 'nodes', 'IssueWebhookTrigger'),
];

const obsoleteCredentialArtifacts = [
	path.join(__dirname, '..', 'dist', 'credentials', 'ItOperationTicketingApi.credentials.js'),
];

const assetCopies = [
	{
		source: path.join(__dirname, '..', 'credentials', 'favicon.png'),
		target: path.join(__dirname, '..', 'dist', 'credentials', 'favicon.png'),
	},
	{
		source: path.join(__dirname, '..', 'credentials', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'credentials', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'ReferenceData', 'ReferenceData.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'ReferenceData', 'ReferenceData.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'ReferenceData', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'ReferenceData', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Collection', 'Collection.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Collection', 'Collection.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Collection', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Collection', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Category', 'Category.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Category', 'Category.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Category', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Category', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Issue', 'Issue.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Issue', 'Issue.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'Issue', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'Issue', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueAttachment', 'IssueAttachment.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueAttachment', 'IssueAttachment.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueAttachment', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueAttachment', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueActivity', 'IssueActivity.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueActivity', 'IssueActivity.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueActivity', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueActivity', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssuePollTrigger', 'IssuePollTrigger.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssuePollTrigger', 'IssuePollTrigger.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssuePollTrigger', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssuePollTrigger', 'ticketsystemmock.svg'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueWebhookTrigger', 'IssueWebhookTrigger.node.json'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueWebhookTrigger', 'IssueWebhookTrigger.node.json'),
	},
	{
		source: path.join(__dirname, '..', 'nodes', 'IssueWebhookTrigger', 'ticketsystemmock.svg'),
		target: path.join(__dirname, '..', 'dist', 'nodes', 'IssueWebhookTrigger', 'ticketsystemmock.svg'),
	},
];


for (const directory of nodeAssetDirectories) {
	if (!fs.existsSync(directory)) {
		continue;
	}

	for (const entry of fs.readdirSync(directory)) {
		if (entry.endsWith('.svg') && entry !== 'ticketsystemmock.svg') {
			fs.unlinkSync(path.join(directory, entry));
		}
	}
}

for (const assetPath of obsoleteCredentialArtifacts) {
	if (fs.existsSync(assetPath)) {
		fs.unlinkSync(assetPath);
	}
}

for (const asset of assetCopies) {
	fs.mkdirSync(path.dirname(asset.target), { recursive: true });
	fs.copyFileSync(asset.source, asset.target);
}
