import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from './LoginForm';
import { useAuthStore } from '@/store/authStore';
import { api } from '@/services/api';

// Mock dependencies
vi.mock('@/store/authStore');
vi.mock('@/services/api');
vi.mock('react-hot-toast');

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginForm', () => {
  const mockLogin = vi.fn();
  
  beforeEach(() => {
    vi.clearAllMocks();
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: null,
    });
  });

  const renderLoginForm = () => {
    return render(
      <BrowserRouter>
        <LoginForm />
      </BrowserRouter>
    );
  };

  it('renders login form with all required fields', () => {
    renderLoginForm();
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
    expect(screen.getByText(/don't have an account/i)).toBeInTheDocument();
  });

  it('validates email format', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const emailInput = screen.getByLabelText(/email/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    // Test invalid email
    await user.type(emailInput, 'invalid-email');
    await user.click(submitButton);
    
    expect(await screen.findByText(/invalid email format/i)).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('validates required fields', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);
    
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('submits form with valid credentials', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    mockLogin.mockResolvedValueOnce({ success: true });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'SecurePassword123!');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'SecurePassword123!',
      });
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('displays error message on login failure', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const errorMessage = 'Invalid credentials';
    mockLogin.mockRejectedValueOnce(new Error(errorMessage));
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'WrongPassword');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(errorMessage);
    });
  });

  it('disables submit button while loading', () => {
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      isLoading: true,
      error: null,
    });
    
    renderLoginForm();
    
    const submitButton = screen.getByRole('button', { name: /signing in/i });
    expect(submitButton).toBeDisabled();
  });

  it('toggles password visibility', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole('button', { name: /show password/i });
    
    // Initially password should be hidden
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click to show password
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Click again to hide password
    await user.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('navigates to register page when clicking sign up link', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const signUpLink = screen.getByText(/sign up/i);
    await user.click(signUpLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/register');
  });

  it('handles 2FA requirement', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    mockLogin.mockResolvedValueOnce({ requires2FA: true, userId: '123' });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'SecurePassword123!');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/auth/2fa', {
        state: { userId: '123' },
      });
    });
  });

  it('remembers user on checkbox selection', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    const rememberCheckbox = screen.getByLabelText(/remember me/i);
    await user.click(rememberCheckbox);
    
    expect(rememberCheckbox).toBeChecked();
    
    // Submit form
    mockLogin.mockResolvedValueOnce({ success: true });
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'SecurePassword123!');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'SecurePassword123!',
        rememberMe: true,
      });
    });
  });

  it('clears error message when user starts typing', async () => {
    renderLoginForm();
    const user = userEvent.setup();
    
    // Set initial error state
    (useAuthStore as any).mockReturnValue({
      login: mockLogin,
      isLoading: false,
      error: 'Previous error message',
      clearError: vi.fn(),
    });
    
    renderLoginForm();
    
    expect(screen.getByRole('alert')).toHaveTextContent('Previous error message');
    
    const emailInput = screen.getByLabelText(/email/i);
    await user.type(emailInput, 't');
    
    expect(useAuthStore().clearError).toHaveBeenCalled();
  });
});