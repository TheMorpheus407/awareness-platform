import { render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { Dashboard } from './Dashboard';
import * as apiModule from '../services/api';

// Mock the API module
vi.mock('../services/api', () => ({
  default: {
    getDashboardStats: vi.fn(),
  },
}));

describe('Dashboard Component', () => {
  const mockStats = {
    total_users: 150,
    active_users: 120,
    total_companies: 25,
    courses_completed: 450,
    phishing_campaigns: 12,
    compliance_score: 85,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderDashboard = () => {
    return render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );
  };

  it('renders dashboard title and subtitle', () => {
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(mockStats);
    
    renderDashboard();

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview of your cybersecurity training platform')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    apiModule.default.getDashboardStats = vi.fn().mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve(mockStats), 100))
    );
    
    renderDashboard();

    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  it('displays error message when API call fails', async () => {
    const errorMessage = 'Failed to fetch dashboard stats';
    apiModule.default.getDashboardStats = vi.fn().mockRejectedValue(new Error(errorMessage));
    
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard data/)).toBeInTheDocument();
    });
  });

  it('displays all stats cards with correct data', async () => {
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(mockStats);
    
    renderDashboard();

    await waitFor(() => {
      // Total Users card
      expect(screen.getByText('Total Users')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      
      // Active Users card
      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('120')).toBeInTheDocument();
      expect(screen.getByText('80% of total')).toBeInTheDocument();
      
      // Companies card
      expect(screen.getByText('Companies')).toBeInTheDocument();
      expect(screen.getByText('25')).toBeInTheDocument();
      
      // Courses Completed card
      expect(screen.getByText('Courses Completed')).toBeInTheDocument();
      expect(screen.getByText('450')).toBeInTheDocument();
      
      // Phishing Campaigns card
      expect(screen.getByText('Phishing Campaigns')).toBeInTheDocument();
      expect(screen.getByText('12')).toBeInTheDocument();
      
      // Compliance Score card
      expect(screen.getByText('Compliance Score')).toBeInTheDocument();
      expect(screen.getByText('85%')).toBeInTheDocument();
    });
  });

  it('calculates active users percentage correctly', async () => {
    const statsWithDifferentRatio = {
      ...mockStats,
      total_users: 200,
      active_users: 50,
    };
    
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(statsWithDifferentRatio);
    
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('25% of total')).toBeInTheDocument();
    });
  });

  it('handles zero total users gracefully', async () => {
    const statsWithZeroUsers = {
      ...mockStats,
      total_users: 0,
      active_users: 0,
    };
    
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(statsWithZeroUsers);
    
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('0% of total')).toBeInTheDocument();
    });
  });

  it('renders all icon components', async () => {
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(mockStats);
    
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByTestId('users-icon')).toBeInTheDocument();
      expect(screen.getByTestId('user-check-icon')).toBeInTheDocument();
      expect(screen.getByTestId('building2-icon')).toBeInTheDocument();
      expect(screen.getByTestId('graduation-cap-icon')).toBeInTheDocument();
      expect(screen.getByTestId('mail-icon')).toBeInTheDocument();
      expect(screen.getByTestId('shield-icon')).toBeInTheDocument();
    });
  });

  it('applies correct styling classes to stats cards', async () => {
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(mockStats);
    
    renderDashboard();

    await waitFor(() => {
      const cards = screen.getAllByRole('article');
      expect(cards).toHaveLength(6);
      
      cards.forEach(card => {
        expect(card.className).toContain('card');
      });
    });
  });

  it('retries API call when component remounts', async () => {
    apiModule.default.getDashboardStats = vi.fn().mockResolvedValue(mockStats);
    
    const { unmount } = renderDashboard();
    
    await waitFor(() => {
      expect(apiModule.default.getDashboardStats).toHaveBeenCalledTimes(1);
    });

    unmount();
    renderDashboard();

    await waitFor(() => {
      expect(apiModule.default.getDashboardStats).toHaveBeenCalledTimes(2);
    });
  });
});