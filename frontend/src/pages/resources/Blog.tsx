import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Shield, ArrowLeft, Calendar, Clock, User, ChevronRight, Search } from 'lucide-react';
import { LanguageSwitcher } from '../../components/Common';

const Blog = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const blogPosts = [
    {
      id: 1,
      title: 'Die 10 häufigsten Phishing-Methoden in 2024',
      excerpt: 'Erfahren Sie, welche Phishing-Techniken Cyberkriminelle aktuell am häufigsten einsetzen und wie Sie sich schützen können.',
      author: 'Dr. Max Mustermann',
      date: '2024-01-15',
      readTime: '8 Min.',
      category: 'Phishing',
      image: '/blog/phishing-methods.jpg',
    },
    {
      id: 2,
      title: 'DSGVO-konforme Mitarbeiterschulungen durchführen',
      excerpt: 'Ein Leitfaden für datenschutzkonforme Awareness-Trainings in Ihrem Unternehmen.',
      author: 'Sarah Weber',
      date: '2024-01-10',
      readTime: '6 Min.',
      category: 'Compliance',
      image: '/blog/dsgvo-training.jpg',
    },
    {
      id: 3,
      title: 'ROI von Security Awareness Trainings berechnen',
      excerpt: 'Wie Sie den Return on Investment Ihrer Cybersecurity-Schulungen messen und optimieren.',
      author: 'Thomas Schmidt',
      date: '2024-01-05',
      readTime: '10 Min.',
      category: 'Business',
      image: '/blog/roi-calculation.jpg',
    },
    {
      id: 4,
      title: 'KI-gestützte Cyberangriffe: Die neue Bedrohung',
      excerpt: 'Wie künstliche Intelligenz die Landschaft der Cyberkriminalität verändert.',
      author: 'Erika Musterfrau',
      date: '2023-12-28',
      readTime: '12 Min.',
      category: 'Technologie',
      image: '/blog/ai-threats.jpg',
    },
    {
      id: 5,
      title: 'Best Practices für Remote Work Security',
      excerpt: 'Sicherheitsrichtlinien und -tipps für das Arbeiten im Home Office.',
      author: 'Dr. Max Mustermann',
      date: '2023-12-20',
      readTime: '7 Min.',
      category: 'Best Practices',
      image: '/blog/remote-security.jpg',
    },
    {
      id: 6,
      title: 'Der menschliche Faktor in der Cybersicherheit',
      excerpt: 'Warum Mitarbeiter die erste Verteidigungslinie gegen Cyberangriffe sind.',
      author: 'Sarah Weber',
      date: '2023-12-15',
      readTime: '9 Min.',
      category: 'Awareness',
      image: '/blog/human-factor.jpg',
    },
  ];

  const categories = [
    { value: 'all', label: 'Alle Kategorien' },
    { value: 'phishing', label: 'Phishing' },
    { value: 'compliance', label: 'Compliance' },
    { value: 'business', label: 'Business' },
    { value: 'technologie', label: 'Technologie' },
    { value: 'best-practices', label: 'Best Practices' },
    { value: 'awareness', label: 'Awareness' },
  ];

  const filteredPosts = blogPosts.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         post.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || 
                           post.category.toLowerCase() === selectedCategory.toLowerCase();
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm z-50 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <Link to="/" className="flex items-center space-x-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <span className="text-xl font-bold text-gray-900">Bootstrap Academy</span>
            </Link>
            <div className="flex items-center space-x-6">
              <LanguageSwitcher />
              <Link to="/" className="text-gray-600 hover:text-gray-900 transition-colors">
                {t('common.backToHome')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-blue-50 to-white">
        <div className="max-w-7xl mx-auto">
          <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-8">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {t('common.back')}
          </Link>

          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6">
              {t('blog.title', 'Blog & Insights')}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {t('blog.subtitle', 
                'Aktuelle Artikel, Tipps und Best Practices rund um Cybersecurity und Awareness-Training.'
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Search and Filter Section */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 border-b border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder={t('blog.search', 'Artikel durchsuchen...')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {categories.map(category => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Blog Posts Grid */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          {filteredPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 text-lg">
                {t('blog.noResults', 'Keine Artikel gefunden.')}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredPosts.map(post => (
                <article key={post.id} className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
                  <div className="h-48 bg-gray-300"></div>
                  <div className="p-6">
                    <div className="flex items-center text-sm text-gray-500 mb-3">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs font-medium">
                        {post.category}
                      </span>
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 mb-3">
                      {post.title}
                    </h2>
                    <p className="text-gray-600 mb-4 line-clamp-3">
                      {post.excerpt}
                    </p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-500 space-x-4">
                        <span className="flex items-center">
                          <Calendar className="w-4 h-4 mr-1" />
                          {new Date(post.date).toLocaleDateString('de-DE')}
                        </span>
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {post.readTime}
                        </span>
                      </div>
                      <Link
                        to={`/blog/${post.id}`}
                        className="text-blue-600 hover:text-blue-700 font-medium flex items-center"
                      >
                        {t('blog.readMore', 'Weiterlesen')}
                        <ChevronRight className="w-4 h-4 ml-1" />
                      </Link>
                    </div>
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex items-center text-sm text-gray-500">
                        <User className="w-4 h-4 mr-1" />
                        {post.author}
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Newsletter Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            {t('blog.newsletter.title', 'Bleiben Sie informiert')}
          </h2>
          <p className="text-lg text-blue-100 mb-8">
            {t('blog.newsletter.subtitle', 
              'Abonnieren Sie unseren Newsletter und erhalten Sie die neuesten Insights direkt in Ihr Postfach.'
            )}
          </p>
          <form className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
            <input
              type="email"
              placeholder={t('blog.newsletter.placeholder', 'Ihre E-Mail-Adresse')}
              className="flex-1 px-4 py-3 rounded-lg text-gray-900 placeholder-gray-500 focus:ring-2 focus:ring-white focus:outline-none"
            />
            <button
              type="submit"
              className="px-6 py-3 bg-white text-blue-600 font-medium rounded-lg hover:bg-gray-100 transition-colors"
            >
              {t('blog.newsletter.subscribe', 'Abonnieren')}
            </button>
          </form>
          <p className="text-sm text-blue-100 mt-4">
            {t('blog.newsletter.privacy', 'Wir respektieren Ihre Privatsphäre. Jederzeit abbestellbar.')}
          </p>
        </div>
      </section>

      {/* Popular Topics */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
            {t('blog.topics.title', 'Beliebte Themen')}
          </h2>
          <div className="flex flex-wrap justify-center gap-4">
            {['Phishing-Simulation', 'DSGVO', 'Social Engineering', 'Ransomware', 
              'Zero Trust', 'Cloud Security', 'Mobile Security', 'Incident Response'].map(topic => (
              <Link
                key={topic}
                to={`/blog?topic=${topic.toLowerCase().replace(' ', '-')}`}
                className="px-6 py-2 bg-white rounded-full shadow-md hover:shadow-lg transition-shadow text-gray-700 hover:text-blue-600"
              >
                {topic}
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
};

export default Blog;