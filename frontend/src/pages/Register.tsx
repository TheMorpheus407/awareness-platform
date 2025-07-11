import React from 'react';
import { RegisterForm } from '../components/Auth';
import { SEO } from '../components/SEO';
import { getPageMetadata } from '../utils/seo/pageMetadata';

export const Register: React.FC = () => {
  const metadata = getPageMetadata('register');
  
  return (
    <>
      <SEO {...metadata} />
      <RegisterForm />
    </>
  );
};