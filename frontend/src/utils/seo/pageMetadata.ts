interface PageMetadata {
  title: string;
  description: string;
  keywords?: string[];
  ogImage?: string;
  noindex?: boolean;
}

export const pageMetadata: Record<string, PageMetadata> = {
  home: {
    title: 'Cybersecurity Awareness Training Platform',
    description: 'Transform your organization\'s security culture with comprehensive awareness training, phishing simulations, and interactive courses. Protect your business from cyber threats.',
    keywords: ['cybersecurity training', 'awareness platform', 'phishing simulation', 'security education', 'employee training'],
  },
  dashboard: {
    title: 'Dashboard - Security Overview',
    description: 'Monitor your organization\'s security awareness progress, track training completion, and analyze phishing simulation results.',
    noindex: true,
  },
  login: {
    title: 'Login - Secure Access',
    description: 'Access your cybersecurity awareness training platform. Secure login with two-factor authentication support.',
    noindex: true,
  },
  register: {
    title: 'Register - Start Your Security Journey',
    description: 'Create your account and start protecting your organization with comprehensive cybersecurity awareness training.',
  },
  pricing: {
    title: 'Pricing Plans - Flexible Solutions',
    description: 'Choose the perfect cybersecurity training plan for your organization. From small teams to enterprise solutions.',
    keywords: ['pricing', 'plans', 'subscription', 'enterprise security', 'team training'],
  },
  about: {
    title: 'About Us - Security Experts',
    description: 'Learn about Bootstrap Academy\'s mission to create a safer digital world through comprehensive cybersecurity education.',
    keywords: ['about', 'company', 'mission', 'cybersecurity experts', 'team'],
  },
  contact: {
    title: 'Contact Us - Get in Touch',
    description: 'Contact our cybersecurity experts for questions about awareness training, enterprise solutions, or partnership opportunities.',
    keywords: ['contact', 'support', 'help', 'customer service'],
  },
  blog: {
    title: 'Blog - Cybersecurity Insights',
    description: 'Stay updated with the latest cybersecurity trends, best practices, and insights from our security experts.',
    keywords: ['blog', 'cybersecurity news', 'security insights', 'best practices'],
  },
  careers: {
    title: 'Careers - Join Our Team',
    description: 'Join Bootstrap Academy and help organizations worldwide improve their cybersecurity posture through education.',
    keywords: ['careers', 'jobs', 'employment', 'cybersecurity careers'],
  },
  partners: {
    title: 'Partners - Collaboration Network',
    description: 'Partner with Bootstrap Academy to deliver comprehensive cybersecurity awareness solutions to your clients.',
    keywords: ['partners', 'partnership', 'resellers', 'collaboration'],
  },
  caseStudies: {
    title: 'Case Studies - Success Stories',
    description: 'Discover how organizations transformed their security culture with our cybersecurity awareness training platform.',
    keywords: ['case studies', 'success stories', 'testimonials', 'results'],
  },
  demo: {
    title: 'Request Demo - See It In Action',
    description: 'Schedule a personalized demo of our cybersecurity awareness training platform and see how it can protect your organization.',
    keywords: ['demo', 'free trial', 'demonstration', 'preview'],
  },
  phishing: {
    title: 'Phishing Simulations - Test & Train',
    description: 'Run realistic phishing simulations to test and improve your employees\' ability to recognize and report phishing attempts.',
    keywords: ['phishing simulation', 'phishing test', 'email security', 'security testing'],
    noindex: true,
  },
  analytics: {
    title: 'Analytics - Security Metrics',
    description: 'Comprehensive analytics and reporting for your cybersecurity awareness training programs.',
    noindex: true,
  },
  users: {
    title: 'User Management - Team Administration',
    description: 'Manage users, assign training courses, and track individual progress in cybersecurity awareness.',
    noindex: true,
  },
  companies: {
    title: 'Company Management - Multi-Tenant Administration',
    description: 'Manage multiple companies and subsidiaries within your cybersecurity training platform.',
    noindex: true,
  },
  impressum: {
    title: 'Impressum - Legal Information',
    description: 'Legal information and company details for Bootstrap Academy GmbH.',
    noindex: true,
  },
  privacy: {
    title: 'Privacy Policy - Data Protection',
    description: 'Learn how Bootstrap Academy protects your data and ensures GDPR compliance in our cybersecurity training platform.',
    keywords: ['privacy policy', 'data protection', 'GDPR', 'compliance'],
  },
  terms: {
    title: 'Terms of Service - Legal Agreement',
    description: 'Terms and conditions for using Bootstrap Academy\'s cybersecurity awareness training platform.',
    keywords: ['terms of service', 'legal', 'agreement', 'conditions'],
  },
};

export const getPageMetadata = (page: string): PageMetadata => {
  return pageMetadata[page] || {
    title: 'Cybersecurity Awareness Platform',
    description: 'Comprehensive cybersecurity awareness training platform - Protect your organization through education.',
  };
};