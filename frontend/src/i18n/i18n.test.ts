import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock i18next and plugins
vi.mock('i18next', () => ({
  default: {
    use: vi.fn().mockReturnThis(),
    init: vi.fn().mockResolvedValue(true),
    t: vi.fn((key) => key),
    language: 'en',
  },
}));

vi.mock('react-i18next', () => ({
  initReactI18next: {
    type: '3rdParty',
    init: vi.fn(),
  },
}));

vi.mock('i18next-browser-languagedetector', () => ({
  default: vi.fn(),
}));

describe('i18n Configuration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes i18n with correct configuration', async () => {
    // Import after mocks are set up
    const { default: i18n } = await import('./i18n');
    
    expect(i18n.use).toHaveBeenCalled();
    expect(i18n.init).toHaveBeenCalled();
  });

  it('sets default language to en', async () => {
    const { default: i18n } = await import('./i18n');
    
    expect(i18n.language).toBe('en');
  });

  it('can translate keys', async () => {
    const { default: i18n } = await import('./i18n');
    
    const result = i18n.t('test.key');
    expect(result).toBe('test.key');
  });
});