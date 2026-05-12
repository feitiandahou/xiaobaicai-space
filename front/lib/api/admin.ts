import { API_BASE_URL, type ApiPaginationMeta, type Post } from "./index";

export type LoginResult = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: {
    id: number;
    username: string;
    role: string;
    is_active: boolean;
  };
};

export type AdminDashboard = {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  category_count: number;
  tag_count: number;
  posts_created_last_7_days: number;
  recent_logs: Array<{
    id: number;
    action: string;
    detail?: string | null;
    created_at: string;
    admin_name?: string | null;
  }>;
  generated_at: string;
};

export type CategoryOption = {
  id: number;
  name: string;
  slug: string;
  post_count?: number;
};

export type TagOption = {
  id: number;
  name: string;
  slug: string;
  post_count?: number;
};

export type CategoryCreateData = {
  name: string;
  slug: string;
  description?: string | null;
  parent_id?: number;
  sort_order?: number;
  icon?: string | null;
  status?: number;
};

export type CategoryUpdateData = {
  name?: string;
  slug?: string;
};

export type TagCreateData = {
  name: string;
  slug: string;
};

export type TagUpdateData = {
  name?: string;
  slug?: string;
};

export type AdminSetting = {
  id: number;
  key: string;
  value: string | null;
  updated_at: string;
};

export type PostCreateData = {
  user_id: number;
  title: string;
  slug?: string;
  summary?: string;
  content: string;
  cover_image?: string;
  category_id?: number | null;
  status: number;
  is_top?: number;
  created_at?: string | null;
  published_at?: string | null;
  tag_ids: number[];
};

export type PostUpdateData = {
  title?: string;
  slug?: string;
  summary?: string;
  content?: string;
  cover_image?: string;
  category_id?: number | null;
  status?: number;
  is_top?: number;
  created_at?: string | null;
  published_at?: string | null;
  tag_ids?: number[];
};

async function parseJsonResponse<T>(response: Response): Promise<T> {
  const payload = await response.json();
  if (!response.ok) {
    const detail =
      (payload && (payload.detail || payload.message || payload.code)) ||
      `Request failed (${response.status})`;
    throw new Error(String(detail));
  }
  return payload as T;
}

function getAuthHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function loginAdmin(account: string, password: string): Promise<LoginResult> {
  const response = await fetch(`${API_BASE_URL}/users/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ account, password }),
  });
  return parseJsonResponse<LoginResult>(response);
}

export async function fetchAdminDashboard(token: string): Promise<AdminDashboard> {
  const response = await fetch(`${API_BASE_URL}/admin/dashboard`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });
  const payload = await parseJsonResponse<{ data: AdminDashboard }>(response);
  return payload.data;
}

export async function fetchAdminPosts(
  token: string,
  params?: { page?: number; page_size?: number; search?: string }
): Promise<{ data: Post[]; meta: ApiPaginationMeta }> {
  const query = new URLSearchParams();
  query.set("page", String(params?.page || 1));
  query.set("page_size", String(params?.page_size || 20));
  query.set("include_drafts", "true");
  query.set("include_deleted", "false");
  if (params?.search) {
    query.set("search", params.search);
  }

  const response = await fetch(`${API_BASE_URL}/admin/posts?${query.toString()}`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });

  const payload = await parseJsonResponse<{
    data: Post[];
    meta: ApiPaginationMeta;
  }>(response);

  return payload;
}

export async function fetchAdminPostById(token: string, id: string): Promise<Post> {
  const response = await fetch(`${API_BASE_URL}/admin/posts/${id}`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });

  const payload = await parseJsonResponse<{ data: Post }>(response);
  return payload.data;
}

export async function fetchAdminCategories(token: string): Promise<CategoryOption[]> {
  const response = await fetch(`${API_BASE_URL}/admin/categories`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });

  const payload = await parseJsonResponse<{
    data: CategoryOption[];
  }>(response);

  return payload.data;
}

export async function fetchAdminTags(token: string): Promise<TagOption[]> {
  const response = await fetch(`${API_BASE_URL}/admin/tags`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });

  const payload = await parseJsonResponse<{
    data: TagOption[];
  }>(response);

  return payload.data;
}

export async function fetchAdminSettings(token: string): Promise<AdminSetting[]> {
  const response = await fetch(`${API_BASE_URL}/admin/settings`, {
    headers: getAuthHeaders(token),
    cache: "no-store",
  });

  const payload = await parseJsonResponse<{
    data: AdminSetting[];
  }>(response);

  return payload.data;
}

export async function updateAdminSetting(token: string, key: string, value: string | null): Promise<AdminSetting> {
  const response = await fetch(`${API_BASE_URL}/admin/settings/${encodeURIComponent(key)}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ value }),
  });

  const payload = await parseJsonResponse<{ data: AdminSetting }>(response);
  return payload.data;
}

export async function createAdminCategory(
  token: string,
  categoryData: CategoryCreateData
): Promise<CategoryOption> {
  const response = await fetch(`${API_BASE_URL}/admin/categories`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      parent_id: 0,
      sort_order: 0,
      status: 1,
      ...categoryData,
    }),
  });

  const payload = await parseJsonResponse<{ data: CategoryOption }>(response);
  return payload.data;
}

export async function deleteAdminCategory(token: string, id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/categories/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  await parseJsonResponse<{ message: string }>(response);
}

export async function updateAdminCategory(
  token: string,
  id: number,
  categoryData: CategoryUpdateData
): Promise<CategoryOption> {
  const response = await fetch(`${API_BASE_URL}/admin/categories/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(categoryData),
  });

  const payload = await parseJsonResponse<{ data: CategoryOption }>(response);
  return payload.data;
}

export async function createAdminTag(token: string, tagData: TagCreateData): Promise<TagOption> {
  const response = await fetch(`${API_BASE_URL}/admin/tags`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(tagData),
  });

  const payload = await parseJsonResponse<{ data: TagOption }>(response);
  return payload.data;
}

export async function deleteAdminTag(token: string, id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/tags/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  await parseJsonResponse<{ message: string }>(response);
}

export async function updateAdminTag(token: string, id: number, tagData: TagUpdateData): Promise<TagOption> {
  const response = await fetch(`${API_BASE_URL}/admin/tags/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(tagData),
  });

  const payload = await parseJsonResponse<{ data: TagOption }>(response);
  return payload.data;
}

export async function createPost(token: string, postData: PostCreateData): Promise<Post> {
  const response = await fetch(`${API_BASE_URL}/admin/posts`, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(postData),
  });
  const payload = await parseJsonResponse<{ data: Post }>(response);
  return payload.data;
}

export async function updatePost(token: string, id: string, postData: PostUpdateData): Promise<Post> {
  const response = await fetch(`${API_BASE_URL}/admin/posts/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(postData),
  });
  const payload = await parseJsonResponse<{ data: Post }>(response);
  return payload.data;
}

export async function deletePost(token: string, id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/admin/posts/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  await parseJsonResponse<{ message: string }>(response);
}
