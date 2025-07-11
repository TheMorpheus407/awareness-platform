import { Plugin } from 'vite';
import { generateSitemap } from './src/utils/seo/generateSitemap';
import fs from 'fs/promises';
import path from 'path';

export function sitemapPlugin(): Plugin {
  return {
    name: 'vite-plugin-sitemap',
    apply: 'build',
    async closeBundle() {
      try {
        const sitemap = await generateSitemap();
        const distPath = path.resolve(__dirname, 'dist');
        const sitemapPath = path.join(distPath, 'sitemap.xml');
        
        await fs.writeFile(sitemapPath, sitemap, 'utf-8');
        console.log('Sitemap generated successfully at:', sitemapPath);
      } catch (error) {
        console.error('Error generating sitemap:', error);
      }
    }
  };
}