# 📋 Royal Prompts Admin API Endpoints

## 🔐 Authentication Endpoints
**Base URL**: `/api/admin/auth`

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/login` | Admin login | `AdminLogin` | `AdminLoginResponse` |
| `GET` | `/me` | Get current admin profile | - | `AdminResponse` |

### Examples:
```typescript
// Login
POST /api/admin/auth/login
{
  "email": "admin@example.com", 
  "password": "password"
}

// Get current admin
GET /api/admin/auth/me
Authorization: Bearer <token>
```

---

## 📊 Dashboard Endpoints
**Base URL**: `/api/admin/dashboard`

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/` | Get dashboard statistics | `DashboardStats` |

### Examples:
```typescript
// Get dashboard stats
GET /api/admin/dashboard
Authorization: Bearer <token>
```

---

## 📝 Prompts Management Endpoints
**Base URL**: `/api/admin/prompts`

| Method | Endpoint | Description | Query Params | Request Body | Response |
|--------|----------|-------------|--------------|--------------|----------|
| `GET` | `/` | Get prompts list | `page`, `limit`, `search`, `category_id`, `status` | - | `PaginatedResponse<PromptAdmin>` |
| `POST` | `/` | Create new prompt | - | `PromptCreate` | `PromptAdmin` |
| `PUT` | `/{prompt_id}` | Update prompt | - | `PromptUpdate` | `PromptAdmin` |
| `DELETE` | `/{prompt_id}` | Delete prompt | - | - | `{message: string}` |
| `POST` | `/upload-image` | Upload prompt image | - | `FormData` | `ImageUploadResponse` |

### Examples:
```typescript
// Get prompts with filters
GET /api/admin/prompts?page=1&limit=20&search=email&category_id=business
Authorization: Bearer <token>

// Create prompt
POST /api/admin/prompts
Authorization: Bearer <token>
{
  "title": "Email Writer",
  "description": "Professional email writing assistant",
  "content": "Write a professional email for...",
  "category_id": "business",
  "tags": ["email", "professional"],
  "is_featured": false
}

// Update prompt
PUT /api/admin/prompts/123
Authorization: Bearer <token>
{
  "is_featured": true,
  "status": "published"
}

// Upload image
POST /api/admin/prompts/upload-image
Authorization: Bearer <token>
Content-Type: multipart/form-data
FormData: file=<image_file>
```

---

## 📂 Categories Management Endpoints
**Base URL**: `/api/admin/categories`

| Method | Endpoint | Description | Query Params | Request Body | Response |
|--------|----------|-------------|--------------|--------------|----------|
| `GET` | `/` | Get categories list | `page`, `limit`, `search`, `is_active` | - | `PaginatedResponse<CategoryAdmin>` |
| `POST` | `/` | Create new category | - | `CategoryCreate` | `CategoryAdmin` |
| `PUT` | `/{category_id}` | Update category | - | `CategoryUpdate` | `CategoryAdmin` |
| `DELETE` | `/{category_id}` | Delete category | - | - | `{message: string}` |
| `POST` | `/{category_id}/toggle-status` | Toggle category status | - | - | `CategoryAdmin` |

### Examples:
```typescript
// Get categories with filters
GET /api/admin/categories?page=1&limit=20&is_active=true
Authorization: Bearer <token>

// Create category
POST /api/admin/categories
Authorization: Bearer <token>
{
  "name": "Business",
  "description": "Business and professional prompts",
  "slug": "business",
  "order": 1
}

// Toggle category status
POST /api/admin/categories/123/toggle-status
Authorization: Bearer <token>
```

---

## 🔍 API Service Coverage Status

### ✅ Fully Implemented Services:

#### **AuthApiService** (`auth-api.ts`)
- ✅ `POST /api/admin/auth/login` → `login()`
- ✅ `GET /api/admin/auth/me` → `getCurrentAdmin()`
- ✅ Local logout → `logout()`

#### **PromptApiService** (`prompt-api.ts`)
- ✅ `GET /api/admin/prompts` → `getPrompts()`
- ✅ `POST /api/admin/prompts` → `createPrompt()`
- ✅ `PUT /api/admin/prompts/{id}` → `updatePrompt()`
- ✅ `DELETE /api/admin/prompts/{id}` → `deletePrompt()`
- ✅ `POST /api/admin/prompts/upload-image` → `uploadImage()`
- ✅ Search functionality → `searchPrompts()`
- ✅ Feature operations → `featurePrompt()`, `unfeaturePrompt()`
- ✅ Status operations → `publishPrompt()`, `archivePrompt()`

#### **CategoryApiService** (`category-api.ts`)
- ✅ `GET /api/admin/categories` → `getCategories()`
- ✅ `POST /api/admin/categories` → `createCategory()`
- ✅ `PUT /api/admin/categories/{id}` → `updateCategory()`
- ✅ `DELETE /api/admin/categories/{id}` → `deleteCategory()`
- ✅ `POST /api/admin/categories/{id}/toggle-status` → `toggleStatus()`
- ✅ Search functionality → `searchCategories()`

#### **DashboardApiService** (`dashboard-api.ts`)
- ✅ `GET /api/admin/dashboard` → `getDashboardStats()`
- ✅ Mock chart data → `getChartData()`
- ✅ Recent prompts → `getRecentPrompts()`

---

## 🚀 API Services Usage in Components

### **Authentication**
```typescript
import { authApi } from '@/services';

// Login
const response = await authApi.login({ email, password });

// Get current admin
const admin = await authApi.getCurrentAdmin();
```

### **Prompts Management**
```typescript
import { promptApi } from '@/services';

// Get prompts with filters
const prompts = await promptApi.getPrompts({
  page: 1,
  limit: 20,
  search: 'email',
  category_id: 'business'
});

// Create prompt
const newPrompt = await promptApi.createPrompt(promptData);

// Upload image
const imageResponse = await promptApi.uploadImage(file);

// Feature/unfeature prompt
await promptApi.featurePrompt(promptId);
await promptApi.unfeaturePrompt(promptId);
```

### **Categories Management**
```typescript
import { categoryApi } from '@/services';

// Get categories
const categories = await categoryApi.getCategories({
  page: 1,
  limit: 50,
  is_active: true
});

// Create category
const newCategory = await categoryApi.createCategory(categoryData);

// Toggle status
await categoryApi.toggleStatus(categoryId);
```

### **Dashboard Data**
```typescript
import { dashboardApi } from '@/services';

// Get dashboard stats
const stats = await dashboardApi.getDashboardStats();

// Get chart data
const chartData = await dashboardApi.getChartData();

// Get recent prompts
const recentPrompts = await dashboardApi.getRecentPrompts();
```

---

## ✅ All Admin Endpoints Covered

**Total Endpoints**: 11  
**Implemented in API Services**: 11  
**Coverage**: 100% ✅

All admin endpoints are properly implemented in the corresponding API services with:
- ✅ Correct HTTP methods
- ✅ Proper URL paths  
- ✅ Type-safe parameters
- ✅ Authentication headers
- ✅ Error handling
- ✅ Response typing
