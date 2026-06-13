export const apiPaths = {
	health: '/api/health',
	authMe: '/api/auth/me',
	profileMe: '/api/profile/me',
	groups: '/api/groups',
	users: '/api/users',
	collections: '/api/collections',
	categories: '/api/categories',
} as const;

export type ReferenceDataOperation =
	| 'health'
	| 'authMe'
	| 'profileMe'
	| 'userProfile'
	| 'listGroups'
	| 'listUsers';
