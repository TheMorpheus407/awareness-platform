// Mock implementation for lucide-react icons
import React from 'react';

// Create a mock component factory
const createMockIcon = (displayName: string) => {
  const MockIcon = React.forwardRef<SVGSVGElement, React.SVGProps<SVGSVGElement>>(
    (props, ref) => (
      <svg
        ref={ref}
        data-testid={`lucide-${displayName.toLowerCase()}`}
        {...props}
      >
        <title>{displayName}</title>
      </svg>
    )
  );
  MockIcon.displayName = displayName;
  return MockIcon;
};

// Export all commonly used icons
export const Menu = createMockIcon('Menu');
export const X = createMockIcon('X');
export const Home = createMockIcon('Home');
export const Users = createMockIcon('Users');
export const Building = createMockIcon('Building');
export const LogOut = createMockIcon('LogOut');
export const User = createMockIcon('User');
export const Lock = createMockIcon('Lock');
export const Mail = createMockIcon('Mail');
export const Shield = createMockIcon('Shield');
export const AlertCircle = createMockIcon('AlertCircle');
export const CheckCircle = createMockIcon('CheckCircle');
export const Loader = createMockIcon('Loader');
export const Eye = createMockIcon('Eye');
export const EyeOff = createMockIcon('EyeOff');
export const ChevronDown = createMockIcon('ChevronDown');
export const ChevronUp = createMockIcon('ChevronUp');
export const ChevronLeft = createMockIcon('ChevronLeft');
export const ChevronRight = createMockIcon('ChevronRight');
export const Search = createMockIcon('Search');
export const Plus = createMockIcon('Plus');
export const Trash = createMockIcon('Trash');
export const Edit = createMockIcon('Edit');
export const Save = createMockIcon('Save');
export const Download = createMockIcon('Download');
export const Upload = createMockIcon('Upload');
export const Settings = createMockIcon('Settings');
export const Bell = createMockIcon('Bell');
export const Calendar = createMockIcon('Calendar');
export const Clock = createMockIcon('Clock');
export const Globe = createMockIcon('Globe');
export const Phone = createMockIcon('Phone');
export const Smartphone = createMockIcon('Smartphone');
export const Key = createMockIcon('Key');
export const RefreshCw = createMockIcon('RefreshCw');
export const Copy = createMockIcon('Copy');

// Default export for dynamic imports
export default {
  Menu,
  X,
  Home,
  Users,
  Building,
  LogOut,
  User,
  Lock,
  Mail,
  Shield,
  AlertCircle,
  CheckCircle,
  Loader,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  Search,
  Plus,
  Trash,
  Edit,
  Save,
  Download,
  Upload,
  Settings,
  Bell,
  Calendar,
  Clock,
  Globe,
  Phone,
  Smartphone,
  Key,
  RefreshCw,
  Copy,
};