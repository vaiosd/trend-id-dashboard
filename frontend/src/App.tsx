import { useCallback, useEffect, useState } from "react";
import {
  api,
  type GoogleTrend,
  type ShortsScript,
  type TwitterTrend,
} from "./api";
import "./App.css";

interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

function initial<T>(): ApiState<T> {
  return { data: null, loading: true, error: null };
}

function formatTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("id-ID", {
      hour: "2-digit",
      minute: "2-digit",
      day: "2-digit",
      month: "short",
      timeZone: "Asia/Jakarta",
    });
  } catch {
    return iso;
  }
}

export default function App() {
  const [twitter, setTwitter] = useState<ApiState<{
    fetched_at: string;
    trends: TwitterTrend[];
  }>>(initial);
  const [google, setGoogle] = useState<ApiState<{
    fetched_at: string;
    trends: GoogleTrend[];
  }>>(initial);
  const [script, setScript] = useState<ApiState<ShortsScript>>({
    data: null,
    loading: false,
    error: null,
  });
  const [copyOk, setCopyOk] = useState(false);

  const loadTrends = useCallback(async (showLoading: boolean) => {
    if (showLoading) {
      setTwitter({ data: null, loading: true, error: null });
      setGoogle({ data: null, loading: true, error: null });
    }
    const [tw, gt] = await Promise.allSettled([api.twitter(), api.google()]);
    if (tw.status === "fulfilled") {
      setTwitter({
        data: { fetched_at: tw.value.fetched_at, trends: tw.value.trends },
        loading: false,
        error: null,
      });
    } else {
      setTwitter({ data: null, loading: false, error: String(tw.reason) });
    }
    if (gt.status === "fulfilled") {
      setGoogle({
        data: { fetched_at: gt.value.fetched_at, trends: gt.value.trends },
        loading: false,
        error: null,
      });
    } else {
      setGoogle({ data: null, loading: false, error: String(gt.reason) });
    }
  }, []);

  useEffect(() => {
    // Initial fetch on mount; setState inside the async function is intentional.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadTrends(false);
  }, [loadTrends]);

  const handleRefresh = useCallback(async () => {
    try {
      await api.refresh();
    } catch {
      // refresh endpoint just clears the cache; ignore errors and re-fetch anyway
    }
    await loadTrends(true);
  }, [loadTrends]);

  const handleGenerate = useCallback(async () => {
    setScript({ data: null, loading: true, error: null });
    setCopyOk(false);
    try {
      const res = await api.generateScript(3);
      setScript({ data: res.script, loading: false, error: null });
    } catch (err) {
      setScript({ data: null, loading: false, error: String(err) });
    }
  }, []);

  const handleCopy = useCallback(async () => {
    if (!script.data) return;
    try {
      await navigator.clipboard.writeText(script.data.full_text);
      setCopyOk(true);
      setTimeout(() => setCopyOk(false), 1800);
    } catch {
      setCopyOk(false);
    }
  }, [script.data]);

  return (
    <div className="page">
      <header className="hero">
        <div>
          <h1>
            Tren ID <span className="accent">Dashboard</span>
          </h1>
          <p className="sub">
            Topik viral hari ini di X (Twitter) &amp; Google Trends Indonesia,
            otomatis dirangkum jadi skrip Shorts 50 detik.
          </p>
        </div>
        <button className="btn btn-secondary" onClick={handleRefresh}>
          Refresh data
        </button>
      </header>

      <section className="grid">
        <TwitterPanel state={twitter} />
        <GooglePanel state={google} />
      </section>

      <section className="script-section">
        <div className="script-header">
          <div>
            <h2>Skrip Shorts 50 detik</h2>
            <p className="muted">
              Otomatis dibuat dari 3 tren teratas X dan Google. Klik "Generate"
              untuk merangkum tren terbaru hari ini.
            </p>
          </div>
          <div className="script-actions">
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={script.loading}
            >
              {script.loading ? "Membuat skrip…" : "Generate skrip"}
            </button>
            {script.data ? (
              <button className="btn btn-secondary" onClick={handleCopy}>
                {copyOk ? "Tersalin!" : "Salin teks"}
              </button>
            ) : null}
          </div>
        </div>

        {script.error ? (
          <div className="error">Gagal membuat skrip: {script.error}</div>
        ) : null}

        {script.data ? (
          <ScriptCard script={script.data} />
        ) : !script.loading ? (
          <div className="placeholder">
            Belum ada skrip. Klik <strong>Generate skrip</strong> untuk
            merangkum tren menjadi narasi 50 detik.
          </div>
        ) : null}
      </section>

      <footer className="foot">
        <span>
          Sumber X: <a href="https://trends24.in/indonesia/" target="_blank" rel="noreferrer">trends24.in</a>
        </span>
        <span>
          Sumber Google:{" "}
          <a
            href="https://trends.google.com/trending?geo=ID"
            target="_blank"
            rel="noreferrer"
          >
            trends.google.com
          </a>
        </span>
      </footer>
    </div>
  );
}

