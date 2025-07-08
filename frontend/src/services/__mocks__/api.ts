import { vi } from 'vitest';

const apiClient = {
  login: vi.fn(),
  register: vi.fn(),
  getCurrentUser: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  
  // User endpoints
  getUsers: vi.fn(),
  getUser: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  updateProfile: vi.fn(),
  changePassword: vi.fn(),
  
  // Company endpoints
  getCompanies: vi.fn(),
  getCompany: vi.fn(),
  createCompany: vi.fn(),
  updateCompany: vi.fn(),
  deleteCompany: vi.fn(),
  
  // Course endpoints
  getCourses: vi.fn(),
  getCourse: vi.fn(),
  createCourse: vi.fn(),
  updateCourse: vi.fn(),
  deleteCourse: vi.fn(),
  
  // Module endpoints
  getModules: vi.fn(),
  getModule: vi.fn(),
  createModule: vi.fn(),
  updateModule: vi.fn(),
  deleteModule: vi.fn(),
  
  // Progress endpoints
  getProgress: vi.fn(),
  updateProgress: vi.fn(),
  
  // Certificate endpoints
  getCertificates: vi.fn(),
  getCertificate: vi.fn(),
  generateCertificate: vi.fn(),
};

export default apiClient;