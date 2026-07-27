async function loadKpis() {
  const { ok, data, error } = await apiFetch('/api/reports/summary');
  if (!ok) return showAlert(error);

  const kpis = [
    { label: 'Total Poles', value: data.total_poles, icon: 'fa-tower-observation' },
    { label: 'Total Complaints', value: data.total_complaints, icon: 'fa-clipboard-list' },
    { label: 'Open', value: data.open_complaints, icon: 'fa-triangle-exclamation' },
    { label: 'Assigned', value: data.assigned_complaints, icon: 'fa-user-clock' },
    { label: 'In Progress', value: data.in_progress_complaints, icon: 'fa-screwdriver-wrench' },
    { label: 'Closed', value: data.closed_complaints, icon: 'fa-circle-check' },
    { label: 'Active Electricians', value: data.active_electricians, icon: 'fa-helmet-safety' },
    { label: 'Repeat-Offender Poles', value: data.repeat_offender_poles, icon: 'fa-rotate' },
  ];

  document.getElementById('kpiRow').innerHTML = kpis.map(k => `
    <div class="col-6 col-md-3">
      <div class="card kpi-card p-3 d-flex flex-row justify-content-between align-items-center">
        <div>
          <div class="kpi-value">${k.value}</div>
          <div class="kpi-label">${k.label}</div>
        </div>
        <i class="fa-solid ${k.icon} kpi-icon"></i>
      </div>
    </div>
  `).join('');

  document.getElementById('rankingPeriod').textContent = `Last ${data.repeat_offender_period_months} months`;
}

async function loadWardChart() {
  const { ok, data, error } = await apiFetch('/api/reports/open-by-ward');
  if (!ok) return showAlert(error);
  new Chart(document.getElementById('wardChart'), {
    type: 'bar',
    data: {
      labels: data.map(d => d.ward),
      datasets: [{ label: 'Open Complaints', data: data.map(d => d.open_complaints), backgroundColor: '#0d5c46' }],
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
  });
}

async function loadStatusChart() {
  const { ok, data, error } = await apiFetch('/api/reports/status-distribution');
  if (!ok) return showAlert(error);
  const order = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'CLOSED'];
  new Chart(document.getElementById('statusChart'), {
    type: 'doughnut',
    data: {
      labels: order,
      datasets: [{ data: order.map(s => data[s] || 0), backgroundColor: ['#dc2626', '#d97706', '#2563eb', '#16a34a'] }],
    },
    options: { responsive: true },
  });
}

async function loadRanking() {
  const { ok, data, error } = await apiFetch('/api/reports/repeat-offenders');
  if (!ok) return showAlert(error);
  const top = data.poles.slice(0, 10);
  document.getElementById('rankingBody').innerHTML = top.map(p => `
    <tr class="${p.high_frequency ? 'high-freq' : ''}">
      <td>${p.rank}</td>
      <td>${p.pole_number}</td>
      <td>${p.ward}</td>
      <td>${p.location}</td>
      <td><strong>${p.total_complaints}</strong>${p.high_frequency ? ' <i class="fa-solid fa-fire text-danger" title="High frequency"></i>' : ''}</td>
      <td>${formatDate(p.last_complaint_date)}</td>
      <td>${p.pole_status}</td>
    </tr>
  `).join('') || '<tr><td colspan="7" class="text-center text-muted p-3">No data yet</td></tr>';
}

loadKpis();
loadWardChart();
loadStatusChart();
loadRanking();
