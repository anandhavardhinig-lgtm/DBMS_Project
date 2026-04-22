/**
 * script.js — Shared utilities for Hostel Mess Feedback Portal
 * Includes: API helper, auth guard, toast notifications, HTML escaping
 */

const API_BASE = 'http://localhost:5000';

// ═══════════════════════════════════════════════════════════════
//  API HELPER
// ═══════════════════════════════════════════════════════════════
/**
 * Wrapper around fetch that prepends API_BASE and sets JSON headers.
 * Usage: const res = await apiFetch('/menu');
 */
async function apiFetch(endpoint, options = {}) {
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  };

  // Merge headers
  const config = {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) },
  };

  return fetch(API_BASE + endpoint, config);
}


// ═══════════════════════════════════════════════════════════════
//  AUTH GUARD & LOGOUT
// ═══════════════════════════════════════════════════════════════
/**
 * Call at top of each protected page.
 * Redirects to login.html if the stored role doesn't match expectedRole.
 */
function requireAuth(expectedRole) {
  const role = sessionStorage.getItem('role');
  if (role !== expectedRole) {
    location.href = 'login.html';
  }
}

/** Sign out: clear session and go to login page. */
function logout() {
  sessionStorage.clear();
  location.href = 'login.html';
}


// ═══════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════
const TOAST_ICONS = {
  success: '✓',
  error:   '✕',
  warning: '⚠',
  info:    'ℹ',
};

/**
 * Show a toast notification.
 * @param {string} message  - Message to display
 * @param {'success'|'error'|'warning'|'info'} type - Toast type (default: 'info')
 * @param {number} duration - Duration in ms before auto-dismiss (default: 3500)
 */
function showToast(message, type = 'info', duration = 3500) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span class="toast-icon">${TOAST_ICONS[type] || 'ℹ'}</span>
    <span class="toast-msg">${escHtml(message)}</span>
    <button class="toast-close" onclick="this.closest('.toast').remove()">×</button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}


// ═══════════════════════════════════════════════════════════════
//  HTML ESCAPE (XSS prevention)
// ═══════════════════════════════════════════════════════════════
/**
 * Escape a string for safe insertion as HTML text content.
 */
function escHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}


// ═══════════════════════════════════════════════════════════════
//  DATE HELPER
// ═══════════════════════════════════════════════════════════════
/**
 * Format a Date (or today) as YYYY-MM-DD (used for API params if needed).
 */
function formatDate(date = new Date()) {
  return date.toISOString().split('T')[0];
}
