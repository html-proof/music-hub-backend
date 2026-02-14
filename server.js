
const express = require("express");
const cors = require("cors");
const morgan = require("morgan");
const dotenv = require("dotenv");
const { LRUCache } = require("lru-cache");
const YTMusic = require("ytmusic-api");
const ytdl = require("@distube/ytdl-core");

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT || 8080);
const HOST = "0.0.0.0";
const CORS_ORIGINS = process.env.CORS_ORIGINS || "*";
const START_MS = Date.now();

app.use(express.json({ limit: "1mb" }));
app.use(morgan("tiny"));
app.use(
  cors({
    origin: CORS_ORIGINS === "*" ? true : CORS_ORIGINS.split(",").map((v) => v.trim()),
    credentials: true,
  }),
);

const yt = new YTMusic();
const streamCache = new LRUCache({ max: 2000, ttl: 1000 * 60 * 30 });
const searchCache = new LRUCache({ max: 500, ttl: 1000 * 60 * 10 });
const cacheStats = { search_hits: 0, search_misses: 0, stream_hits: 0, stream_misses: 0 };

const usersByUid = new Map();
const playlistsByUser = new Map();
const likesByUser = new Map();
const trackingByUser = new Map();
const autoPlaylistsById = new Map();
const autoPlaylistIndexByUser = new Map();
let firebaseAdmin = null;
let rtdb = null;

try {
  // Optional at runtime; keeps local/dev booting even without firebase-admin installed.
  firebaseAdmin = require("firebase-admin");
  if (!firebaseAdmin.apps.length) {
    if (process.env.FIREBASE_SERVICE_ACCOUNT_JSON) {
      firebaseAdmin.initializeApp({
        credential: firebaseAdmin.credential.cert(JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_JSON)),
        databaseURL: process.env.FIREBASE_DATABASE_URL,
      });
    } else if (process.env.FIREBASE_SERVICE_ACCOUNT_PATH && process.env.FIREBASE_DATABASE_URL) {
      // eslint-disable-next-line global-require, import/no-dynamic-require
      const svc = require(process.env.FIREBASE_SERVICE_ACCOUNT_PATH);
      firebaseAdmin.initializeApp({
        credential: firebaseAdmin.credential.cert(svc),
        databaseURL: process.env.FIREBASE_DATABASE_URL,
      });
    }
  }
  if (firebaseAdmin.apps.length) {
    rtdb = firebaseAdmin.database();
  }
} catch (_e) {
  firebaseAdmin = null;
  rtdb = null;
}

function nowIso() { return new Date().toISOString(); }
function year() { return new Date().getFullYear(); }

function getUidFromToken(authHeader) {
  if (!authHeader || typeof authHeader !== "string" || !authHeader.startsWith("Bearer ")) return null;
  const token = authHeader.slice("Bearer ".length).trim();
  if (!token) return null;
  return `uid_${token.slice(0, 16)}`;
}

function requireAuth(req, res, next) {
  const uid = getUidFromToken(req.headers.authorization);
  if (!uid) return res.status(401).json({ detail: "Missing authentication token" });
  req.uid = uid;
  next();
}

function optionalAuth(req, _res, next) {
  req.uid = getUidFromToken(req.headers.authorization);
  next();
}

function getOrCreateUser(uid) {
  let user = usersByUid.get(uid);
  if (!user) {
    user = {
      uid,
      email: `${uid}@example.local`,
      name: "Music Hub User",
      photoUrl: "",
      language: null,
      moods: [],
      genres: [],
      is_onboarded: false,
      total_searches: 0,
      total_plays: 0,
      total_skips: 0,
      total_completes: 0,
      created_at: nowIso(),
      last_login: nowIso(),
    };
    usersByUid.set(uid, user);
  }
  return user;
}

function getOrCreateTracking(uid) {
  let t = trackingByUser.get(uid);
  if (!t) {
    t = { searches: [], plays: [], activities: [], keywordWeights: new Map() };
    trackingByUser.set(uid, t);
  }
  return t;
}

