import { useState, useEffect, useCallback, DependencyList } from 'react';
import { AxiosError } from 'axios';
import type { ApiError } from '../types';

interface UseApiOptions<T = unknown> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
}

export function useApi<T = unknown>(
  apiCall: () => Promise<T>,
  dependencies: DependencyList = [],
  options?: UseApiOptions<T>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
      options?.onSuccess?.(result);
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      const apiError: ApiError = {
        detail: error.response?.data?.detail || error.message,
        status: error.response?.status,
      };
      setError(apiError);
      options?.onError?.(apiError);
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    execute();
  }, dependencies);

  return { data, loading, error, refetch: execute };
}

export function useMutation<TData = unknown, TVariables = unknown>(
  apiCall: (variables: TVariables) => Promise<TData>,
  options?: UseApiOptions<TData>
) {
  const [data, setData] = useState<TData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const mutate = async (variables: TVariables) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall(variables);
      setData(result);
      options?.onSuccess?.(result);
      return result;
    } catch (err) {
      const error = err as AxiosError<ApiError>;
      const apiError: ApiError = {
        detail: error.response?.data?.detail || error.message,
        status: error.response?.status,
      };
      setError(apiError);
      options?.onError?.(apiError);
      throw apiError;
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, mutate };
}