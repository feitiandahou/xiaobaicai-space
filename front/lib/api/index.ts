export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001/api/v1";

export type ApiPaginationMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
};

export type SiteLink = {
  name: string;
  url: string;
  icon?: string | null;
};

export type SiteConfig = {
  title: string;
  subtitle?: string | null;
  description?: string | null;
  icp_beian?: string | null;
  social_links: SiteLink[];
  footer: {
    text?: string | null;
    copyright?: string | null;
    links: SiteLink[];
  };
  updated_at?: string | null;
};

export type Post = {
  id: number;
  user_id?: number;
  title: string;
  slug: string;
  summary?: string | null;
  content?: string;
  cover_image?: string | null;
  category_id?: number | null;
  status: number;
  is_top: number;
  published_at?: string | null;
  is_delete?: number;
  view_count: number;
  like_count: number;
  created_at: string;
  updated_at?: string;
  tags: string[];
  tag_ids: number[];
};

export type PostListResult = {
  data: Post[];
  meta: ApiPaginationMeta;
};

export type LikePostResult = {
  likeCount: number;
  alreadyLiked: boolean;
};

const VISITOR_ID_STORAGE_KEY = "visitor_id";
const ADMIN_ACCESS_TOKEN_STORAGE_KEY = "admin_access_token";

function logApiError(context: string, error: unknown): void {
  if (typeof window !== "undefined" && error instanceof TypeError) {
    return;
  }

  console.error(`${context}:`, error);
}

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

function normalizePost(raw: {
  id: number;
  user_id?: number;
  title: string;
  slug: string | null;
  summary?: string | null;
  content?: string;
  cover_image?: string | null;
  category_id?: number | null;
  status: number;
  is_top: number;
  published_at?: string | null;
  is_delete?: number;
  view_count: number;
  like_count: number;
  created_at: string;
  updated_at?: string;
  tags?: string[];
  tag_ids?: number[];
}): Post {
  return {
    id: raw.id,
    user_id: raw.user_id,
    title: raw.title,
    slug: raw.slug ?? "",
    summary: raw.summary,
    content: raw.content,
    cover_image: raw.cover_image,
    category_id: raw.category_id,
    status: raw.status,
    is_top: raw.is_top,
    published_at: raw.published_at,
    is_delete: raw.is_delete,
    view_count: raw.view_count,
    like_count: raw.like_count,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
    tags: raw.tags || [],
    tag_ids: raw.tag_ids || [],
  };
}

function getPersistentVisitorId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const existingVisitorId = window.localStorage.getItem(VISITOR_ID_STORAGE_KEY);
  if (existingVisitorId) {
    return existingVisitorId;
  }

  const nextVisitorId = typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `visitor-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  window.localStorage.setItem(VISITOR_ID_STORAGE_KEY, nextVisitorId);
  return nextVisitorId;
}

function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const accessToken = window.localStorage.getItem(ADMIN_ACCESS_TOKEN_STORAGE_KEY);
  return accessToken && accessToken.trim() ? accessToken : null;
}

export async function fetchSiteConfig(): Promise<SiteConfig | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/site-config`, {
      cache: "no-store",
    });
    const payload = await parseJsonResponse<{ data: SiteConfig }>(res);
    return payload.data;
  } catch (error) {
    logApiError("Error fetching site config", error);
    return null;
  }
}

export async function fetchPosts(params?: {
  page?: number;
  page_size?: number;
  search?: string;
}): Promise<PostListResult> {
  try {
    const query = new URLSearchParams();
    query.set("page", String(params?.page || 1));
    query.set("page_size", String(params?.page_size || 12));
    if (params?.search) {
      query.set("search", params.search);
    }

    const res = await fetch(`${API_BASE_URL}/posts?${query.toString()}`, {
      next: { revalidate: 10 },
    });
    const payload = await parseJsonResponse<{
      data: Array<{
        id: number;
        title: string;
        slug: string | null;
        summary?: string | null;
        cover_image?: string | null;
        status: number;
        is_top: number;
        view_count: number;
        like_count: number;
        published_at?: string | null;
        created_at: string;
        tags?: string[];
        tag_ids?: number[];
      }>;
      meta: ApiPaginationMeta;
    }>(res);

    return {
      data: payload.data.filter((item) => Boolean(item.slug)).map((item) => normalizePost(item)),
      meta: payload.meta,
    };
  } catch (error) {
    logApiError("Error fetching posts", error);
    return {
      data: [],
      meta: {
        page: 1,
        page_size: params?.page_size || 12,
        total: 0,
        total_pages: 0,
        has_next: false,
        has_prev: false,
      },
    };
  }
}

export async function fetchPostBySlug(slug: string): Promise<Post | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/posts/slug/${slug}`, {
      next: { revalidate: 10 },
    });
    const payload = await parseJsonResponse<{
      data: {
        id: number;
        user_id: number;
        title: string;
        slug: string | null;
        summary?: string | null;
        content: string;
        cover_image?: string | null;
        category_id?: number | null;
        status: number;
        is_top: number;
        published_at?: string | null;
        is_delete: number;
        view_count: number;
        like_count: number;
        created_at: string;
        updated_at: string;
        tags?: string[];
        tag_ids?: number[];
      };
    }>(res);
    return normalizePost(payload.data);
  } catch (error) {
    logApiError("Error fetching post", error);
    return null;
  }
}

export async function likePostAPI(slug: string): Promise<LikePostResult | null> {
  try {
    const visitorId = getPersistentVisitorId();
    const accessToken = getStoredAccessToken();
    const headers: HeadersInit = {};
    if (visitorId) {
      headers["X-Visitor-Id"] = visitorId;
    }
    if (accessToken) {
      headers.Authorization = `Bearer ${accessToken}`;
    }
    const res = await fetch(`${API_BASE_URL}/posts/slug/${slug}/like`, {
      method: "POST",
      credentials: "include",
      headers: Object.keys(headers).length > 0 ? headers : undefined,
    });
    const payload = await parseJsonResponse<{ like_count: number }>(res);
    return {
      likeCount: payload.like_count,
      alreadyLiked: false,
    };
  } catch (error) {
    if (error instanceof Error && error.message === "Already liked") {
      return {
        likeCount: 0,
        alreadyLiked: true,
      };
    }
    logApiError("Error liking post", error);
    return null;
  }
}
