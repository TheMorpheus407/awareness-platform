import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export const usePageTitle = (titleKey: string, params?: Record<string, string>) => {
  const { t, i18n } = useTranslation();
  
  useEffect(() => {
    const translatedTitle = t(titleKey, params);
    document.title = `${translatedTitle} | ${t('app.name', 'Cybersecurity Awareness Platform')}`;
    
    // Update meta description if translation key exists
    const descriptionKey = `${titleKey}.description`;
    const description = t(descriptionKey, { defaultValue: '' });
    if (description) {
      const metaDescription = document.querySelector('meta[name="description"]');
      if (metaDescription) {
        metaDescription.setAttribute('content', description);
      }
    }
    
    // Update language attribute
    document.documentElement.lang = i18n.language;
  }, [titleKey, params, t, i18n.language]);
};