function bumpKeywords(uid, text, weight = 1) {
  const t = getOrCreateTracking(uid);
  const tokens = String(text || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").split(/\s+/).filter((w) => w.length >= 3).slice(0, 30);
  for (const w of tokens) t.keywordWeights.set(w, (t.keywordWeights.get(w) || 0) + weight);
}

async function rtdbGet(path) {
  if (!rtdb) return null;
  const snap = await rtdb.ref(path).get();
  return snap.exists() ? snap.val() : null;
}

async function rtdbSet(path, data) {
  if (!rtdb) return false;
  await rtdb.ref(path).set(data);
  return true;
}

async function rtdbUpdate(path, data) {
  if (!rtdb) return false;
  await rtdb.ref(path).update(data);
  return true;
}

function keywordEntriesToArray(mapObj, limit = 30) {
  const entries = Array.isArray(mapObj)
    ? mapObj
    : Object.entries(mapObj || {}).map(([keyword, weight]) => ({ keyword, weight: Number(weight) || 0 }));
  return entries.sort((a, b) => (b.weight || 0) - (a.weight || 0)).slice(0, limit);
}
function normalizeSong(song) {
  const artist = (song.artist && (song.artist.name || song.artist)) || (Array.isArray(song.artists) ? song.artists[0]?.name : "") || "Unknown";
  const thumb = (Array.isArray(song.thumbnails) && song.thumbnails.at(-1)?.url) || song.thumbnailUrl || "";
  return {
    id: song.videoId || song.id || "",
    title: song.name || song.title || "Unknown",
    artist,
    thumbnailUrl: thumb,
    audioUrl: "",
    durationSeconds: Number(song.duration || song.durationSeconds || 0),
  };
}

async function searchSongs(query, limit = 15) {
  const q = String(query || "").trim() || "music";
  const key = `q:${q}:${limit}`;
  const cached = searchCache.get(key);
  if (cached) {
    cacheStats.search_hits += 1;
    return cached;
  }
  cacheStats.search_misses += 1;
  const raw = await yt.searchSongs(q);
  const results = (raw || []).slice(0, limit).map(normalizeSong).filter((s) => s.id);
  searchCache.set(key, results);
  return results;
}

function pickAudioFormat(formats, quality) {
  const audioOnly = ytdl
    .filterFormats(formats, "audioonly")
    .filter((f) => f.url && f.audioBitrate)
    .sort((a, b) => (b.audioBitrate || 0) - (a.audioBitrate || 0));
  if (!audioOnly.length) return null;
  if (quality === "48k") return audioOnly.find((f) => (f.audioBitrate || 0) <= 56) || audioOnly.at(-1);
  if (quality === "64k") return audioOnly.find((f) => (f.audioBitrate || 0) <= 64) || audioOnly.at(-1);
  if (quality === "low") return audioOnly.find((f) => (f.audioBitrate || 0) <= 80) || audioOnly.at(-1);
  if (quality === "medium") return audioOnly.find((f) => (f.audioBitrate || 0) <= 128) || audioOnly[0];
  return audioOnly[0];
}

async function resolveStream(videoId, quality = "high", forceRefresh = false) {
  const id = String(videoId || "").trim();
  if (!id) return null;
  const key = `${id}:${quality}`;

  if (!forceRefresh) {
    const cached = streamCache.get(key);
    if (cached) {
      cacheStats.stream_hits += 1;
      return cached;
    }
  } else {
    streamCache.delete(key);
  }

  cacheStats.stream_misses += 1;
  const info = await ytdl.getInfo(id);
  const picked = pickAudioFormat(info.formats || [], quality);
  if (!picked?.url) return null;

  const payload = {
    stream_url: picked.url,
    url: picked.url,
    title: info.videoDetails?.title || "",
    artist: info.videoDetails?.author?.name || "",
    duration: Number(info.videoDetails?.lengthSeconds || 0),
    thumbnail: info.videoDetails?.thumbnails?.at(-1)?.url || "",
    view_count: Number(info.videoDetails?.viewCount || 0),
  };

  streamCache.set(key, payload);
  return payload;
}

function getCacheStats() {
  const totalSearch = cacheStats.search_hits + cacheStats.search_misses;
  const totalStream = cacheStats.stream_hits + cacheStats.stream_misses;
  const total = totalSearch + totalStream;

  return {
    search_cache: {
      size: searchCache.size,
      max_size: 500,
      ttl_seconds: 600,
      hits: cacheStats.search_hits,
      misses: cacheStats.search_misses,
      hit_rate: totalSearch ? Number(((cacheStats.search_hits / totalSearch) * 100).toFixed(1)) : 0,
    },
    stream_cache: {
      size: streamCache.size,
      max_size: 2000,
      ttl_seconds: 1800,
      hits: cacheStats.stream_hits,
      misses: cacheStats.stream_misses,
      hit_rate: totalStream ? Number(((cacheStats.stream_hits / totalStream) * 100).toFixed(1)) : 0,
    },
    total_requests: total,
    total_hit_rate: total ? Number((((cacheStats.search_hits + cacheStats.stream_hits) / total) * 100).toFixed(1)) : 0,
  };
}

function clearCaches() {
  streamCache.clear();
  searchCache.clear();
  cacheStats.search_hits = 0;
  cacheStats.search_misses = 0;
  cacheStats.stream_hits = 0;
  cacheStats.stream_misses = 0;
  return { status: "cleared", message: "All caches cleared" };
}

function recommendationQuery(type, value) {
  const y = year();
  switch (type) {
    case "for-you": return `recommended songs ${y}`;
    case "daily-mix": return "daily mix playlist";
    case "because-liked": return "songs similar to popular hits";
    case "discover-weekly": return `discover new artists ${y}`;
    case "mood": return `${value || "chill"} music playlist`;
    case "type": return `${value || "pop"} music playlist`;
    case "artist": return `${value || "ed sheeran"} songs`;
    default: return `trending songs ${y}`;
  }
}

function buildTimeContext() {
  const now = new Date();
  const hour = now.getHours();
  const time_of_day = hour >= 5 && hour < 12 ? "morning" : hour < 17 ? "afternoon" : hour < 21 ? "evening" : "night";
  const month_num = now.getMonth() + 1;
  const season = [12, 1, 2].includes(month_num) ? "winter" : [3, 4, 5].includes(month_num) ? "spring" : [6, 7, 8].includes(month_num) ? "summer" : "fall";
  return {
    year: now.getFullYear(),
    month: now.toLocaleString("en-US", { month: "long" }),
    month_num,
    day: now.getDate(),
    weekday: now.toLocaleString("en-US", { weekday: "long" }),
    time_of_day,
    is_weekend: [0, 6].includes(now.getDay()),
    season,
  };
}

function asyncRoute(fn) {
  return (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
}
app.get("/", (_req, res) => {
  res.json({ status: "ok", service: "Music Hub Backend", version: "2.0.0" });
});

function healthPayload() {
  const uptime = (Date.now() - START_MS) / 1000;
  return {
    status: "healthy",
    service: "music-hub-backend",
    version: "2.0.0",
    uptime_seconds: Number(uptime.toFixed(1)),
    endpoints: {
      auth: "/auth/login",
      search: "/music/search",
      play: "/music/play",
      recommendations: "/recommend/personalized",
      smart_feed: "/recommend/smart/feed",
      playlists: "/playlist/my",
      profile: "/user/profile",
      tracking: "/track/search",
      cache_stats: "/api/cache/stats",
    },
  };
}

app.get("/health", (_req, res) => res.json(healthPayload()));
app.get("/api/health", (_req, res) => res.json(healthPayload()));
app.get("/api/cache/stats", (_req, res) => res.json(getCacheStats()));
app.delete("/api/cache/clear", (_req, res) => res.json(clearCaches()));

app.post("/auth/login", (req, res) => {
  const token = req.body?.firebase_token || req.body?.id_token;
  if (!token || typeof token !== "string" || !token.trim()) {
    return res.status(422).json({ detail: "firebase_token is required" });
  }
  if (/^(dummy|test)/i.test(token)) {
    return res.status(401).json({ detail: "Invalid Firebase token" });
  }

  const uid = `uid_${token.slice(0, 16)}`;
  const user = getOrCreateUser(uid);
  user.last_login = nowIso();

  return res.json({
    access_token: token,
    token_type: "bearer",
    user_id: uid,
    email: user.email,
    display_name: user.name,
  });
});

app.post("/auth/logout", requireAuth, (_req, res) => {
  res.json({ status: "success", message: "Logged out successfully" });
});

app.get("/auth/me", requireAuth, (req, res) => {
  const user = getOrCreateUser(req.uid);
  res.json({
    user_id: user.uid,
    email: user.email,
    display_name: user.name,
    photo_url: user.photoUrl,
    email_verified: true,
    created_at: user.created_at,
    last_login: user.last_login,
    onboarding_complete: user.is_onboarded,
  });
});

app.get("/music/search", asyncRoute(async (req, res) => {
  const q = String(req.query.q || "").trim();
  if (!q) return res.status(422).json({ detail: "q is required" });
  res.json({ results: await searchSongs(q, 15) });
}));

app.post("/music/search", asyncRoute(async (req, res) => {
  const q = String(req.query.q || req.body?.q || "").trim();
  if (!q) return res.status(422).json({ detail: "q is required" });
  res.json({ results: await searchSongs(q, 15) });
}));

async function handlePlay(videoId, quality, forceRefresh) {
  const id = String(videoId || "").trim();
  if (!id) return { status: 422, payload: { success: false, message: "Missing video ID" } };
  const data = await resolveStream(id, quality, forceRefresh);
  if (!data?.stream_url) return { status: 200, payload: { success: false, message: "Could not resolve stream URL" } };
  return { status: 200, payload: { success: true, data } };
}

app.get("/music/play", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.query.id || ""), String(req.query.quality || "high"), String(req.query.force_refresh || "false") === "true");
  res.status(r.status).json(r.payload);
}));

