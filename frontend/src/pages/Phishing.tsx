/**
 * Phishing simulation page
 */

import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import PhishingDashboard from '../components/Phishing/PhishingDashboard';
import CampaignList from '../components/Phishing/CampaignList';
import CampaignForm from '../components/Phishing/CampaignForm';
import TemplateLibrary from '../components/Phishing/TemplateLibrary';

const Phishing: React.FC = () => {
  return (
    <Routes>
      <Route index element={<PhishingDashboard />} />
      <Route path="campaigns" element={<CampaignList />} />
      <Route path="campaigns/new" element={<CampaignForm />} />
      <Route path="templates" element={<TemplateLibrary />} />
      <Route path="*" element={<Navigate to="/phishing" replace />} />
    </Routes>
  );
};

export default Phishing;