import { useState, useEffect, useCallback } from 'react';
import { AxiosError } from 'axios';
import type { ApiError } from '../types';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: ApiError) => void;
}

export function useApi<T = any>(
  apiCall: () => Promise<T>,
  dependencies: any[] = [],
  options?: UseApiOptions
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

export function useMutation<TData = any, TVariables = any>(
  apiCall: (variables: TVariables) => Promise<TData>,
  options?: UseApiOptions
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