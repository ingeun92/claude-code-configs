#!/usr/bin/env node
// Claude Code statusLine: a standalone replacement for the oh-my-claude-sisyphus HUD.
//
//   ~/Ing/playground/claude-code-configs | branch:main | !2 ?1
//   Model: Opus 5.5 | 5h:[#-------]8%(4h12m) wk:[#-------]10%(3d13h) fable:[--------]2%(3d13h) | ctx:[##--------]23% | session:42m
//
// Everything comes from the statusLine stdin payload except per-model weekly
// buckets (Fable etc.), which only the OAuth usage endpoint reports. That call
// runs in a detached child (`--refresh`) and lands in a cache file, so drawing
// never waits on the network.

import { execFileSync, spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { closeSync, fstatSync, mkdirSync, openSync, readFileSync, readSync, renameSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const CACHE_FILE = join(homedir(), '.claude', 'statusline', 'usage-cache.json');
const POLL_MS = 90_000;
const FAILURE_BACKOFF_MS = 2 * 60_000;
const RATE_LIMITED_BACKOFF_MS = 5 * 60_000;

const RESET = '\x1b[0m';
const DIM = '\x1b[2m';
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const CYAN = '\x1b[36m';
const SEP = `${DIM} | ${RESET}`;

const dim = (s) => `${DIM}${s}${RESET}`;
const paint = (color, s) => `${color}${s}${RESET}`;

// --- usage cache -------------------------------------------------------------

function readCache() {
  try {
    return JSON.parse(readFileSync(CACHE_FILE, 'utf8'));
  } catch {
    return {};
  }
}

function writeCache(cache) {
  mkdirSync(dirname(CACHE_FILE), { recursive: true });
  const tmp = `${CACHE_FILE}.${process.pid}`;
  writeFileSync(tmp, JSON.stringify(cache));
  renameSync(tmp, CACHE_FILE);
}

// Claude Code names its Keychain entry after CLAUDE_CONFIG_DIR's literal value.
function keychainService() {
  const dir = process.env.CLAUDE_CONFIG_DIR;
  if (!dir) return 'Claude Code-credentials';
  return `Claude Code-credentials-${createHash('sha256').update(dir).digest('hex').slice(0, 8)}`;
}

function readAccessToken() {
  let raw = null;
  try {
    raw = execFileSync('/usr/bin/security', ['find-generic-password', '-s', keychainService(), '-w'], {
      encoding: 'utf8',
      timeout: 2000,
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
  } catch {
    try {
      raw = readFileSync(join(homedir(), '.claude', '.credentials.json'), 'utf8');
    } catch {
      return null;
    }
  }
  try {
    const parsed = JSON.parse(raw);
    const creds = parsed.claudeAiOauth ?? parsed;
    if (!creds.accessToken) return null;
    if (creds.expiresAt != null && creds.expiresAt <= Date.now()) return null;
    return creds.accessToken;
  } catch {
    return null;
  }
}

// Per-model weekly windows ("weekly_scoped" entries); Opus/Sonnet included if present.
function scopedBuckets(limits) {
  if (!Array.isArray(limits)) return [];
  const byName = new Map();
  for (const entry of limits) {
    if (entry?.kind !== 'weekly_scoped' || typeof entry.percent !== 'number') continue;
    const name = entry.scope?.model?.display_name?.trim();
    if (!name) continue;
    const key = name.toLowerCase();
    const prev = byName.get(key);
    if (!prev || (entry.is_active === true && !prev.isActive)) {
      byName.set(key, { label: key, percent: entry.percent, resetsAt: entry.resets_at ?? null, isActive: entry.is_active === true });
    }
  }
  return [...byName.values()];
}

// The endpoint throttles hard unless User-Agent carries a real Claude Code version.
async function refresh(version) {
  const cache = readCache();
  const token = readAccessToken();
  if (!token) {
    writeCache({ ...cache, nextAttemptAt: Date.now() + FAILURE_BACKOFF_MS });
    return;
  }
  const headers = {
    Authorization: `Bearer ${token}`,
    'anthropic-beta': 'oauth-2025-04-20',
    'Content-Type': 'application/json',
  };
  if (/^\d+\.\d+\.\d+[A-Za-z0-9.+-]*$/.test(version ?? '')) headers['User-Agent'] = `claude-code/${version}`;

  try {
    const res = await fetch('https://api.anthropic.com/api/oauth/usage', { headers, signal: AbortSignal.timeout(5000) });
    if (res.status === 429) {
      const retryAfter = Number(res.headers.get('retry-after'));
      const wait = Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter * 1000 : RATE_LIMITED_BACKOFF_MS;
      writeCache({ ...cache, nextAttemptAt: Date.now() + wait });
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const body = await res.json();
    writeCache({
      fetchedAt: Date.now(),
      nextAttemptAt: Date.now() + POLL_MS,
      fiveHour: body.five_hour ? { percent: body.five_hour.utilization, resetsAt: body.five_hour.resets_at } : null,
      sevenDay: body.seven_day ? { percent: body.seven_day.utilization, resetsAt: body.seven_day.resets_at } : null,
      scoped: scopedBuckets(body.limits),
    });
  } catch {
    writeCache({ ...cache, nextAttemptAt: Date.now() + FAILURE_BACKOFF_MS });
  }
}

function scheduleRefresh(cache, version) {
  if ((cache.nextAttemptAt ?? 0) > Date.now()) return;
  // Claim the slot first so concurrent redraws don't each spawn a fetch.
  try {
    writeCache({ ...cache, nextAttemptAt: Date.now() + 30_000 });
  } catch {
    return;
  }
  const self = fileURLToPath(import.meta.url);
  spawn(process.execPath, [self, '--refresh', version ?? ''], { detached: true, stdio: 'ignore' }).unref();
}

// --- rendering ---------------------------------------------------------------

function git(args, cwd) {
  try {
    return execFileSync('git', args, { cwd, encoding: 'utf8', timeout: 1000, stdio: ['ignore', 'pipe', 'ignore'] }).trim();
  } catch {
    return null;
  }
}

function renderCwd(cwd) {
  const home = homedir();
  if (cwd === home) return dim('~');
  return dim(cwd.startsWith(`${home}/`) ? `~${cwd.slice(home.length)}` : cwd);
}

function renderGit(cwd) {
  const status = git(['--no-optional-locks', 'status', '--porcelain', '-b'], cwd);
  if (status == null) return [];
  const branch = git(['branch', '--show-current'], cwd) || git(['rev-parse', '--short', 'HEAD'], cwd);
  const parts = branch ? [`${dim('branch:')}${paint(CYAN, branch)}`] : [];

  const [head, ...files] = status.split('\n');
  let staged = 0, modified = 0, untracked = 0;
  for (const line of files) {
    if (line.length < 2) continue;
    if (line[0] === '?') { untracked++; continue; }
    if (line[0] !== ' ') staged++;
    if (line[1] === 'M' || line[1] === 'D') modified++;
  }
  const ahead = Number(head.match(/\bahead (\d+)/)?.[1] ?? 0);
  const behind = Number(head.match(/\bbehind (\d+)/)?.[1] ?? 0);
  const counts = [
    staged && `${paint(GREEN, '+')}${staged}`,
    modified && `${paint(RED, '!')}${modified}`,
    untracked && `${paint(CYAN, '?')}${untracked}`,
    ahead && `${paint(GREEN, '⇡')}${ahead}`,
    behind && `${paint(RED, '⇣')}${behind}`,
  ].filter(Boolean);
  if (counts.length) parts.push(counts.join(' '));
  return parts;
}

const clampPct = (v) => Math.min(100, Math.max(0, Math.round(v)));

function bar(pct, width, color) {
  const filled = Math.round((pct / 100) * width);
  return `${color}${'#'.repeat(filled)}${DIM}${'-'.repeat(width - filled)}${RESET}`;
}

// resets_at arrives as epoch seconds or millis (stdin) or an ISO string (usage API).
function untilReset(resetsAt) {
  if (resetsAt == null || resetsAt === '') return null;
  const n = Number(resetsAt);
  const at = Number.isFinite(n) ? (Math.abs(n) < 1e12 ? n * 1000 : n) : Date.parse(resetsAt);
  const mins = Math.floor((at - Date.now()) / 60_000);
  if (!Number.isFinite(mins) || mins <= 0) return null;
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  return days > 0 ? `${days}d${hours % 24}h` : `${hours}h${mins % 60}m`;
}

// `fit` drops decoration for narrow terminals: bars first, then reset countdowns.
function renderLimit(label, percent, resetsAt, fit) {
  const pct = clampPct(percent);
  const color = pct >= 90 ? RED : pct >= 70 ? YELLOW : GREEN;
  const reset = untilReset(resetsAt);
  const gauge = fit.bars ? `[${bar(pct, 8, color)}]` : '';
  return `${label}:${gauge}${paint(color, `${pct}%`)}${reset && fit.resets ? dim(`(${reset})`) : ''}`;
}

function renderLimits(stdinLimits, cache, fit) {
  // stdin is refreshed on every API response; the cache only fills gaps.
  const fiveHour = stdinLimits?.five_hour
    ? { percent: stdinLimits.five_hour.used_percentage, resetsAt: stdinLimits.five_hour.resets_at }
    : cache.fiveHour;
  const sevenDay = stdinLimits?.seven_day
    ? { percent: stdinLimits.seven_day.used_percentage, resetsAt: stdinLimits.seven_day.resets_at }
    : cache.sevenDay;

  const parts = [];
  if (fiveHour?.percent != null) parts.push(renderLimit('5h', fiveHour.percent, fiveHour.resetsAt, fit));
  if (sevenDay?.percent != null) parts.push(renderLimit(dim('wk'), sevenDay.percent, sevenDay.resetsAt, fit));
  // A trailing * flags buckets the usage API hasn't confirmed in a while (token expired, endpoint changed).
  const stale = Date.now() - (cache.fetchedAt ?? 0) > 5 * POLL_MS ? dim('*') : '';
  for (const b of cache.scoped ?? []) parts.push(renderLimit(dim(b.label), b.percent, b.resetsAt, fit) + stale);
  return parts.length ? parts.join(' ') : null;
}

function renderContext(percent, fit) {
  const pct = clampPct(percent);
  const [color, suffix] = pct >= 85 ? [RED, ' CRITICAL'] : pct >= 80 ? [YELLOW, ' COMPRESS?'] : pct >= 70 ? [YELLOW, ''] : [GREEN, ''];
  const gauge = fit.bars ? `[${bar(pct, 10, color)}]` : '';
  return `ctx:${gauge}${paint(color, `${pct}%${suffix}`)}`;
}

// Skills loaded since the last human prompt, in order. Both routes leave a
// "Base directory for this skill: <dir>" meta message (a slash command typed by
// the user, or the model's Skill tool), so that one marker covers both. The list
// resets when the next prompt arrives instead of sticking to the last skill ever used.
const SKILL_MARKER = 'Base directory for this skill: ';
const TAIL_BYTES = 2 * 1024 * 1024;

function readTail(path) {
  let fd;
  try {
    fd = openSync(path, 'r');
    const size = fstatSync(fd).size;
    const len = Math.min(size, TAIL_BYTES);
    const buf = Buffer.alloc(len);
    readSync(fd, buf, 0, len, size - len);
    const text = buf.toString('utf8');
    // Drop the first, probably partial, line when the read didn't start at 0.
    return len < size ? text.slice(text.indexOf('\n') + 1) : text;
  } catch {
    return '';
  } finally {
    if (fd != null) closeSync(fd);
  }
}

function currentTurnSkills(transcriptPath) {
  if (!transcriptPath) return [];
  const lines = readTail(transcriptPath).split('\n');
  const skills = [];
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i];
    if (!line) continue;
    const isPrompt = line.includes('"kind":"human"');
    if (!isPrompt && !line.includes(SKILL_MARKER)) continue;
    let rec;
    try {
      rec = JSON.parse(line);
    } catch {
      continue;
    }
    if (rec.type !== 'user') continue;
    if (rec.isMeta) {
      const content = rec.message?.content;
      const text = typeof content === 'string' ? content : content?.[0]?.text ?? '';
      if (text.startsWith(SKILL_MARKER)) {
        const name = text.slice(SKILL_MARKER.length).split('\n')[0].trim().split('/').pop();
        if (name && !skills.includes(name)) skills.unshift(name);
      }
    } else if (rec.origin?.kind === 'human') {
      break;
    }
  }
  return skills;
}

// --- width handling ----------------------------------------------------------
// Claude Code captures stdout, so the terminal width only arrives as $COLUMNS.
// Without it (a manual run) nothing is trimmed.

const ANSI = /\x1b\[[0-9;]*m/g;
const visibleWidth = (s) => [...s.replace(ANSI, '')].length;

// Cuts to `max` visible characters, ending in … and keeping color codes intact.
function truncate(s, max) {
  if (visibleWidth(s) <= max) return s;
  if (max <= 0) return '';
  let out = '';
  let seen = 0;
  for (const part of s.split(/(\x1b\[[0-9;]*m)/)) {
    if (part.startsWith('\x1b[')) {
      out += part;
      continue;
    }
    for (const ch of part) {
      if (seen === max - 1) return `${out}…${RESET}`;
      out += ch;
      seen++;
    }
  }
  return out;
}

const SKILL_MIN_NAME = 6;

// Fits as many skill names as `budget` allows, the rest folded into "+N";
// a lone name that still doesn't fit is cut with ….
function renderSkills(skills, budget) {
  if (!skills.length) return null;
  const label = (shown, rest) => `skill:${shown.join(',')}${rest ? ` +${rest}` : ''}`;
  for (let n = skills.length; n >= 1; n--) {
    const text = label(skills.slice(0, n), skills.length - n);
    if (text.length <= budget) return paint(CYAN, text);
  }
  const suffix = skills.length > 1 ? ` +${skills.length - 1}` : '';
  const room = budget - 'skill:'.length - suffix.length;
  // Too tight for a readable name: just say how many are loaded, or nothing at all.
  if (room < SKILL_MIN_NAME) {
    const count = `skill(${skills.length})`;
    return count.length <= budget ? paint(CYAN, count) : null;
  }
  return paint(CYAN, `skill:${[...skills[0]].slice(0, room - 1).join('')}…${suffix}`);
}

function renderSession(durationMs, ctxPct) {
  const mins = Math.floor((durationMs ?? 0) / 60_000);
  const color = mins > 120 || ctxPct > 85 ? RED : mins > 60 || ctxPct > 70 ? YELLOW : GREEN;
  return `session:${paint(color, `${mins}m`)}`;
}

async function main() {
  if (process.argv[2] === '--refresh') return refresh(process.argv[3]);

  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const data = JSON.parse(input || '{}');

  const cache = readCache();
  scheduleRefresh(cache, data.version);

  const cwd = data.workspace?.current_dir || data.cwd || process.cwd();
  const ctxPct = data.context_window?.used_percentage ?? 0;
  const model = data.model?.display_name || data.model?.id;

  const cols = Number(process.env.COLUMNS) > 0 ? Number(process.env.COLUMNS) : Infinity;

  // Skills ride on the short top line; the bottom one is already ~125 columns.
  const top = [renderCwd(cwd), ...renderGit(cwd)];
  const skillBudget = cols - visibleWidth(top.join(SEP)) - visibleWidth(SEP);
  const skills = renderSkills(currentTurnSkills(data.transcript_path), skillBudget);
  if (skills) top.push(skills);

  // The bottom line sheds decoration until it fits, so ctx and session (at its
  // end) survive a narrow terminal instead of being the first thing cut.
  const fits = [
    { bars: true, resets: true, modelLabel: true },
    { bars: false, resets: true, modelLabel: true },
    { bars: false, resets: false, modelLabel: true },
    { bars: false, resets: false, modelLabel: false },
  ];
  let bottom;
  for (const fit of fits) {
    bottom = [
      model && paint(CYAN, fit.modelLabel ? `Model: ${model}` : model),
      renderLimits(data.rate_limits, cache, fit),
      renderContext(ctxPct, fit),
      renderSession(data.cost?.total_duration_ms, ctxPct),
    ].filter(Boolean).join(SEP);
    if (visibleWidth(bottom) <= cols) break;
  }

  // Last resort: never let a line wrap, since that pushes the prompt down a row.
  const lines = [top.join(SEP), bottom].map((line) => truncate(line, cols));
  process.stdout.write(`${lines.join('\n')}\n`);
}

main().catch(() => process.stdout.write('statusline error\n'));
