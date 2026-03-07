import { auth } from './firebase';

/**
 * Returns an Authorization Bearer header using the current user's Firebase ID token.
 * Throws if the user is not signed in.
 */
export async function getAuthHeader(): Promise<HeadersInit> {
    const user = auth.currentUser;
    if (!user) throw new Error('Not authenticated');
    const token = await user.getIdToken();
    return { Authorization: `Bearer ${token}` };
}
