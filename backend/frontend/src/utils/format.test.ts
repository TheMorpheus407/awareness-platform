import { describe, it, expect } from 'vitest';
import {
  formatDate,
  formatPercentage,
  formatNumber,
  formatDuration,
  formatFileSize,
  formatDateTime,
  formatRelativeTime,
} from './format';

describe('Format Utils', () => {
  describe('formatDate', () => {
    it('formats date correctly', () => {
      const dateStr = '2024-01-15T10:30:00Z';
      const result = formatDate(dateStr);
      expect(result).toBeTruthy();
      expect(result).toContain('2024');
    });

    it('formats date string correctly', () => {
      const result = formatDate('2024-01-15');
      expect(result).toBeTruthy();
      expect(result).toContain('2024');
    });
  });

  describe('formatDateTime', () => {
    it('formats date and time correctly', () => {
      const result = formatDateTime('2024-01-15T10:30:00Z');
      expect(result).toBeTruthy();
      expect(result).toContain('2024');
    });
  });

  describe('formatPercentage', () => {
    it('formats percentage correctly', () => {
      expect(formatPercentage(12.34)).toBe('12.3%');
      expect(formatPercentage(100)).toBe('100.0%');
    });

    it('handles decimal values', () => {
      expect(formatPercentage(12.3456)).toBe('12.3%');
      expect(formatPercentage(0.1)).toBe('0.1%');
    });
  });

  describe('formatNumber', () => {
    it('formats large numbers correctly', () => {
      expect(formatNumber(1234567)).toBe('1,234,567');
      expect(formatNumber(1000)).toBe('1,000');
    });

    it('handles decimals', () => {
      expect(formatNumber(1234.567)).toBe('1,234.567');
    });
  });

  describe('formatDuration', () => {
    it('formats seconds correctly', () => {
      expect(formatDuration(45)).toBe('45s');
      expect(formatDuration(90)).toBe('1m 30s');
    });

    it('formats minutes correctly', () => {
      expect(formatDuration(120)).toBe('2m');
      expect(formatDuration(3661)).toBe('1h 1m');
    });

    it('formats hours correctly', () => {
      expect(formatDuration(7200)).toBe('2h');
      expect(formatDuration(3660)).toBe('1h 1m');
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes correctly', () => {
      expect(formatFileSize(500)).toBe('500 Bytes');
      expect(formatFileSize(0)).toBe('0 Bytes');
    });

    it('formats KB correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(2048)).toBe('2 KB');
    });

    it('formats MB correctly', () => {
      expect(formatFileSize(1048576)).toBe('1 MB');
    });

    it('formats GB correctly', () => {
      expect(formatFileSize(1073741824)).toBe('1 GB');
    });
  });

  describe('formatRelativeTime', () => {
    it('formats recent time as "just now"', () => {
      const now = new Date();
      expect(formatRelativeTime(now.toISOString())).toBe('just now');
    });

    it('formats time in minutes', () => {
      const date = new Date(Date.now() - 5 * 60 * 1000); // 5 minutes ago
      expect(formatRelativeTime(date.toISOString())).toBe('5 minutes ago');
    });

    it('formats time in hours', () => {
      const date = new Date(Date.now() - 2 * 60 * 60 * 1000); // 2 hours ago
      expect(formatRelativeTime(date.toISOString())).toBe('2 hours ago');
    });
  });
});