function TwitterPanel({
  state,
}: {
  state: ApiState<{ fetched_at: string; trends: TwitterTrend[] }>;
}) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>
          <span className="dot dot-x" /> X (Twitter) Indonesia
        </h2>
        <span className="muted">
          {state.data ? `Diambil ${formatTime(state.data.fetched_at)} WIB` : ""}
        </span>
      </div>
      {state.loading ? (
        <div className="placeholder">Memuat tren…</div>
      ) : state.error ? (
        <div className="error">{state.error}</div>
      ) : !state.data || state.data.trends.length === 0 ? (
        <div className="placeholder">Belum ada data tren.</div>
      ) : (
        <ol className="trend-list">
          {state.data.trends.slice(0, 25).map((t) => (
            <li key={`${t.rank}-${t.name}`}>
              <span className="rank">{t.rank}</span>
              {t.url ? (
                <a href={t.url} target="_blank" rel="noreferrer">
                  {t.name}
                </a>
              ) : (
                <span>{t.name}</span>
              )}
              {t.tweet_volume ? (
                <span className="vol">{t.tweet_volume}</span>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function GooglePanel({
  state,
}: {
  state: ApiState<{ fetched_at: string; trends: GoogleTrend[] }>;
}) {
  return (
    <div className="card">
      <div className="card-head">
        <h2>
          <span className="dot dot-g" /> Google Trends Indonesia
        </h2>
        <span className="muted">
          {state.data ? `Diambil ${formatTime(state.data.fetched_at)} WIB` : ""}
        </span>
      </div>
      {state.loading ? (
        <div className="placeholder">Memuat tren…</div>
      ) : state.error ? (
        <div className="error">{state.error}</div>
      ) : !state.data || state.data.trends.length === 0 ? (
        <div className="placeholder">Belum ada data tren.</div>
      ) : (
        <ul className="g-list">
          {state.data.trends.slice(0, 12).map((t) => (
            <li key={`${t.rank}-${t.title}`}>
              <div className="g-row">
                <span className="rank">{t.rank}</span>
                <span className="g-title">{t.title}</span>
                {t.traffic ? <span className="vol">{t.traffic} pencarian</span> : null}
              </div>
              {t.news.length > 0 ? (
                <a
                  className="g-news"
                  href={t.news[0].url}
                  target="_blank"
                  rel="noreferrer"
                  title={t.news[0].title}
                >
                  {t.news[0].source ? `${t.news[0].source}: ` : ""}
                  {t.news[0].title}
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ScriptCard({ script }: { script: ShortsScript }) {
  return (
    <div className="script-card">
      <div className="script-meta">
        <h3>{script.title}</h3>
        <div className="muted">
          {script.duration_seconds} detik · ~{script.word_count} kata
        </div>
      </div>
      <ol className="script-sections">
        {script.sections.map((s) => (
          <li key={s.label}>
            <div className="script-tag">
              <strong>{s.label}</strong>
              <span className="muted">{s.timecode}</span>
            </div>
            <p>{s.text}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
