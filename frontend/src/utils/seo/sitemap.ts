export interface SitemapEntry {
  url: string;
  lastModified?: Date;
  changeFrequency?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority?: number;
}

export const generateSitemapXml = (entries: SitemapEntry[]): string => {
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries.map(entry => `  <url>
    <loc>${entry.url}</loc>
    ${entry.lastModified ? `<lastmod>${entry.lastModified.toISOString()}</lastmod>` : ''}
    ${entry.changeFrequency ? `<changefreq>${entry.changeFrequency}</changefreq>` : ''}
    ${entry.priority !== undefined ? `<priority>${entry.priority}</priority>` : ''}
  </url>`).join('\n')}
</urlset>`;
  
  return xml;
};

export const sitemapRoutes: SitemapEntry[] = [
  {
    url: 'https://awareness.bootstrapacademy.com/',
    changeFrequency: 'weekly',
    priority: 1.0,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/pricing',
    changeFrequency: 'weekly',
    priority: 0.9,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/demo',
    changeFrequency: 'monthly',
    priority: 0.8,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/about',
    changeFrequency: 'monthly',
    priority: 0.7,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/contact',
    changeFrequency: 'monthly',
    priority: 0.7,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/blog',
    changeFrequency: 'daily',
    priority: 0.8,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/courses',
    changeFrequency: 'weekly',
    priority: 0.9,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/careers',
    changeFrequency: 'weekly',
    priority: 0.6,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/partners',
    changeFrequency: 'monthly',
    priority: 0.6,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/case-studies',
    changeFrequency: 'weekly',
    priority: 0.7,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/privacy',
    changeFrequency: 'monthly',
    priority: 0.5,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/terms',
    changeFrequency: 'monthly',
    priority: 0.5,
  },
  {
    url: 'https://awareness.bootstrapacademy.com/impressum',
    changeFrequency: 'yearly',
    priority: 0.3,
  },
];