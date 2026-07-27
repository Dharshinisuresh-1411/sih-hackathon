// Sidebar toggle for mobile
document.getElementById('sidebarToggle')?.addEventListener('click', () => {
  document.getElementById('sidebar').classList.toggle('show');
});

// Central fetch wrapper: handles network / DB-unavailable errors gracefully (FAILURE CASE 3)
async function apiFetch(url, options = {}) {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    let body = null;
    try { body = await res.json(); } catch (e) { /* no body */ }
    if (!res.ok) {
      const message = (body && body.error) || 'Something went wrong. Please try again.';
      return { ok: false, status: res.status, data: body, error: message };
    }
    return { ok: true, status: res.status, data: body };
  } catch (err) {
    return {
      ok: false, status: 0, data: null,
      error: 'Unable to process your request because the database is temporarily unavailable. Please try again.',
    };
  }
}

function showAlert(message, type = 'danger') {
  const area = document.getElementById('alertArea');
  if (!area) { alert(message); return; }
  const el = document.createElement('div');
  el.className = `alert alert-${type} alert-dismissible fade show`;
  el.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
  area.prepend(el);
  setTimeout(() => el.remove(), 6000);
}

function statusBadge(status) {
  return `<span class="badge badge-status-${status}">${status.replace('_', ' ')}</span>`;
}

function formatDate(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
