export interface PageMeta {
  title: string;
  description: string;
  keywords?: string;
  ogImage?: string;
  noindex?: boolean;
  canonicalPath?: string;
}

export const pageMeta: Record<string, PageMeta> = {
  home: {
    title: 'Cybersecurity Awareness Training Platform',
    description: 'Transform your organization\'s security culture with engaging cybersecurity awareness training, phishing simulations, and compliance education.',
    keywords: 'cybersecurity training, security awareness, phishing simulation, employee training, data protection',
  },
  pricing: {
    title: 'Pricing Plans - Cybersecurity Training',
    description: 'Flexible pricing plans for cybersecurity awareness training. From small teams to enterprise organizations. Start with a free trial.',
    keywords: 'cybersecurity training pricing, security awareness cost, training plans, enterprise security training',
  },
  demo: {
    title: 'Request a Demo - See Our Platform in Action',
    description: 'Schedule a personalized demo of our cybersecurity awareness training platform. See how we can help protect your organization.',
    keywords: 'cybersecurity demo, training platform demo, security awareness demonstration',
  },
  about: {
    title: 'About Us - Leaders in Cybersecurity Education',
    description: 'Learn about Bootstrap Academy\'s mission to make cybersecurity education accessible and effective for organizations worldwide.',
    keywords: 'about bootstrap academy, cybersecurity education company, security training experts',
  },
  contact: {
    title: 'Contact Us - Get in Touch',
    description: 'Contact our cybersecurity training experts. We\'re here to help you build a stronger security culture.',
    keywords: 'contact cybersecurity experts, security training support, get in touch',
  },
  blog: {
    title: 'Cybersecurity Blog - Latest Insights & Best Practices',
    description: 'Stay updated with the latest cybersecurity trends, best practices, and insights from our security experts.',
    keywords: 'cybersecurity blog, security best practices, cyber threats, security insights',
  },
  login: {
    title: 'Login - Cybersecurity Training Platform',
    description: 'Access your cybersecurity training dashboard. Continue your security awareness journey.',
    noindex: true,
  },
  register: {
    title: 'Sign Up - Start Your Security Training',
    description: 'Create your account and start protecting your organization with our cybersecurity awareness training.',
    keywords: 'sign up cybersecurity training, create account, start security training',
  },
  courses: {
    title: 'Security Training Courses - Comprehensive Curriculum',
    description: 'Explore our comprehensive cybersecurity training courses. From basic awareness to advanced threat detection.',
    keywords: 'security training courses, cybersecurity curriculum, online security education',
  },
  dashboard: {
    title: 'Dashboard - Your Training Progress',
    description: 'Track your cybersecurity training progress and manage your security awareness program.',
    noindex: true,
  },
};

export const getPageMeta = (page: string): PageMeta => {
  return pageMeta[page] || pageMeta.home;
};

export const generateMetaTitle = (pageTitle?: string, siteName = 'Cybersecurity Awareness Platform'): string => {
  if (!pageTitle) return siteName;
  if (pageTitle.includes(siteName)) return pageTitle;
  return `${pageTitle} | ${siteName}`;
};

export const generateCanonicalUrl = (path: string): string => {
  const baseUrl = 'https://awareness.bootstrapacademy.com';
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};