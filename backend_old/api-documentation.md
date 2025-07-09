# API Dokumentation - Cybersecurity Awareness Platform
**Version 1.0 | OpenAPI 3.0 Specification**

## 1. OpenAPI Specification

```yaml
openapi: 3.0.3
info:
  title: Cybersecurity Awareness Platform API
  description: |
    Comprehensive API for cybersecurity awareness training platform.
    
    ## Authentication
    The API uses JWT Bearer token authentication. Obtain a token via `/auth/login` endpoint.
    
    ## Rate Limiting
    - General endpoints: 100 requests per minute
    - Auth endpoints: 5 requests per minute
    - Report generation: 10 requests per hour
    
  version: 1.0.0
  contact:
    email: hallo@bootstrap-awareness.de
  license:
    name: Proprietary
    
servers:
  - url: https://bootstrap-awareness.de/api
    description: Production server
  - url: https://staging.bootstrap-awareness.de/api
    description: Staging server
  - url: http://localhost:8000/api
    description: Development server

security:
  - bearerAuth: []

tags:
  - name: Authentication
    description: User authentication and authorization
  - name: Users
    description: User management operations
  - name: Courses
    description: Training courses and progress
  - name: Phishing
    description: Phishing simulation campaigns
  - name: Reports
    description: Compliance and analytics reports
  - name: Admin
    description: Administrative operations

paths:
  # Authentication Endpoints
  /auth/login:
    post:
      tags:
        - Authentication
      summary: User login
      description: Authenticate user and receive access tokens
      security: []
      requestBody:
        required: true
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              required:
                - username
                - password
              properties:
                username:
                  type: string
                  format: email
                  example: user@company.com
                password:
                  type: string
                  format: password
                  example: SecurePassword123!
                grant_type:
                  type: string
                  default: password
      responses:
        '200':
          description: Successful authentication
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
              example:
                access_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                refresh_token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
                token_type: "bearer"
                expires_in: 1800
        '401':
          $ref: '#/components/responses/UnauthorizedError'
        '429':
          $ref: '#/components/responses/RateLimitError'

  /auth/register:
    post:
      tags:
        - Authentication
      summary: Register new company and admin user
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanyRegistration'
      responses:
        '201':
          description: Registration successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegistrationResponse'
        '400':
          $ref: '#/components/responses/BadRequestError'
        '409':
          $ref: '#/components/responses/ConflictError'

  /auth/refresh:
    post:
      tags:
        - Authentication
      summary: Refresh access token
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - refresh_token
              properties:
                refresh_token:
                  type: string
      responses:
        '200':
          description: Token refreshed successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedError'

  /auth/logout:
    post:
      tags:
        - Authentication
      summary: Logout user
      responses:
        '200':
          description: Successfully logged out
        '401':
          $ref: '#/components/responses/UnauthorizedError'

  /auth/verify-email/{token}:
    post:
      tags:
        - Authentication
      summary: Verify email address
      security: []
      parameters:
        - name: token
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Email verified successfully
        '400':
          $ref: '#/components/responses/BadRequestError'

  /auth/forgot-password:
    post:
      tags:
        - Authentication
      summary: Request password reset
      security: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - email
              properties:
                email:
                  type: string
                  format: email
      responses:
        '200':
          description: Password reset email sent
        '404':
          $ref: '#/components/responses/NotFoundError'

  # User Management Endpoints
  /users:
    get:
      tags:
        - Users
      summary: List company users
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/SizeParam'
        - name: search
          in: query
          schema:
            type: string
          description: Search by name or email
        - name: department
          in: query
          schema:
            type: string
        - name: role
          in: query
          schema:
            $ref: '#/components/schemas/UserRole'
        - name: risk_score_min
          in: query
          schema:
            type: number
            minimum: 0
            maximum: 100
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserListResponse'
        '403':
          $ref: '#/components/responses/ForbiddenError'

    post:
      tags:
        - Users
      summary: Create new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserCreate'
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '400':
          $ref: '#/components/responses/BadRequestError'
        '403':
          $ref: '#/components/responses/ForbiddenError'

  /users/bulk:
    post:
      tags:
        - Users
      summary: Bulk create users from CSV
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: CSV file with columns email, first_name, last_name, department, role
                send_invites:
                  type: boolean
                  default: true
      responses:
        '200':
          description: Bulk creation result
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/BulkUserResponse'
        '400':
          $ref: '#/components/responses/BadRequestError'

  /users/me:
    get:
      tags:
        - Users
      summary: Get current user details
      responses:
        '200':
          description: Current user details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetail'

    patch:
      tags:
        - Users
      summary: Update current user profile
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserProfileUpdate'
      responses:
        '200':
          description: Profile updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetail'

  /users/{user_id}:
    get:
      tags:
        - Users
      summary: Get user by ID
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      responses:
        '200':
          description: User details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserDetail'
        '404':
          $ref: '#/components/responses/NotFoundError'

    patch:
      tags:
        - Users
      summary: Update user
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserUpdate'
      responses:
        '200':
          description: User updated successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '403':
          $ref: '#/components/responses/ForbiddenError'
        '404':
          $ref: '#/components/responses/NotFoundError'

    delete:
      tags:
        - Users
      summary: Deactivate user
      parameters:
        - $ref: '#/components/parameters/UserIdParam'
      responses:
        '204':
          description: User deactivated successfully
        '403':
          $ref: '#/components/responses/ForbiddenError'
        '404':
          $ref: '#/components/responses/NotFoundError'

  # Course Endpoints
  /courses:
    get:
      tags:
        - Courses
      summary: List available courses
      parameters:
        - name: tag
          in: query
          schema:
            type: string
        - name: compliance_tag
          in: query
          schema:
            type: string
        - name: difficulty
          in: query
          schema:
            $ref: '#/components/schemas/CourseDifficulty'
        - name: language
          in: query
          schema:
            type: string
            enum: [de, en, fr, it]
      responses:
        '200':
          description: List of available courses
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Course'

  /courses/assigned:
    get:
      tags:
        - Courses
      summary: Get user's assigned courses
      parameters:
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CourseProgressStatus'
      responses:
        '200':
          description: List of assigned courses
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AssignedCourse'

  /courses/{course_id}:
    get:
      tags:
        - Courses
      summary: Get course details
      parameters:
        - $ref: '#/components/parameters/CourseIdParam'
      responses:
        '200':
          description: Course details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CourseDetail'
        '404':
          $ref: '#/components/responses/NotFoundError'

  /courses/{course_id}/start:
    post:
      tags:
        - Courses
      summary: Start course
      parameters:
        - $ref: '#/components/parameters/CourseIdParam'
      responses:
        '200':
          description: Course started successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CourseProgress'
        '400':
          $ref: '#/components/responses/BadRequestError'

  /courses/{course_id}/progress:
    post:
      tags:
        - Courses
      summary: Update course progress
      parameters:
        - $ref: '#/components/parameters/CourseIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProgressUpdate'
      responses:
        '200':
          description: Progress updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CourseProgress'

  /courses/{course_id}/quiz:
    post:
      tags:
        - Courses
      summary: Submit quiz answers
      parameters:
        - $ref: '#/components/parameters/CourseIdParam'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - answers
              properties:
                answers:
                  type: array
                  items:
                    $ref: '#/components/schemas/QuizAnswer'
      responses:
        '200':
          description: Quiz results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuizResult'

  /courses/{course_id}/certificate:
    get:
      tags:
        - Courses
      summary: Download course certificate
      parameters:
        - $ref: '#/components/parameters/CourseIdParam'
      responses:
        '200':
          description: Certificate PDF
          content:
            application/pdf:
              schema:
                type: string
                format: binary
        '404':
          $ref: '#/components/responses/NotFoundError'

  # Phishing Simulation Endpoints
  /phishing/templates:
    get:
      tags:
        - Phishing
      summary: List phishing templates
      parameters:
        - name: difficulty
          in: query
          schema:
            $ref: '#/components/schemas/PhishingDifficulty'
        - name: category
          in: query
          schema:
            $ref: '#/components/schemas/PhishingCategory'
      responses:
        '200':
          description: List of phishing templates
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PhishingTemplate'

  /phishing/campaigns:
    get:
      tags:
        - Phishing
      summary: List phishing campaigns
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/SizeParam'
        - name: status
          in: query
          schema:
            $ref: '#/components/schemas/CampaignStatus'
      responses:
        '200':
          description: List of campaigns
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CampaignListResponse'

    post:
      tags:
        - Phishing
      summary: Create phishing campaign
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CampaignCreate'
      responses:
        '201':
          description: Campaign created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Campaign'

  /phishing/campaigns/{campaign_id}:
    get:
      tags:
        - Phishing
      summary: Get campaign details
      parameters:
        - $ref: '#/components/parameters/CampaignIdParam'
      responses:
        '200':
          description: Campaign details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CampaignDetail'

  /phishing/campaigns/{campaign_id}/launch:
    post:
      tags:
        - Phishing
      summary: Launch campaign
      parameters:
        - $ref: '#/components/parameters/CampaignIdParam'
      responses:
        '200':
          description: Campaign launched
        '400':
          $ref: '#/components/responses/BadRequestError'

  /phishing/campaigns/{campaign_id}/results:
    get:
      tags:
        - Phishing
      summary: Get campaign results
      parameters:
        - $ref: '#/components/parameters/CampaignIdParam'
      responses:
        '200':
          description: Campaign results
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CampaignResults'

  /phishing/track/{tracking_id}:
    get:
      tags:
        - Phishing
      summary: Track phishing link click
      security: []
      parameters:
        - name: tracking_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '302':
          description: Redirect to training page
          headers:
            Location:
              schema:
                type: string

  /phishing/report/{tracking_id}:
    post:
      tags:
        - Phishing
      summary: Report phishing email
      security: []
      parameters:
        - name: tracking_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Report recorded

  # Reporting Endpoints
  /reports/compliance/{report_type}:
    get:
      tags:
        - Reports
      summary: Generate compliance report
      parameters:
        - name: report_type
          in: path
          required: true
          schema:
            type: string
            enum: [nis2, dsgvo, iso27001, tisax, bait]
        - name: start_date
          in: query
          schema:
            type: string
            format: date
        - name: end_date
          in: query
          schema:
            type: string
            format: date
        - name: format
          in: query
          schema:
            type: string
            enum: [json, pdf, csv]
            default: json
      responses:
        '200':
          description: Compliance report
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ComplianceReport'
            application/pdf:
              schema:
                type: string
                format: binary
            text/csv:
              schema:
                type: string

  /reports/dashboard/executive:
    get:
      tags:
        - Reports
      summary: Get executive dashboard data
      responses:
        '200':
          description: Executive dashboard
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ExecutiveDashboard'

  /reports/analytics/risk-trends:
    get:
      tags:
        - Reports
      summary: Get risk trend analysis
      parameters:
        - name: timeframe
          in: query
          schema:
            type: string
            enum: [daily, weekly, monthly]
            default: monthly
        - name: months
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 24
            default: 12
      responses:
        '200':
          description: Risk trends
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RiskTrends'

  # Admin Endpoints
  /admin/companies:
    get:
      tags:
        - Admin
      summary: List all companies (Super Admin only)
      parameters:
        - $ref: '#/components/parameters/PageParam'
        - $ref: '#/components/parameters/SizeParam'
      responses:
        '200':
          description: List of companies
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanyListResponse'
        '403':
          $ref: '#/components/responses/ForbiddenError'

  /admin/settings:
    get:
      tags:
        - Admin
      summary: Get company settings
      responses:
        '200':
          description: Company settings
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanySettings'

    patch:
      tags:
        - Admin
      summary: Update company settings
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompanySettingsUpdate'
      responses:
        '200':
          description: Settings updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompanySettings'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  parameters:
    UserIdParam:
      name: user_id
      in: path
      required: true
      schema:
        type: string
        format: uuid

    CourseIdParam:
      name: course_id
      in: path
      required: true
      schema:
        type: string
        format: uuid

    CampaignIdParam:
      name: campaign_id
      in: path
      required: true
      schema:
        type: string
        format: uuid

    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 0
        default: 0

    SizeParam:
      name: size
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 100
        default: 20

  schemas:
    # Authentication Schemas
    TokenResponse:
      type: object
      required:
        - access_token
        - token_type
      properties:
        access_token:
          type: string
        refresh_token:
          type: string
        token_type:
          type: string
          default: bearer
        expires_in:
          type: integer
          description: Token validity in seconds

    CompanyRegistration:
      type: object
      required:
        - company_name
        - company_domain
        - industry
        - size
        - admin_email
        - admin_password
        - admin_first_name
        - admin_last_name
      properties:
        company_name:
          type: string
          minLength: 2
          maxLength: 255
        company_domain:
          type: string
          pattern: '^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
        industry:
          type: string
        size:
          type: string
          enum: [small, medium, large, enterprise]
        compliance_requirements:
          type: array
          items:
            type: string
            enum: [nis2, dsgvo, iso27001, tisax, bait, kritis]
        admin_email:
          type: string
          format: email
        admin_password:
          type: string
          minLength: 8
          pattern: '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        admin_first_name:
          type: string
        admin_last_name:
          type: string

    RegistrationResponse:
      type: object
      properties:
        company:
          $ref: '#/components/schemas/Company'
        user:
          $ref: '#/components/schemas/User'
        message:
          type: string

    # User Schemas
    UserRole:
      type: string
      enum: [admin, manager, employee]

    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        first_name:
          type: string
        last_name:
          type: string
        role:
          $ref: '#/components/schemas/UserRole'
        department:
          type: string
        is_active:
          type: boolean
        risk_score:
          type: number
          minimum: 0
          maximum: 100
        last_login_at:
          type: string
          format: date-time
        created_at:
          type: string
          format: date-time

    UserDetail:
      allOf:
        - $ref: '#/components/schemas/User'
        - type: object
          properties:
            company:
              $ref: '#/components/schemas/Company'
            training_completion_rate:
              type: number
            phishing_click_rate:
              type: number
            last_training_date:
              type: string
              format: date-time
            courses_completed:
              type: integer
            courses_in_progress:
              type: integer
            courses_assigned:
              type: integer

    UserCreate:
      type: object
      required:
        - email
        - first_name
        - last_name
        - role
      properties:
        email:
          type: string
          format: email
        first_name:
          type: string
        last_name:
          type: string
        role:
          $ref: '#/components/schemas/UserRole'
        department:
          type: string
        send_invite:
          type: boolean
          default: true

    UserUpdate:
      type: object
      properties:
        first_name:
          type: string
        last_name:
          type: string
        role:
          $ref: '#/components/schemas/UserRole'
        department:
          type: string
        is_active:
          type: boolean

    UserProfileUpdate:
      type: object
      properties:
        first_name:
          type: string
        last_name:
          type: string
        department:
          type: string

    UserListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/User'
        total:
          type: integer
        page:
          type: integer
        size:
          type: integer
        pages:
          type: integer

    BulkUserResponse:
      type: object
      properties:
        created:
          type: integer
        failed:
          type: integer
        errors:
          type: array
          items:
            type: object
            properties:
              row:
                type: integer
              email:
                type: string
              error:
                type: string

    # Course Schemas
    CourseDifficulty:
      type: string
      enum: [beginner, intermediate, advanced]

    CourseProgressStatus:
      type: string
      enum: [not_started, in_progress, completed, failed]

    Course:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        description:
          type: string
        duration_minutes:
          type: integer
        difficulty:
          $ref: '#/components/schemas/CourseDifficulty'
        tags:
          type: array
          items:
            type: string
        compliance_tags:
          type: array
          items:
            type: string
        available_languages:
          type: array
          items:
            type: string
        is_mandatory:
          type: boolean

    CourseDetail:
      allOf:
        - $ref: '#/components/schemas/Course'
        - type: object
          properties:
            youtube_video_id:
              type: string
            content_markdown:
              type: string
            quiz_questions:
              type: array
              items:
                $ref: '#/components/schemas/QuizQuestion'
            passing_score:
              type: integer

    AssignedCourse:
      allOf:
        - $ref: '#/components/schemas/Course'
        - type: object
          properties:
            assigned_at:
              type: string
              format: date-time
            due_date:
              type: string
              format: date-time
            status:
              $ref: '#/components/schemas/CourseProgressStatus'
            progress_percentage:
              type: number
            quiz_score:
              type: number

    CourseProgress:
      type: object
      properties:
        course_id:
          type: string
          format: uuid
        user_id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/CourseProgressStatus'
        started_at:
          type: string
          format: date-time
        last_accessed_at:
          type: string
          format: date-time
        video_progress_seconds:
          type: integer
        video_total_seconds:
          type: integer
        video_completion_percentage:
          type: number

    ProgressUpdate:
      type: object
      required:
        - video_progress_seconds
      properties:
        video_progress_seconds:
          type: integer
          minimum: 0

    QuizQuestion:
      type: object
      properties:
        id:
          type: string
        question:
          type: string
        options:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
              text:
                type: string

    QuizAnswer:
      type: object
      required:
        - question_id
        - answer_id
      properties:
        question_id:
          type: string
        answer_id:
          type: string

    QuizResult:
      type: object
      properties:
        score:
          type: number
        passed:
          type: boolean
        passing_score:
          type: number
        correct_answers:
          type: integer
        total_questions:
          type: integer
        feedback:
          type: array
          items:
            type: object
            properties:
              question_id:
                type: string
              correct:
                type: boolean
              explanation:
                type: string

    # Phishing Schemas
    PhishingDifficulty:
      type: string
      enum: [easy, medium, hard, expert]

    PhishingCategory:
      type: string
      enum: [credential, attachment, link, mixed]

    CampaignStatus:
      type: string
      enum: [draft, scheduled, running, completed, cancelled]

    PhishingTemplate:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        description:
          type: string
        category:
          $ref: '#/components/schemas/PhishingCategory'
        difficulty:
          $ref: '#/components/schemas/PhishingDifficulty'
        subject:
          type: string
        sender_name:
          type: string
        preview:
          type: string
        red_flags:
          type: array
          items:
            type: object
            properties:
              type:
                type: string
              description:
                type: string

    Campaign:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        template_id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/CampaignStatus'
        scheduled_at:
          type: string
          format: date-time
        total_recipients:
          type: integer
        created_at:
          type: string
          format: date-time

    CampaignCreate:
      type: object
      required:
        - name
        - template_id
        - target_groups
      properties:
        name:
          type: string
        description:
          type: string
        template_id:
          type: string
          format: uuid
        target_groups:
          type: array
          items:
            type: string
          example: ["all", "department:IT", "role:manager"]
        excluded_users:
          type: array
          items:
            type: string
            format: uuid
        scheduled_at:
          type: string
          format: date-time
        track_duration_days:
          type: integer
          minimum: 1
          maximum: 30
          default: 7

    CampaignDetail:
      allOf:
        - $ref: '#/components/schemas/Campaign'
        - type: object
          properties:
            template:
              $ref: '#/components/schemas/PhishingTemplate'
            started_at:
              type: string
              format: date-time
            completed_at:
              type: string
              format: date-time
            emails_sent:
              type: integer
            emails_opened:
              type: integer
            links_clicked:
              type: integer
            data_submitted:
              type: integer
            reported_suspicious:
              type: integer

    CampaignResults:
      type: object
      properties:
        campaign:
          $ref: '#/components/schemas/CampaignDetail'
        summary:
          type: object
          properties:
            click_rate:
              type: number
            report_rate:
              type: number
            average_time_to_click:
              type: string
            risk_score_impact:
              type: number
        user_results:
          type: array
          items:
            type: object
            properties:
              user_id:
                type: string
                format: uuid
              email:
                type: string
              department:
                type: string
              opened:
                type: boolean
              clicked:
                type: boolean
              data_submitted:
                type: boolean
              reported:
                type: boolean
              time_to_click:
                type: string
              training_completed:
                type: boolean

    CampaignListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Campaign'
        total:
          type: integer
        page:
          type: integer
        size:
          type: integer
        pages:
          type: integer

    # Report Schemas
    ComplianceReport:
      type: object
      properties:
        report_type:
          type: string
        company_id:
          type: string
          format: uuid
        period:
          type: object
          properties:
            start:
              type: string
              format: date
            end:
              type: string
              format: date
        compliance_status:
          type: string
          enum: [compliant, non-compliant, partially-compliant]
        details:
          type: object
          additionalProperties: true
        generated_at:
          type: string
          format: date-time

    ExecutiveDashboard:
      type: object
      properties:
        company_metrics:
          type: object
          properties:
            total_users:
              type: integer
            active_users:
              type: integer
            average_risk_score:
              type: number
            high_risk_users:
              type: integer
        training_metrics:
          type: object
          properties:
            courses_completed_this_month:
              type: integer
            average_completion_rate:
              type: number
            overdue_trainings:
              type: integer
        phishing_metrics:
          type: object
          properties:
            campaigns_this_quarter:
              type: integer
            average_click_rate:
              type: number
            improvement_rate:
              type: number
        compliance_overview:
          type: array
          items:
            type: object
            properties:
              standard:
                type: string
              status:
                type: string
              last_assessment:
                type: string
                format: date

    RiskTrends:
      type: object
      properties:
        timeframe:
          type: string
        data_points:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              average_risk_score:
                type: number
              high_risk_count:
                type: integer
              total_users:
                type: integer
        departments:
          type: array
          items:
            type: object
            properties:
              department:
                type: string
              trend:
                type: string
                enum: [improving, stable, declining]
              current_score:
                type: number

    # Company Schemas
    Company:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        domain:
          type: string
        industry:
          type: string
        size:
          type: string
        compliance_requirements:
          type: array
          items:
            type: string
        subscription_tier:
          type: string
        created_at:
          type: string
          format: date-time

    CompanySettings:
      type: object
      properties:
        phishing_frequency:
          type: string
          enum: [weekly, biweekly, monthly, quarterly]
        reminder_days:
          type: array
          items:
            type: integer
        auto_assign_courses:
          type: boolean
        language:
          type: string
          enum: [de, en, fr, it]
        require_2fa:
          type: boolean
        password_policy:
          type: object
          properties:
            min_length:
              type: integer
            require_uppercase:
              type: boolean
            require_lowercase:
              type: boolean
            require_numbers:
              type: boolean
            require_special:
              type: boolean
            expiry_days:
              type: integer

    CompanySettingsUpdate:
      type: object
      properties:
        phishing_frequency:
          type: string
          enum: [weekly, biweekly, monthly, quarterly]
        reminder_days:
          type: array
          items:
            type: integer
        auto_assign_courses:
          type: boolean
        language:
          type: string
          enum: [de, en, fr, it]

    CompanyListResponse:
      type: object
      properties:
        items:
          type: array
          items:
            $ref: '#/components/schemas/Company'
        total:
          type: integer
        page:
          type: integer
        size:
          type: integer
        pages:
          type: integer

    # Error Schemas
    Error:
      type: object
      required:
        - detail
      properties:
        detail:
          type: string
        code:
          type: string
        field:
          type: string

    ValidationError:
      type: object
      required:
        - detail
      properties:
        detail:
          type: array
          items:
            type: object
            properties:
              loc:
                type: array
                items:
                  type: string
              msg:
                type: string
              type:
                type: string

  responses:
    BadRequestError:
      description: Bad request
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationError'

    UnauthorizedError:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: "Not authenticated"
            code: "UNAUTHORIZED"

    ForbiddenError:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: "Not enough permissions"
            code: "FORBIDDEN"

    NotFoundError:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: "Resource not found"
            code: "NOT_FOUND"

    ConflictError:
      description: Resource conflict
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: "Resource already exists"
            code: "CONFLICT"

    RateLimitError:
      description: Rate limit exceeded
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            detail: "Rate limit exceeded. Try again later."
            code: "RATE_LIMITED"
      headers:
        X-RateLimit-Limit:
          schema:
            type: integer
          description: Request limit per minute
        X-RateLimit-Remaining:
          schema:
            type: integer
          description: Remaining requests
        X-RateLimit-Reset:
          schema:
            type: integer
          description: Reset time (Unix timestamp)
```

