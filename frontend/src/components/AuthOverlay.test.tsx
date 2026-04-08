import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthOverlay } from './AuthOverlay';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth';

// Mock firebase/auth
vi.mock('firebase/auth', () => ({
    signInWithEmailAndPassword: vi.fn(),
    createUserWithEmailAndPassword: vi.fn(),
}));

// Mock ../lib/firebase
vi.mock('../lib/firebase', () => ({
    auth: {
        currentUser: null
    }
}));

describe('AuthOverlay', () => {
    const mockOnClose = vi.fn();
    const mockOnSuccess = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders login mode by default', () => {
        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        expect(screen.getByText('Welcome Back')).toBeDefined();
        expect(screen.getByText('Log in to access your saved Publisher templates.')).toBeDefined();
        expect(screen.getByRole('button', { name: 'Sign In' })).toBeDefined();
    });

    it('switches to signup mode', () => {
        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        const switchButton = screen.getByRole('button', { name: 'Sign Up' });
        fireEvent.click(switchButton);

        // Both heading and button have 'Create Account' text, so we check for both
        expect(screen.getAllByText('Create Account')).toHaveLength(2);
        expect(screen.getByText('Sign up to build your Metadata default templates.')).toBeDefined();
        expect(screen.getByRole('button', { name: 'Create Account' })).toBeDefined();
    });

    it('calls signInWithEmailAndPassword and onSuccess on successful login', async () => {
        (signInWithEmailAndPassword as any).mockResolvedValueOnce({});

        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        fireEvent.change(screen.getByPlaceholderText('you@domain.com'), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } });

        const submitButton = screen.getByRole('button', { name: 'Sign In' });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(signInWithEmailAndPassword).toHaveBeenCalledWith(expect.anything(), 'test@example.com', 'password123');
            expect(mockOnSuccess).toHaveBeenCalled();
        });
    });

    it('shows error message on login failure', async () => {
        (signInWithEmailAndPassword as any).mockRejectedValueOnce(new Error('Invalid credentials'));

        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        fireEvent.change(screen.getByPlaceholderText('you@domain.com'), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } });

        const submitButton = screen.getByRole('button', { name: 'Sign In' });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText('Invalid credentials')).toBeDefined();
        });
    });

    it('calls createUserWithEmailAndPassword and onSuccess on successful signup', async () => {
        (createUserWithEmailAndPassword as any).mockResolvedValueOnce({});

        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        // Switch to signup
        fireEvent.click(screen.getByRole('button', { name: 'Sign Up' }));

        fireEvent.change(screen.getByPlaceholderText('you@domain.com'), { target: { value: 'new@example.com' } });
        fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'password123' } });

        const submitButton = screen.getByRole('button', { name: 'Create Account' });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(createUserWithEmailAndPassword).toHaveBeenCalledWith(expect.anything(), 'new@example.com', 'password123');
            expect(mockOnSuccess).toHaveBeenCalled();
        });
    });

    it('calls onClose when close button is clicked', () => {
        render(<AuthOverlay onClose={mockOnClose} onSuccess={mockOnSuccess} />);

        const closeButton = screen.getByLabelText('Close');
        fireEvent.click(closeButton);

        expect(mockOnClose).toHaveBeenCalled();
    });
});
