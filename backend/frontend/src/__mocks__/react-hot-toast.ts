import { vi } from 'vitest';

const toast = {
  success: vi.fn(),
  error: vi.fn(),
  loading: vi.fn(),
  dismiss: vi.fn(),
  promise: vi.fn(),
  custom: vi.fn(),
};

export default toast;