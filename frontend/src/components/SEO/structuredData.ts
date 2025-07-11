export interface BreadcrumbItem {
  name: string;
  url: string;
}

export interface FAQItem {
  question: string;
  answer: string;
}

export interface CourseData {
  name: string;
  description: string;
  provider: string;
  url: string;
  duration?: string;
  price?: number;
  currency?: string;
}

export const generateStructuredData = {
  organization: () => ({
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Bootstrap Academy GmbH',
    url: 'https://bootstrapacademy.com',
    logo: 'https://awareness.bootstrapacademy.com/logo.svg',
    contactPoint: {
      '@type': 'ContactPoint',
      telephone: '+49-123-456789',
      contactType: 'customer service',
      areaServed: 'DE',
      availableLanguage: ['German', 'English'],
    },
    sameAs: [
      'https://www.linkedin.com/company/bootstrap-academy',
      'https://twitter.com/bootstrapacademy',
    ],
  }),

  breadcrumb: (items: BreadcrumbItem[]) => ({
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  }),

  course: (courseData: CourseData) => ({
    '@context': 'https://schema.org',
    '@type': 'Course',
    name: courseData.name,
    description: courseData.description,
    provider: {
      '@type': 'Organization',
      name: courseData.provider,
    },
    url: courseData.url,
    hasCourseInstance: {
      '@type': 'CourseInstance',
      courseMode: 'online',
      duration: courseData.duration || 'PT1H',
    },
    offers: courseData.price ? {
      '@type': 'Offer',
      price: courseData.price,
      priceCurrency: courseData.currency || 'EUR',
      availability: 'https://schema.org/InStock',
    } : undefined,
  }),

  faqPage: (faqs: FAQItem[]) => ({
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faqs.map(faq => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  }),

  service: () => ({
    '@context': 'https://schema.org',
    '@type': 'Service',
    serviceType: 'Cybersecurity Training',
    provider: {
      '@type': 'Organization',
      name: 'Bootstrap Academy GmbH',
    },
    areaServed: {
      '@type': 'Country',
      name: 'Germany',
    },
    hasOfferCatalog: {
      '@type': 'OfferCatalog',
      name: 'Cybersecurity Training Services',
      itemListElement: [
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Phishing Simulation',
            description: 'Realistic phishing attack simulations to test and train employees',
          },
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Security Awareness Training',
            description: 'Comprehensive security awareness courses for all employees',
          },
        },
        {
          '@type': 'Offer',
          itemOffered: {
            '@type': 'Service',
            name: 'Compliance Training',
            description: 'GDPR, ISO 27001, and industry-specific compliance training',
          },
        },
      ],
    },
  }),

  webPage: (pageName: string, description: string) => ({
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: pageName,
    description: description,
    url: typeof window !== 'undefined' ? window.location.href : '',
    isPartOf: {
      '@type': 'WebSite',
      name: 'Cybersecurity Awareness Platform',
      url: 'https://awareness.bootstrapacademy.com',
    },
  }),
};