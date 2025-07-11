import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';

interface SEOProps {
  title: string;
  description?: string;
  keywords?: string[];
  canonicalUrl?: string;
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogType?: string;
  twitterCard?: string;
  jsonLd?: object;
  noindex?: boolean;
  lang?: string;
}

export const SEO: React.FC<SEOProps> = ({
  title,
  description,
  keywords,
  canonicalUrl,
  ogTitle,
  ogDescription,
  ogImage,
  ogType = 'website',
  twitterCard = 'summary_large_image',
  jsonLd,
  noindex = false,
  lang,
}) => {
  const { i18n } = useTranslation();
  const currentLang = lang || i18n.language;
  
  const siteUrl = import.meta.env.VITE_SITE_URL || 'https://awareness.bootstrapacademy.com';
  const defaultDescription = 'Comprehensive cybersecurity awareness training platform - Protect your organization through education, phishing simulations, and interactive courses.';
  const defaultKeywords = ['cybersecurity', 'awareness training', 'phishing simulation', 'security education', 'compliance training', 'cyber security', 'GDPR', 'ISO 27001'];
  const defaultImage = `${siteUrl}/og-image.png`;

  const actualDescription = description || defaultDescription;
  const actualKeywords = keywords || defaultKeywords;
  const actualOgTitle = ogTitle || title;
  const actualOgDescription = ogDescription || actualDescription;
  const actualOgImage = ogImage || defaultImage;
  const actualCanonicalUrl = canonicalUrl || `${siteUrl}${window.location.pathname}`;

  // Default structured data for Organization
  const defaultJsonLd = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Bootstrap Academy GmbH",
    "url": siteUrl,
    "logo": `${siteUrl}/logo.svg`,
    "sameAs": [
      "https://www.linkedin.com/company/bootstrap-academy",
      "https://twitter.com/bootstrapacad"
    ],
    "contactPoint": {
      "@type": "ContactPoint",
      "telephone": "+49-123-456789",
      "contactType": "customer support",
      "availableLanguage": ["en", "de"]
    }
  };

  const structuredData = jsonLd || defaultJsonLd;

  return (
    <Helmet>
      {/* Primary Meta Tags */}
      <html lang={currentLang} />
      <title>{title} | Cybersecurity Awareness Platform</title>
      <meta name="title" content={`${title} | Cybersecurity Awareness Platform`} />
      <meta name="description" content={actualDescription} />
      <meta name="keywords" content={actualKeywords.join(', ')} />
      <meta name="author" content="Bootstrap Academy GmbH" />
      <link rel="canonical" href={actualCanonicalUrl} />
      
      {/* Control indexing */}
      {noindex && <meta name="robots" content="noindex, nofollow" />}
      {!noindex && <meta name="robots" content="index, follow" />}
      
      {/* Open Graph / Facebook */}
      <meta property="og:type" content={ogType} />
      <meta property="og:url" content={actualCanonicalUrl} />
      <meta property="og:title" content={actualOgTitle} />
      <meta property="og:description" content={actualOgDescription} />
      <meta property="og:image" content={actualOgImage} />
      <meta property="og:site_name" content="Cybersecurity Awareness Platform" />
      <meta property="og:locale" content={currentLang === 'de' ? 'de_DE' : 'en_US'} />
      
      {/* Twitter */}
      <meta property="twitter:card" content={twitterCard} />
      <meta property="twitter:url" content={actualCanonicalUrl} />
      <meta property="twitter:title" content={actualOgTitle} />
      <meta property="twitter:description" content={actualOgDescription} />
      <meta property="twitter:image" content={actualOgImage} />
      <meta property="twitter:site" content="@bootstrapacad" />
      
      {/* Additional Meta Tags */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta name="theme-color" content="#1e40af" />
      <meta name="apple-mobile-web-app-capable" content="yes" />
      <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      <meta name="format-detection" content="telephone=no" />
      
      {/* Structured Data */}
      <script type="application/ld+json">
        {JSON.stringify(structuredData)}
      </script>
    </Helmet>
  );
};