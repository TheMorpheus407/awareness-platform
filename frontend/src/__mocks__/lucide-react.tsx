import React from 'react';

const createMockIcon = (name: string) => {
  const MockIcon = React.forwardRef<SVGSVGElement, React.SVGProps<SVGSVGElement>>(
    (props, ref) => (
      <svg
        ref={ref}
        data-testid={`${name.toLowerCase()}-icon`}
        {...props}
      >
        <title>{name}</title>
      </svg>
    )
  );
  MockIcon.displayName = name;
  return MockIcon;
};

// Export all the icons used in the app
export const Search = createMockIcon('Search');
export const Plus = createMockIcon('Plus');
export const Edit = createMockIcon('Edit');
export const Trash2 = createMockIcon('Trash2');
export const Users = createMockIcon('Users');
export const Globe = createMockIcon('Globe');
export const UserCheck = createMockIcon('UserCheck');
export const Building2 = createMockIcon('Building2');
export const GraduationCap = createMockIcon('GraduationCap');
export const Mail = createMockIcon('Mail');
export const Shield = createMockIcon('Shield');
export const AlertCircle = createMockIcon('AlertCircle');
export const ChevronLeft = createMockIcon('ChevronLeft');
export const ChevronRight = createMockIcon('ChevronRight');
export const X = createMockIcon('X');
export const Check = createMockIcon('Check');
export const Eye = createMockIcon('Eye');
export const EyeOff = createMockIcon('EyeOff');
export const Lock = createMockIcon('Lock');
export const User = createMockIcon('User');
export const LogOut = createMockIcon('LogOut');
export const Menu = createMockIcon('Menu');
export const Home = createMockIcon('Home');
export const BarChart = createMockIcon('BarChart');
export const Settings = createMockIcon('Settings');
export const FileText = createMockIcon('FileText');
export const Download = createMockIcon('Download');
export const Upload = createMockIcon('Upload');
export const RefreshCw = createMockIcon('RefreshCw');
export const Info = createMockIcon('Info');
export const AlertTriangle = createMockIcon('AlertTriangle');
export const CheckCircle = createMockIcon('CheckCircle');
export const XCircle = createMockIcon('XCircle');
export const Loader2 = createMockIcon('Loader2');
export const Calendar = createMockIcon('Calendar');
export const Clock = createMockIcon('Clock');
export const MapPin = createMockIcon('MapPin');
export const Phone = createMockIcon('Phone');
export const Briefcase = createMockIcon('Briefcase');