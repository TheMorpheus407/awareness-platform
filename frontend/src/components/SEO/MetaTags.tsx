import React from 'react';
import { Helmet } from 'react-helmet-async';

interface MetaTagsProps {
  title?: string;
  description?: string;
  keywords?: string;
  ogTitle?: string;
  ogDescription?: string;
  ogImage?: string;
  ogUrl?: string;
  twitterCard?: 'summary' | 'summary_large_image' | 'app' | 'player';
  twitterSite?: string;
  twitterCreator?: string;
  canonicalUrl?: string;
  jsonLd?: object;
  noindex?: boolean;
  nofollow?: boolean;
}

export const MetaTags: React.FC<MetaTagsProps> = ({
  title = 'Cybersecurity Awareness Training Platform',
  description = 'Comprehensive cybersecurity awareness training platform. Protect your organization through interactive phishing simulations, compliance training, and security education.',
  keywords = 'cybersecurity training, phishing simulation, security awareness, compliance training, cyber security education, employee training, data protection, GDPR compliance, security best practices',
  ogTitle,
  ogDescription,
  ogImage = '/og-image.png',
  ogUrl,
  twitterCard = 'summary_large_image',
  twitterSite = '@bootstrapacademy',
  twitterCreator = '@bootstrapacademy',
  canonicalUrl,
  jsonLd,
  noindex = false,
  nofollow = false,
}) => {
  const fullTitle = title.includes('Cybersecurity') ? title : `${title} | Cybersecurity Awareness Platform`;
  const siteUrl = 'https://awareness.bootstrapacademy.com';
  const fullOgUrl = ogUrl || (typeof window !== 'undefined' ? window.location.href : siteUrl);
  
  // Default JSON-LD structured data
  const defaultJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Cybersecurity Awareness Platform',
    applicationCategory: 'SecurityApplication',
    operatingSystem: 'Web',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'EUR',
    },
    aggregateRating: {
      '@type': 'AggregateRating',
      ratingValue: '4.8',
      ratingCount: '1250',
    },
    author: {
      '@type': 'Organization',
      name: 'Bootstrap Academy GmbH',
      url: 'https://bootstrapacademy.com',
    },
  };

  const structuredData = jsonLd || defaultJsonLd;

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content="Bootstrap Academy GmbH" />
      
      {/* Robots Meta Tags */}
      {(noindex || nofollow) && (
        <meta 
          name="robots" 
          content={`${noindex ? 'noindex' : 'index'},${nofollow ? 'nofollow' : 'follow'}`} 
        />
      )}
      
      {/* Canonical URL */}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      
      {/* Open Graph Meta Tags */}
      <meta property="og:type" content="website" />
      <meta property="og:title" content={ogTitle || fullTitle} />
      <meta property="og:description" content={ogDescription || description} />
      <meta property="og:image" content={`${siteUrl}${ogImage}`} />
      <meta property="og:image:width" content="1200" />
      <meta property="og:image:height" content="630" />
      <meta property="og:url" content={fullOgUrl} />
      <meta property="og:site_name" content="Cybersecurity Awareness Platform" />
      <meta property="og:locale" content="en_US" />
      
      {/* Twitter Card Meta Tags */}
      <meta name="twitter:card" content={twitterCard} />
      <meta name="twitter:site" content={twitterSite} />
      <meta name="twitter:creator" content={twitterCreator} />
      <meta name="twitter:title" content={ogTitle || fullTitle} />
      <meta name="twitter:description" content={ogDescription || description} />
      <meta name="twitter:image" content={`${siteUrl}${ogImage}`} />
      
      {/* Additional Meta Tags */}
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta httpEquiv="X-UA-Compatible" content="IE=edge" />
      <meta name="theme-color" content="#0EA5E9" />
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

export default MetaTags;