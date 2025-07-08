import { vi } from 'vitest';

export const useApi = vi.fn(() => ({
  data: null,
  loading: false,
  error: null,
  refetch: vi.fn(),
}));

export const useMutation = vi.fn(() => ({
  data: null,
  loading: false,
  error: null,
  mutate: vi.fn(),
}));