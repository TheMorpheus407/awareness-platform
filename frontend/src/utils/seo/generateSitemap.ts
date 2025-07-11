import { SitemapStream, streamToPromise } from 'sitemap';
import { Readable } from 'stream';

interface SitemapRoute {
  url: string;
  changefreq?: 'always' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'never';
  priority?: number;
  lastmod?: Date | string;
}

const routes: SitemapRoute[] = [
  // Public pages
  { url: '/', changefreq: 'weekly', priority: 1.0 },
  { url: '/pricing', changefreq: 'weekly', priority: 0.9 },
  { url: '/demo', changefreq: 'monthly', priority: 0.8 },
  { url: '/about', changefreq: 'monthly', priority: 0.7 },
  { url: '/contact', changefreq: 'monthly', priority: 0.7 },
  { url: '/blog', changefreq: 'daily', priority: 0.8 },
  { url: '/careers', changefreq: 'weekly', priority: 0.6 },
  { url: '/partners', changefreq: 'monthly', priority: 0.6 },
  { url: '/case-studies', changefreq: 'weekly', priority: 0.7 },
  
  // Legal pages
  { url: '/privacy', changefreq: 'monthly', priority: 0.5 },
  { url: '/terms', changefreq: 'monthly', priority: 0.5 },
  { url: '/impressum', changefreq: 'yearly', priority: 0.3 },
  
  // Auth pages (lower priority)
  { url: '/login', changefreq: 'yearly', priority: 0.3 },
  { url: '/register', changefreq: 'monthly', priority: 0.4 },
];

export const generateSitemap = async (hostname: string = 'https://awareness.bootstrapacademy.com'): Promise<string> => {
  const stream = new SitemapStream({ hostname });
  
  const sitemapData = await streamToPromise(
    Readable.from(routes).pipe(stream)
  );
  
  return sitemapData.toString();
};

// Function to generate sitemap dynamically with blog posts, case studies, etc.
export const generateDynamicSitemap = async (
  hostname: string,
  additionalRoutes: SitemapRoute[] = []
): Promise<string> => {
  const allRoutes = [...routes, ...additionalRoutes];
  const stream = new SitemapStream({ hostname });
  
  const sitemapData = await streamToPromise(
    Readable.from(allRoutes).pipe(stream)
  );
  
  return sitemapData.toString();
};

// Generate sitemap index for large sites
export const generateSitemapIndex = (hostname: string, sitemaps: string[]): string => {
  const sitemapIndex = `<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${sitemaps.map(sitemap => `  <sitemap>
    <loc>${hostname}/${sitemap}</loc>
    <lastmod>${new Date().toISOString()}</lastmod>
  </sitemap>`).join('\n')}
</sitemapindex>`;
  
  return sitemapIndex;
};