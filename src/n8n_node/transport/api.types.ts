export interface HealthResponse {
	status: 'ok';
}

export interface AuthenticatedUserResponse {
	id: number;
	username: string;
	display_name: string;
	is_staff: boolean;
	is_superuser: boolean;
}