## 2. API Client Examples

### 2.1 Python Client Example
```python
import httpx
from typing import Optional, Dict, Any
import asyncio

class CybersecAPIClient:
    def __init__(self, base_url: str = "https://bootstrap-awareness.de"):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(base_url=base_url)
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate and store access token"""
        response = await self.client.post(
            "/api/auth/login",
            data={
                "username": email,
                "password": password,
                "grant_type": "password"
            }
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.client.headers["Authorization"] = f"Bearer {self.token}"
        return data
    
    async def get_courses(self) -> list:
        """Get available courses"""
        response = await self.client.get("/api/courses")
        response.raise_for_status()
        return response.json()
    
    async def start_course(self, course_id: str) -> Dict[str, Any]:
        """Start a course"""
        response = await self.client.post(f"/api/courses/{course_id}/start")
        response.raise_for_status()
        return response.json()
    
    async def submit_quiz(self, course_id: str, answers: list) -> Dict[str, Any]:
        """Submit quiz answers"""
        response = await self.client.post(
            f"/api/courses/{course_id}/quiz",
            json={"answers": answers}
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the client connection"""
        await self.client.aclose()

# Usage example
async def main():
    client = CybersecAPIClient()
    try:
        # Login
        await client.login("user@company.com", "password123")
        
        # Get courses
        courses = await client.get_courses()
        print(f"Available courses: {len(courses)}")
        
        # Start first course
        if courses:
            course = courses[0]
            progress = await client.start_course(course["id"])
            print(f"Started course: {course['title']}")
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 JavaScript/TypeScript Client Example
```typescript
// api-client.ts
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface Course {
  id: string;
  title: string;
  description: string;
  duration_minutes: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

class CybersecAPIClient {
  private baseURL: string;
  private token: string | null = null;
  
  constructor(baseURL: string = 'https://bootstrap-awareness.de') {
    this.baseURL = baseURL;
  }
  
  async login(email: string, password: string): Promise<TokenResponse> {
    const response = await fetch(`${this.baseURL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
        grant_type: 'password',
      }),
    });
    
    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }
    
    const data = await response.json();
    this.token = data.access_token;
    return data;
  }
  
  async getCourses(): Promise<Course[]> {
    const response = await this.authFetch('/api/courses');
    return response.json();
  }
  
  async startCourse(courseId: string) {
    const response = await this.authFetch(`/api/courses/${courseId}/start`, {
      method: 'POST',
    });
    return response.json();
  }
  
  private async authFetch(endpoint: string, options: RequestInit = {}) {
    if (!this.token) {
      throw new Error('Not authenticated');
    }
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${this.token}`,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }
    
    return response;
  }
}

// Usage
const client = new CybersecAPIClient();

async function example() {
  try {
    // Login
    await client.login('user@company.com', 'password123');
    
    // Get courses
    const courses = await client.getCourses();
    console.log(`Available courses: ${courses.length}`);
    
    // Start first course
    if (courses.length > 0) {
      const progress = await client.startCourse(courses[0].id);
      console.log('Course started:', progress);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### 2.3 cURL Examples
```bash
# Login
curl -X POST https://bootstrap-awareness.de/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@company.com&password=password123&grant_type=password"

# Get courses (with token)
curl -X GET https://bootstrap-awareness.de/api/courses \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Start course
curl -X POST https://bootstrap-awareness.de/api/courses/COURSE_ID/start \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Submit quiz
curl -X POST https://bootstrap-awareness.de/api/courses/COURSE_ID/quiz \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": "q1", "answer_id": "a"},
      {"question_id": "q2", "answer_id": "b"}
    ]
  }'

# Generate compliance report
curl -X GET "https://bootstrap-awareness.de/api/reports/compliance/nis2?start_date=2025-01-01&end_date=2025-01-31&format=pdf" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o compliance-report.pdf
```

## 3. Webhook Events

### 3.1 Webhook Configuration
```json
{
  "webhook_url": "https://your-app.com/webhooks/cybersec",
  "events": [
    "user.created",
    "user.completed_course",
    "phishing.campaign_completed",
    "compliance.alert"
  ],
  "secret": "your-webhook-secret"
}
```

### 3.2 Event Payloads
```json
// user.completed_course
{
  "event": "user.completed_course",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "course_id": "456e7890-e89b-12d3-a456-426614174000",
    "score": 95,
    "certificate_id": "789e0123-e89b-12d3-a456-426614174000"
  }
}

// phishing.campaign_completed
{
  "event": "phishing.campaign_completed",
  "timestamp": "2025-01-15T15:00:00Z",
  "data": {
    "campaign_id": "abc12345-e89b-12d3-a456-426614174000",
    "company_id": "def67890-e89b-12d3-a456-426614174000",
    "results": {
      "total_recipients": 150,
      "clicked": 12,
      "reported": 45,
      "click_rate": 8.0,
      "report_rate": 30.0
    }
  }
}
```

## 4. Rate Limiting Details

### 4.1 Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642329600
```

### 4.2 Rate Limit Tiers
- **Free Tier**: 100 requests/minute
- **Professional**: 500 requests/minute
- **Enterprise**: 2000 requests/minute
- **Custom**: Negotiable

## 5. Error Handling

### 5.1 Error Response Format
```json
{
  "detail": "Detailed error message",
  "code": "ERROR_CODE",
  "field": "field_name", // Optional, for validation errors
  "request_id": "req_123456" // For support reference
}
```

### 5.2 Common Error Codes
- `UNAUTHORIZED`: Invalid or missing authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Input validation failed
- `RATE_LIMITED`: Too many requests
- `INTERNAL_ERROR`: Server error
- `MAINTENANCE`: Service temporarily unavailable

## 6. API Versioning

### 6.1 Version Strategy
- URL versioning: `/api/v1/`, `/api/v2/` (currently using `/api/` without version)
- Breaking changes require new version
- Deprecation notice: 6 months
- Sunset period: 12 months

### 6.2 Version Headers
```http
X-API-Version: 1.0
X-API-Deprecation-Date: 2026-01-01
X-API-Sunset-Date: 2026-07-01
```

Diese umfassende API-Dokumentation bietet Entwicklern alle notwendigen Informationen zur Integration mit der Cybersecurity Awareness Platform.