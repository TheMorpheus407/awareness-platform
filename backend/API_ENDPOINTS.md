# API Endpoints Summary

## Base URL
- Development: `http://localhost:8000/api/v1`
- Production: `https://api.cybersec-platform.de/api/v1`

## Authentication
All endpoints except auth endpoints require Bearer token authentication.

## Endpoints by Category

### 🔐 Authentication (`/auth`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/login` | User login | No |
| POST | `/auth/register` | Register company & admin | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout user | Yes |
| POST | `/auth/verify-email/{token}` | Verify email | No |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password | No |
| GET | `/auth/2fa/qr` | Get 2FA QR code | Yes |
| POST | `/auth/2fa/enable` | Enable 2FA | Yes |
| POST | `/auth/2fa/verify` | Verify 2FA token | Yes |
| POST | `/auth/2fa/disable` | Disable 2FA | Yes |

### 👥 Users (`/users`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/users` | List company users | Yes (Admin) |
| POST | `/users` | Create user | Yes (Admin) |
| POST | `/users/bulk` | Bulk create from CSV | Yes (Admin) |
| GET | `/users/me` | Get current user | Yes |
| PATCH | `/users/me` | Update profile | Yes |
| GET | `/users/{id}` | Get user by ID | Yes (Admin) |
| PATCH | `/users/{id}` | Update user | Yes (Admin) |
| DELETE | `/users/{id}` | Deactivate user | Yes (Admin) |

### 📚 Courses (`/courses`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/courses` | List available courses | Yes |
| GET | `/courses/assigned` | Get assigned courses | Yes |
| GET | `/courses/{id}` | Get course details | Yes |
| POST | `/courses/{id}/start` | Start course | Yes |
| POST | `/courses/{id}/progress` | Update progress | Yes |
| POST | `/courses/{id}/quiz` | Submit quiz | Yes |
| GET | `/courses/{id}/certificate` | Get certificate | Yes |

### 🎣 Phishing (`/phishing`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/phishing/templates` | List templates | Yes (Admin) |
| GET | `/phishing/campaigns` | List campaigns | Yes (Admin) |
| POST | `/phishing/campaigns` | Create campaign | Yes (Admin) |
| GET | `/phishing/campaigns/{id}` | Get campaign | Yes (Admin) |
| POST | `/phishing/campaigns/{id}/launch` | Launch campaign | Yes (Admin) |
| GET | `/phishing/campaigns/{id}/results` | Get results | Yes (Admin) |
| GET | `/phishing/track/{id}` | Track click | No |
| POST | `/phishing/report/{id}` | Report phishing | No |

### 📊 Reports (`/reports`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/reports/compliance/{type}` | Get compliance report | Yes (Admin) |
| GET | `/reports/dashboard/executive` | Executive dashboard | Yes (Admin) |
| GET | `/reports/analytics/risk-trends` | Risk trends | Yes (Admin) |
| GET | `/reports/analytics/overview` | Analytics overview | Yes |

### 💳 Payments (`/payments`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/payments/checkout` | Create checkout session | Yes (Admin) |
| GET | `/payments/history` | Payment history | Yes (Admin) |
| POST | `/payments/webhook` | Stripe webhook | No |
| GET | `/payments/subscription` | Get subscription | Yes (Admin) |
| POST | `/payments/subscription/cancel` | Cancel subscription | Yes (Admin) |

### 🏢 Admin (`/admin`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/admin/companies` | List all companies | Yes (SuperAdmin) |
| GET | `/admin/settings` | Get company settings | Yes (Admin) |
| PATCH | `/admin/settings` | Update settings | Yes (Admin) |

### 🏥 Health (`/health`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Basic health check | No |
| GET | `/health/db` | Database health | No |
| GET | `/health/ready` | Readiness probe | No |
| GET | `/health/live` | Liveness probe | No |

### 📧 Email Campaigns (`/email-campaigns`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/email-campaigns` | List campaigns | Yes (Admin) |
| POST | `/email-campaigns` | Create campaign | Yes (Admin) |
| GET | `/email-campaigns/{id}` | Get campaign | Yes (Admin) |
| POST | `/email-campaigns/{id}/send` | Send campaign | Yes (Admin) |
| GET | `/email-campaigns/{id}/stats` | Get statistics | Yes (Admin) |

### 📋 Enrollments (`/enrollments`)
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/enrollments` | List enrollments | Yes |
| POST | `/enrollments` | Create enrollment | Yes (Admin) |
| DELETE | `/enrollments/{id}` | Cancel enrollment | Yes (Admin) |
| POST | `/enrollments/bulk` | Bulk enroll | Yes (Admin) |

## Common Parameters

### Pagination
- `page`: Page number (default: 0)
- `size`: Items per page (default: 20, max: 100)

### Filtering
- `search`: Search term
- `status`: Filter by status
- `date_from`: Start date
- `date_to`: End date

### Sorting
- `sort_by`: Field to sort by
- `sort_order`: asc/desc

## Response Formats

### Success Response
```json
{
  "data": {},
  "message": "Success",
  "status": "success"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "field": "field_name" // Optional
}
```

### Paginated Response
```json
{
  "items": [],
  "total": 100,
  "page": 0,
  "size": 20,
  "pages": 5
}
```

## Rate Limits
- General: 100 requests/minute
- Auth endpoints: 5 requests/minute
- Report generation: 10 requests/hour

## Status Codes
- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `429`: Rate Limited
- `500`: Internal Server Error