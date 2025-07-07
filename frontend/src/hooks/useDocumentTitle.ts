import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

export const useDocumentTitle = (titleKey?: string) => {
  const { t } = useTranslation();

  useEffect(() => {
    const baseTitle = t('branding.title');
    const pageTitle = titleKey ? t(titleKey) : '';
    
    document.title = pageTitle ? `${pageTitle} - ${baseTitle}` : baseTitle;
  }, [t, titleKey]);
};