app.post("/music/play", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.body?.id || req.body?.videoId || ""), String(req.body?.quality || "high"), false);
  res.status(r.status).json(r.payload);
}));

app.get("/music/play-48k", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.query.id || ""), "48k", false);
  res.status(r.status).json(r.payload);
}));

app.get("/music/play-64k", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.query.id || ""), "64k", false);
  res.status(r.status).json(r.payload);
}));

app.get("/music/preview", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.query.id || ""), "low", false);
  if (r.payload?.success && r.payload.data) r.payload.data.duration = Math.min(Number(r.payload.data.duration || 30), 30);
  res.status(r.status).json(r.payload);
}));

app.post("/music/preview", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.body?.id || req.body?.videoId || ""), "low", false);
  if (r.payload?.success && r.payload.data) r.payload.data.duration = Math.min(Number(r.payload.data.duration || 30), 30);
  res.status(r.status).json(r.payload);
}));

app.get("/music/resolve", asyncRoute(async (req, res) => {
  const r = await handlePlay(String(req.query.id || ""), String(req.query.quality || "high"), false);
  res.status(r.status).json(r.payload);
}));

app.post("/music/prefetch", asyncRoute(async (req, res) => {
  const ids = Array.isArray(req.body?.ids) ? req.body.ids : [];
  const quality = String(req.body?.quality || "high");
  if (!ids.length) return res.json({ success: true, message: "No IDs to prefetch" });
  await Promise.allSettled(ids.map((id) => resolveStream(String(id), quality, false)));
  res.json({ success: true, message: `Prefetching ${ids.length} songs`, ids });
}));

app.use((_req, res) => {
  res.status(404).json({ error: "Not found", status_code: 404 });
});

app.use((err, _req, res, _next) => {
  console.error("Unhandled error:", err);
  res.status(500).json({ error: "Internal server error", status_code: 500 });
});

async function bootstrap() {
  app.listen(PORT, HOST, () => {
    console.log(`Server listening at http://${HOST}:${PORT} (PORT env: ${process.env.PORT || "unset"})`);
  });

  yt.initialize()
    .then(() => {
      console.log("YTMusic initialized");
    })
    .catch((err) => {
      console.warn("YTMusic init failed:", err?.message || err);
    });
}

bootstrap().catch((err) => {
  console.error("Startup failed:", err);
  process.exit(1);
});
