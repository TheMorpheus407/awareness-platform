import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Users } from './Users';
import apiClient from '../services/api';
import { format } from 'date-fns';

// Mock the API client
vi.mock('../services/api', () => ({
  default: {
    getUsers: vi.fn(),
  },
}));

// Mock the components
vi.mock('../components/Common', () => ({
  LoadingSpinner: ({ size, className }: any) => (
    <div data-testid="loading-spinner" className={className}>Loading...</div>
  ),
  ErrorMessage: ({ message, className }: any) => (
    <div data-testid="error-message" className={className}>{message}</div>
  ),
}));

const mockUsers = {
  items: [
    {
      id: 1,
      email: 'admin@company.com',
      username: 'admin',
      full_name: 'Admin User',
      first_name: 'Admin',
      last_name: 'User',
      role: 'admin',
      is_active: true,
      is_verified: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      email: 'manager@company.com',
      username: 'manager',
      full_name: 'Manager User',
      first_name: 'Manager',
      last_name: 'User',
      role: 'company_admin',
      is_active: true,
      is_verified: true,
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
    {
      id: 3,
      email: 'user@company.com',
      username: 'regularuser',
      full_name: 'Regular User',
      first_name: 'Regular',
      last_name: 'User',
      role: 'user',
      is_active: false,
      is_verified: false,
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    },
  ],
  total: 3,
  pages: 1,
  page: 1,
  size: 20,
};

const renderUsers = () => {
  return render(
    <BrowserRouter>
      <Users />
    </BrowserRouter>
  );
};

describe('Users Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays loading state initially', () => {
    (apiClient.getUsers as any).mockImplementation(() => 
      new Promise(() => {}) // Never resolves to keep loading
    );

    renderUsers();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    const errorMessage = 'Failed to fetch users';
    (apiClient.getUsers as any).mockRejectedValueOnce({
      detail: errorMessage,
    });

    renderUsers();

    await waitFor(() => {
      expect(screen.getByTestId('error-message')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('displays users list when data is loaded', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument();
      expect(screen.getByText('Manage your platform users')).toBeInTheDocument();
      
      // Check if all users are displayed
      expect(screen.getByText('Admin User')).toBeInTheDocument();
      expect(screen.getByText('Manager User')).toBeInTheDocument();
      expect(screen.getByText('Regular User')).toBeInTheDocument();
    });
  });

  it('displays user details correctly', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      // Check emails
      expect(screen.getByText('admin@company.com')).toBeInTheDocument();
      expect(screen.getByText('manager@company.com')).toBeInTheDocument();
      expect(screen.getByText('user@company.com')).toBeInTheDocument();

      // Check roles with proper formatting
      expect(screen.getByText('admin')).toBeInTheDocument();
      expect(screen.getByText('company admin')).toBeInTheDocument();
      expect(screen.getByText('user')).toBeInTheDocument();

      // Check status badges
      const activeBadges = screen.getAllByText('Active');
      const inactiveBadges = screen.getAllByText('Inactive');
      expect(activeBadges).toHaveLength(2);
      expect(inactiveBadges).toHaveLength(1);
    });
  });

  it('filters users based on search term', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search users...');
    
    // Search by name
    fireEvent.change(searchInput, { target: { value: 'admin' } });
    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.queryByText('Regular User')).not.toBeInTheDocument();

    // Search by email
    fireEvent.change(searchInput, { target: { value: 'manager@' } });
    expect(screen.getByText('Manager User')).toBeInTheDocument();
    expect(screen.queryByText('Admin User')).not.toBeInTheDocument();

    // Search by username
    fireEvent.change(searchInput, { target: { value: 'regularuser' } });
    expect(screen.getByText('Regular User')).toBeInTheDocument();
    expect(screen.queryByText('Admin User')).not.toBeInTheDocument();

    // Clear search
    fireEvent.change(searchInput, { target: { value: '' } });
    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.getByText('Manager User')).toBeInTheDocument();
    expect(screen.getByText('Regular User')).toBeInTheDocument();
  });

  it('displays user avatars with correct initials', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      const avatars = screen.getAllByText(/^[A-Z]$/);
      expect(avatars).toHaveLength(3);
      expect(avatars[0]).toHaveTextContent('A'); // Admin User
      expect(avatars[1]).toHaveTextContent('M'); // Manager User
      expect(avatars[2]).toHaveTextContent('R'); // Regular User
    });
  });

  it('formats dates correctly', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      expect(screen.getByText('Jan 1, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 2, 2024')).toBeInTheDocument();
      expect(screen.getByText('Jan 3, 2024')).toBeInTheDocument();
    });
  });

  it('displays action buttons for each user', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      // Should have 3 sets of action buttons (3 users)
      const editButtons = screen.getAllByRole('button', { name: '' }).filter(
        btn => btn.querySelector('.lucide-edit')
      );
      const deleteButtons = screen.getAllByRole('button', { name: '' }).filter(
        btn => btn.querySelector('.lucide-trash-2')
      );
      const moreButtons = screen.getAllByRole('button', { name: '' }).filter(
        btn => btn.querySelector('.lucide-more-vertical')
      );

      expect(editButtons).toHaveLength(3);
      expect(deleteButtons).toHaveLength(3);
      expect(moreButtons).toHaveLength(3);
    });
  });

  it('displays add user button', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      const addButton = screen.getByText('Add User');
      expect(addButton).toBeInTheDocument();
      expect(addButton.closest('button')).toHaveClass('btn-primary');
    });
  });

  it('handles pagination correctly', async () => {
    const multiPageUsers = {
      ...mockUsers,
      total: 50,
      pages: 3,
      page: 1,
    };

    (apiClient.getUsers as any).mockResolvedValueOnce(multiPageUsers);

    renderUsers();

    await waitFor(() => {
      expect(screen.getByText('Showing 1 to 20 of 50 users')).toBeInTheDocument();
      
      const prevButton = screen.getByText('Previous');
      const nextButton = screen.getByText('Next');
      
      expect(prevButton).toBeDisabled();
      expect(nextButton).not.toBeDisabled();
    });

    // Click next page
    fireEvent.click(screen.getByText('Next'));
    
    expect(apiClient.getUsers).toHaveBeenCalledWith(2, 20);
  });

  it('disables next button on last page', async () => {
    const lastPageUsers = {
      ...mockUsers,
      total: 50,
      pages: 3,
      page: 3,
    };

    (apiClient.getUsers as any).mockResolvedValueOnce(lastPageUsers);

    renderUsers();

    await waitFor(() => {
      const prevButton = screen.getByText('Previous');
      const nextButton = screen.getByText('Next');
      
      expect(prevButton).not.toBeDisabled();
      expect(nextButton).toBeDisabled();
    });
  });

  it('does not display pagination for single page', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      expect(screen.queryByText('Previous')).not.toBeInTheDocument();
      expect(screen.queryByText('Next')).not.toBeInTheDocument();
    });
  });

  it('applies correct role badge colors', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      const adminBadge = screen.getByText('admin').closest('span');
      const companyAdminBadge = screen.getByText('company admin').closest('span');
      const userBadge = screen.getByText('user').closest('span');

      expect(adminBadge).toHaveClass('bg-purple-100', 'text-purple-800');
      expect(companyAdminBadge).toHaveClass('bg-blue-100', 'text-blue-800');
      expect(userBadge).toHaveClass('bg-gray-100', 'text-gray-800');
    });
  });

  it('applies correct status badge colors', async () => {
    (apiClient.getUsers as any).mockResolvedValueOnce(mockUsers);

    renderUsers();

    await waitFor(() => {
      const activeBadges = screen.getAllByText('Active');
      const inactiveBadges = screen.getAllByText('Inactive');

      activeBadges.forEach(badge => {
        expect(badge.closest('span')).toHaveClass('bg-green-100', 'text-green-800');
      });

      inactiveBadges.forEach(badge => {
        expect(badge.closest('span')).toHaveClass('bg-red-100', 'text-red-800');
      });
    });
  });

  it('handles users without full_name gracefully', async () => {
    const usersWithoutFullName = {
      ...mockUsers,
      items: [
        {
          ...mockUsers.items[0],
          full_name: null,
        },
      ],
    };

    (apiClient.getUsers as any).mockResolvedValueOnce(usersWithoutFullName);

    renderUsers();

    await waitFor(() => {
      // Should display username when full_name is null
      expect(screen.getByText('admin')).toBeInTheDocument();
    });
  });

  it('refetches data when page changes', async () => {
    const multiPageUsers = {
      ...mockUsers,
      total: 50,
      pages: 3,
      page: 1,
    };

    (apiClient.getUsers as any)
      .mockResolvedValueOnce(multiPageUsers)
      .mockResolvedValueOnce({ ...multiPageUsers, page: 2 });

    renderUsers();

    await waitFor(() => {
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(apiClient.getUsers).toHaveBeenCalledTimes(2);
      expect(apiClient.getUsers).toHaveBeenLastCalledWith(2, 20);
    });
  });
});