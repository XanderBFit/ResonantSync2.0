import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getAuthHeader } from './apiAuth';
import { auth } from './firebase';

vi.mock('./firebase', () => ({
    auth: {
        currentUser: null
    }
}));

describe('getAuthHeader', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('throws "Not authenticated" if user is not signed in', async () => {
        // By default from mock, currentUser is null
        // Typecast needed because we mocked the structure
        (auth as any).currentUser = null;

        await expect(getAuthHeader()).rejects.toThrow('Not authenticated');
    });

    it('returns Authorization header with ID token if user is signed in', async () => {
        const mockGetIdToken = vi.fn().mockResolvedValue('mocked-token-123');

        (auth as any).currentUser = {
            getIdToken: mockGetIdToken
        };

        const result = await getAuthHeader();

        expect(result).toEqual({ Authorization: 'Bearer mocked-token-123' });
        expect(mockGetIdToken).toHaveBeenCalledTimes(1);
    });
});
