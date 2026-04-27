export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ?? "";

export interface TwitterTrend {
  rank: number;
  name: string;
  tweet_volume: string | null;
  url: string | null;
}

export interface NewsItem {
  title: string;
  url: string;
  source: string | null;
}

export interface GoogleTrend {
  rank: number;
  title: string;
  traffic: string | null;
  pub_date: string | null;
  picture: string | null;
  news: NewsItem[];
}

export interface TrendsResponse<T> {
  source: string;
  country: string;
  fetched_at: string;
  count: number;
  trends: T[];
}

export interface ScriptSection {
  label: string;
  timecode: string;
  text: string;
}

export interface ShortsScript {
  title: string;
  sections: ScriptSection[];
  duration_seconds: number;
  word_count: number;
  full_text: string;
  sources: { twitter: string[]; google: string[] };
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, init);
  if (!res.ok) {
    let detail = "";
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      try {
        detail = await res.text();
      } catch {
        // ignore
      }
    }
    throw new Error(`${res.status} ${res.statusText}${detail ? ` — ${detail}` : ""}`);
  }
  return (await res.json()) as T;
}

export const api = {
  twitter: () => fetchJson<TrendsResponse<TwitterTrend>>("/api/trends/twitter"),
  google: () => fetchJson<TrendsResponse<GoogleTrend>>("/api/trends/google"),
  generateScript: (topN = 3) =>
    fetchJson<{ generated_at: string; script: ShortsScript }>("/api/script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ top_n: topN }),
    }),
  refresh: () =>
    fetchJson<{ cleared: boolean; time: string }>("/api/refresh", {
      method: "POST",
    }),
};
