import React from 'react';
import { LoginForm } from '../components/Auth';
import { SEO } from '../components/SEO';
import { getPageMetadata } from '../utils/seo/pageMetadata';

export const Login: React.FC = () => {
  const metadata = getPageMetadata('login');
  
  return (
    <>
      <SEO {...metadata} />
      <LoginForm />
    </>
  );
};