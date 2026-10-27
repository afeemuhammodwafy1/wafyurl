document.addEventListener('DOMContentLoaded', async function () {
  const root = document.querySelector('[data-stats-code]');
  if (!root) return;

  const code = root.getAttribute('data-stats-code');
  const recentClicks = document.getElementById('recentClicks');
  const deviceBreakdown = document.getElementById('deviceBreakdown');
  const browserBreakdown = document.getElementById('browserBreakdown');
  const referrerBreakdown = document.getElementById('referrerBreakdown');
  const chartCanvas = document.getElementById('clickChart');
  const chartEmpty = document.getElementById('chartEmpty');

  function renderBreakdown(target, values, emptyMessage) {
    target.replaceChildren();
    const entries = Object.entries(values || {}).filter((entry) => Number(entry[1]) > 0).sort((a, b) => b[1] - a[1]);
    if (!entries.length) {
      const empty = document.createElement('p');
      empty.className = 'empty-note';
      empty.textContent = emptyMessage;
      target.append(empty);
      return;
    }
    const max = Math.max(1, ...entries.map((entry) => Number(entry[1]) || 0));
    entries.forEach(([label, value]) => {
      const row = document.createElement('div');
      row.className = 'breakdown-item';
      const top = document.createElement('div');
      top.className = 'breakdown-topline';
      const name = document.createElement('span');
      name.textContent = label;
      const count = document.createElement('strong');
      count.textContent = String(value);
      top.append(name, count);
      const track = document.createElement('div');
      track.className = 'breakdown-track';
      const fill = document.createElement('span');
      fill.style.width = `${Math.max(2, ((Number(value) || 0) / max) * 100)}%`;
      track.append(fill);
      row.append(top, track);
      target.append(row);
    });
  }

  try {
    const response = await fetch(`/api/stats/${encodeURIComponent(code)}`, { headers: { Accept: 'application/json' } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Could not load analytics');

    recentClicks.textContent = Number(data.recent_clicks || 0).toLocaleString();
    const daily = Array.isArray(data.daily_data) ? data.daily_data : [];
    const clickTotal = daily.reduce((sum, point) => sum + Number(point.clicks || 0), 0);
    if (!clickTotal) chartEmpty.classList.remove('hidden');
    if (window.Chart && chartCanvas) {
      new Chart(chartCanvas, {
        type: 'line',
        data: {
          labels: daily.map((point) => new Date(`${point.date}T00:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })),
          datasets: [{
            label: 'Clicks',
            data: daily.map((point) => Number(point.clicks || 0)),
            borderColor: '#4f46e5',
            backgroundColor: 'rgba(79, 70, 229, 0.09)',
            fill: true,
            tension: 0.34,
            pointRadius: 2,
            pointHoverRadius: 4,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { intersect: false, mode: 'index' },
          plugins: { legend: { display: false }, tooltip: { displayColors: false } },
          scales: {
            x: { grid: { display: false }, ticks: { maxTicksLimit: 7, color: '#8793a8', font: { size: 10 } }, border: { display: false } },
            y: { beginAtZero: true, ticks: { precision: 0, color: '#8793a8', font: { size: 10 } }, grid: { color: '#edf0f6' }, border: { display: false } }
          }
        }
      });
    } else {
      chartEmpty.textContent = 'Chart library could not load. Refresh to try again.';
      chartEmpty.classList.remove('hidden');
    }
    renderBreakdown(deviceBreakdown, data.devices, 'No device data recorded yet.');
    renderBreakdown(browserBreakdown, data.browsers, 'No browser data recorded yet.');
    renderBreakdown(referrerBreakdown, Object.fromEntries(data.top_referrers || []), 'No external referrers recorded yet.');
  } catch (error) {
    [deviceBreakdown, browserBreakdown, referrerBreakdown].forEach((target) => {
      target.replaceChildren();
      const message = document.createElement('p');
      message.className = 'empty-note';
      message.textContent = 'Analytics could not be loaded. Please refresh and try again.';
      target.append(message);
    });
    chartEmpty.textContent = error.message || 'Analytics could not be loaded.';
    chartEmpty.classList.remove('hidden');
  }
});
