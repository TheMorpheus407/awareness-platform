#!/bin/bash

# Fix type imports
sed -i 's/import { User, AuthResponse }/import type { User, AuthResponse }/' src/store/authStore.ts
sed -i 's/import axios, { AxiosInstance/import axios from '\''axios'\'';\nimport type { AxiosInstance/' src/services/api.ts
sed -i 's/import { LucideIcon }/import type { LucideIcon }/' src/components/Dashboard/StatsCard.tsx
sed -i 's/import { LoginCredentials }/import type { LoginCredentials }/' src/components/Auth/LoginForm.tsx
sed -i 's/import { RegisterCredentials }/import type { RegisterCredentials }/' src/components/Auth/RegisterForm.tsx
sed -i 's/import { Company, PaginatedResponse }/import type { Company, PaginatedResponse }/' src/pages/Companies.tsx
sed -i 's/import { User, PaginatedResponse }/import type { User, PaginatedResponse }/' src/pages/Users.tsx
sed -i 's/import { DashboardStats }/import type { DashboardStats }/' src/pages/Dashboard.tsx

# Remove unused imports
sed -i '/^import React/d' src/App.tsx

# Fix missing imports in api.ts
sed -i '2i import type { ApiError } from '\''../types'\'';' src/services/api.ts

# Remove unused variables
sed -i 's/, get//' src/store/authStore.ts
sed -i 's/const { user } = useAuthStore();/\/\/ const { user } = useAuthStore();/' src/components/Layout/Navbar.tsx

echo "Type fixes applied!"