import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Companies } from './Companies';
import * as apiModule from '../services/api';
import { useApi } from '../hooks/useApi';

// Mock the API module
vi.mock('../services/api', () => ({
  default: {
    getCompanies: vi.fn(),
    createCompany: vi.fn(),
    updateCompany: vi.fn(),
    deleteCompany: vi.fn(),
  },
}));

// Mock useApi hook
vi.mock('../hooks/useApi', () => ({
  useApi: vi.fn(() => ({
    data: null,
    loading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

// Mock date-fns
vi.mock('date-fns', () => ({
  format: vi.fn((date) => 'Jan 1, 2024'),
}));

describe('Companies Component', () => {
  const mockCompanies = {
    items: [
      {
        id: '1',
        name: 'Tech Corp',
        domain: 'techcorp.com',
        size: 'medium',
        subscription_tier: 'professional',
        max_users: 100,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: '2',
        name: 'Small Startup',
        domain: 'startup.io',
        size: 'small',
        subscription_tier: 'free',
        max_users: 10,
        is_active: false,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ],
    total: 2,
    page: 1,
    size: 20,
    pages: 1,
  };

  const mockUseApi = (data = mockCompanies, loading = false, error = null) => {
    vi.mocked(useApi).mockReturnValue({
      data,
      loading,
      error,
      refetch: vi.fn(),
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderCompanies = () => {
    return render(
      <BrowserRouter>
        <Companies />
      </BrowserRouter>
    );
  };

  it('renders companies page title and subtitle', () => {
    mockUseApi();
    renderCompanies();

    expect(screen.getByText('Companies')).toBeInTheDocument();
    expect(screen.getByText('Manage registered companies')).toBeInTheDocument();
  });

  it('displays loading state', () => {
    mockUseApi(null, true);
    renderCompanies();

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays error message when API call fails', () => {
    const errorMessage = 'Failed to fetch companies';
    mockUseApi(null, false, { detail: errorMessage });
    renderCompanies();

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('renders search input', () => {
    mockUseApi();
    renderCompanies();

    const searchInput = screen.getByPlaceholderText('Search companies...');
    expect(searchInput).toBeInTheDocument();
  });

  it('renders add company button', () => {
    mockUseApi();
    renderCompanies();

    const addButton = screen.getByRole('button', { name: /add company/i });
    expect(addButton).toBeInTheDocument();
  });

  it('displays company cards with correct information', () => {
    mockUseApi();
    renderCompanies();

    // First company
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
    expect(screen.getByText('techcorp.com')).toBeInTheDocument();
    expect(screen.getByText('100 max users')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();

    // Second company
    expect(screen.getByText('Small Startup')).toBeInTheDocument();
    expect(screen.getByText('startup.io')).toBeInTheDocument();
    expect(screen.getByText('10 max users')).toBeInTheDocument();
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('filters companies based on search term', async () => {
    mockUseApi();
    const user = userEvent.setup();
    renderCompanies();

    const searchInput = screen.getByPlaceholderText('Search companies...');
    
    // Type search term
    await user.type(searchInput, 'tech');

    // Should only show Tech Corp
    expect(screen.getByText('Tech Corp')).toBeInTheDocument();
    expect(screen.queryByText('Small Startup')).not.toBeInTheDocument();
  });

  it('filters by domain when searching', async () => {
    mockUseApi();
    const user = userEvent.setup();
    renderCompanies();

    const searchInput = screen.getByPlaceholderText('Search companies...');
    
    // Search by domain
    await user.type(searchInput, '.io');

    // Should only show Small Startup
    expect(screen.queryByText('Tech Corp')).not.toBeInTheDocument();
    expect(screen.getByText('Small Startup')).toBeInTheDocument();
  });

  it('displays company initial in avatar', () => {
    mockUseApi();
    renderCompanies();

    expect(screen.getByText('T')).toBeInTheDocument(); // Tech Corp
    expect(screen.getByText('S')).toBeInTheDocument(); // Small Startup
  });

  it('renders edit and delete buttons for each company', () => {
    mockUseApi();
    renderCompanies();

    const editButtons = screen.getAllByRole('button', { name: /edit/i });
    const deleteButtons = screen.getAllByTestId('trash-icon');

    expect(editButtons).toHaveLength(2);
    expect(deleteButtons).toHaveLength(2);
  });

  it('applies correct status styling', () => {
    mockUseApi();
    renderCompanies();

    const activeStatus = screen.getByText('Active');
    const inactiveStatus = screen.getByText('Inactive');

    expect(activeStatus.className).toContain('bg-green-100');
    expect(activeStatus.className).toContain('text-green-800');
    expect(inactiveStatus.className).toContain('bg-red-100');
    expect(inactiveStatus.className).toContain('text-red-800');
  });

  it('shows pagination when there are multiple pages', () => {
    const multiPageData = {
      ...mockCompanies,
      total: 50,
      pages: 3,
    };
    
    mockUseApi(multiPageData);
    renderCompanies();

    expect(screen.getByText('Showing 1 to 20 of 50 companies')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /previous/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /next/i })).toBeInTheDocument();
  });

  it('disables previous button on first page', () => {
    const multiPageData = {
      ...mockCompanies,
      pages: 2,
    };
    
    mockUseApi(multiPageData);
    renderCompanies();

    const previousButton = screen.getByRole('button', { name: /previous/i });
    expect(previousButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    const lastPageData = {
      ...mockCompanies,
      page: 2,
      pages: 2,
    };
    
    mockUseApi(lastPageData);
    renderCompanies();

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  it('handles empty company list', () => {
    const emptyData = {
      items: [],
      total: 0,
      page: 1,
      size: 20,
      pages: 0,
    };
    
    mockUseApi(emptyData);
    renderCompanies();

    // Should not show pagination
    expect(screen.queryByText(/showing/i)).not.toBeInTheDocument();
  });
});