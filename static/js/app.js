const api = async (path, opts = {}) => {
  const res = await fetch('/api' + path, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw err
  }
  const text = await res.text()
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

// Toast helper
function showToast(msg, type = 'info', timeout = 3500) {
  const container = document.getElementById('toast-container') || (() => {
    const d = document.createElement('div'); d.id = 'toast-container'; d.style.position = 'fixed'; d.style.right='18px'; d.style.bottom='18px'; d.style.zIndex='9999'; document.body.appendChild(d); return d;
  })()
  const t = document.createElement('div')
  t.className = `toast ${type}`
  t.textContent = msg
  container.appendChild(t)
  setTimeout(() => t.remove(), timeout)
}

// Simple i18n map (English + Kannada for key UI strings)
const I18N = {
  en: {
    Dashboard: 'Dashboard',
    'My Profile': 'My Profile',
    'All Members': 'All Members',
    'Sign Out': 'Sign Out',
    'Login failed': 'Login failed. Check your name/PIN.',
    'Enter a name': 'Enter a name',
    'Share requested': 'Share payment requested for approval',
    'Submitted for approval': 'Submitted for approval',
    'Loan applied': 'Loan applied and payment requested for approval',
    'Only admin': 'Only admin can approve loans.',
    'Enter loan amount': 'Enter loan amount',
    'Enter amount': 'Enter amount',
    'Photo uploaded': 'Photo uploaded',
    'Upload failed': 'Upload failed',
    Cancel: 'Cancel',
    'Confirm cancel?': 'Confirm cancel?'
  },
  kn: {
    Dashboard: 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
    'My Profile': 'ನನ್ನ ಪ್ರೊಫೈಲ್',
    'All Members': 'ಎಲ್ಲಾ ಸದಸ್ಯರು',
    'Sign Out': 'ಸೈನ್ ಔಟ್',
    'Login failed': 'ಲಾಗಿನ್ ವಿಫಲವಾಯಿತು. ಹೆಸರು/PIN ಪರಿಶೀಲಿಸಿ.',
    'Enter a name': 'ಹೆಸರನ್ನು ನಮೂದಿಸಿ',
    'Share requested': 'ಶೇರು ಪಾವತಿ ಅನುಮೋದನೆಗೆ ವಿನಂತಿಸಲಾಗಿದೆ',
    'Submitted for approval': 'ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ',
    'Loan applied': 'ಸಾಲವನ್ನು ಅನ್ವಯಿಸಲಾಗಿದೆ ಮತ್ತು ಪಾವತಿ ವಿನಂತಿಸಲಾಗಿದೆ',
    'Only admin': 'ಮಾತ್ರ ಆಡಳಿತಗಾರರು ಅನುಮೋದಿಸಬಹುದು.',
    'Enter loan amount': 'ಸಾಲದ ಮೊತ್ತವನ್ನು ನಮೂದಿಸಿ',
    'Enter amount': 'ಮೊತ್ತವನ್ನು ನಮೂದಿಸಿ',
    'Photo uploaded': 'ಫೋಟೋ ಅಪ್ಲೋಡ್ ಆಗಿದೆ',
    'Upload failed': 'ಅಪ್‌ಲೋಡ್ ವಿಫಲವಾಗಿದೆ',
    Cancel: 'ರದ್ದುಮಾಡಿ',
    'Confirm cancel?': 'ರದ್ದುಗೊಳಿಸುವುದನ್ನು ಖಚಿತಪಡಿಸಿಕೊಳ್ಳಿ?'
  }
}

const state = {
  members: [],
  currentUser: null,
  activeView: 'home',
  selectedMember: null,
}

state.lang = state.lang || 'en'
function t(key) { return (I18N[state.lang] && I18N[state.lang][key]) || key }

// Language toggle
document.addEventListener('click', (e) => {
  if (e.target && e.target.id === 'lang-toggle') {
    state.lang = state.lang === 'en' ? 'kn' : 'en'
    e.target.textContent = state.lang === 'en' ? 'KN' : 'EN'
    renderMenu()
    renderView()
  }
})

async function renderAdminLogs() {
  const div = document.getElementById('admin-logs')
  if (!div) return
  div.innerHTML = '<p>Loading logs...</p>'
  try {
    const res = await fetch('/api/logs', {headers: {'X-ADMIN-PIN': ADMIN_PIN}})
    if (!res.ok) {
      const e = await res.json().catch(()=>({error:'failed'}))
      div.innerHTML = `<p style="color:#fca5a5">${e.error||'failed to load logs'}</p>`
      return
    }
    const j = await res.json()
    const pre = document.createElement('pre')
    pre.style.maxHeight = '240px'
    pre.style.overflow = 'auto'
    pre.textContent = j.lines ? j.lines.join('') : JSON.stringify(j)
    div.innerHTML = ''
    div.appendChild(pre)
  } catch (err) {
    div.innerHTML = `<p style="color:#fca5a5">${err.message || err}</p>`
  }
}

let loginScreen = null
let mainScreen = null
let menuLinks = null
let content = null
let memberSelect = null
let adminPin = null
let loginButton = null
let loginError = null

function showScreen(screenId) {
  loginScreen.classList.add('hidden')
  mainScreen.classList.add('hidden')
  if (screenId === 'login') {
    loginScreen.classList.remove('hidden')
  } else {
    mainScreen.classList.remove('hidden')
  }
}

function formatCurrency(amount) {
  return '₹' + Number(amount || 0).toLocaleString('en-IN', {maximumFractionDigits: 2})
}

function toIndianNumber(str) {
  let num = str.replace(/[^0-9.]/g, '')
  let parts = num.split('.')
  let intPart = parts[0]
  if (!intPart) return ''
  let lastThree = intPart.slice(-3)
  let rest = intPart.slice(0, -3)
  if (rest) rest = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',')
  let formatted = rest ? rest + ',' + lastThree : lastThree
  if (parts.length > 1) formatted += '.' + parts.slice(1).join('')
  return formatted
}

function indianizeInput(input) {
  input.addEventListener('input', function () {
    let start = this.selectionStart
    let raw = this.value.replace(/,/g, '')
    let formatted = toIndianNumber(raw)
    let added = formatted.length - this.value.length
    this.value = formatted
    this.setSelectionRange(start + added, start + added)
  })
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'})
}

function formatDateTime(d) {
  if (!d) return '-'
  const dt = new Date(d)
  return dt.toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'})
    + ' ' + dt.toLocaleTimeString('en-IN', {hour: '2-digit', minute: '2-digit'})
}

function calculateAge(dob) {
  if (!dob) return '-'
  const birth = new Date(dob)
  const diff = Date.now() - birth.getTime()
  return Math.max(0, Math.floor(diff / 31557600000))
}

function initials(name) {
  return name.split(' ').map(w => w[0] || '').join('').slice(0, 2).toUpperCase()
}

function monthsBetweenInclusive(start) {
  if (!start) return 0
  const s = new Date(start)
  const now = new Date()
  return (now.getFullYear() - s.getFullYear()) * 12 + (now.getMonth() - s.getMonth()) + 1
}

function renderMenu() {
  menuLinks.innerHTML = ''
  const items = [
    {id: 'home', label: t('Dashboard')},
    {id: 'my-profile', label: t('My Profile')},
    {id: 'my-history', label: '📜 All History'},
    {id: 'all-members', label: t('All Members')},
  ]
  if (state.currentUser.is_admin) {
    items.splice(3, 0, {id: 'admin-panel', label: 'Admin Panel'})
  }
  items.push({id: 'sign-out', label: t('Sign Out')})
  items.forEach(item => {
    const a = document.createElement('a')
    a.href = '#'
    a.className = 'nav-link' + (state.activeView === item.id ? ' active' : '')
    a.textContent = item.label
    a.onclick = (e) => {
      e.preventDefault()
      if (item.id === 'sign-out') {
        logout()
      } else {
        state.activeView = item.id
        renderView()
      }
    }
    menuLinks.appendChild(a)
  })
}

async function loadMembers() {
  state.members = await api('/members')
  memberSelect.innerHTML = state.members.map(m => `<option value="${m.name}">${m.name}${m.is_admin ? ' (Admin)' : ''}</option>`).join('')
}

async function init() {
  await loadMembers()
  showScreen('login')
}

async function handleLogin() {
  try {
    loginError.classList.add('hidden')
    const name = memberSelect.value
    const pin = adminPin.value.trim()
    const user = await api('/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, pin}),
    })
    state.currentUser = user
    state.activeView = 'home'
    renderMenu()
    renderView()
    showScreen('main')
  } catch (err) {
    loginError.textContent = err.error || 'Login failed. Check your name/PIN.'
    loginError.classList.remove('hidden')
  }
}

function logout() {
  state.currentUser = null
  adminPin.value = ''
  state.activeView = 'home'
  showScreen('login')
}

function renderView() {
  renderMenu()
  const view = state.activeView
  if (view === 'admin-panel') return renderAdminPanel()
  if (view === 'my-profile') return renderMemberProfile(state.currentUser.id)
  if (view === 'my-history') return renderAllHistory()
  if (view === 'all-members') return renderAllMembers()
  return renderHome()
}

async function renderHome() {
  const stats = await api('/admin/stats', {headers: {'X-ADMIN-PIN': ADMIN_PIN}}).catch(()=>null)
  const html = `
    <div class="panel welcome-panel">
      <h2 class="page-title">Welcome, ${state.currentUser.name}</h2>
    </div>

    <div class="group-info">
      <h3 class="section-heading">📋 Group Information</h3>
      <div class="group-info-grid">
        <div class="gi-card gi-started">
          <div class="gi-icon">🚀</div>
          <div class="gi-value">${stats?stats.group_start_date:'-'}</div>
          <div class="gi-label">Started</div>
        </div>
        <div class="gi-card gi-members">
          <div class="gi-icon">👥</div>
          <div class="gi-value">${stats?stats.member_count:'-'}</div>
          <div class="gi-label">Members</div>
        </div>
        <div class="gi-card gi-share">
          <div class="gi-icon">📊</div>
          <div class="gi-value">${stats?formatCurrency(stats.share_amount):'-'}</div>
          <div class="gi-label">Share / Month</div>
        </div>
        <div class="gi-card gi-onetime">
          <div class="gi-icon">💰</div>
          <div class="gi-value">${stats?formatCurrency(stats.one_time_amount):'-'}</div>
          <div class="gi-label">One-time Deposit</div>
        </div>
        <div class="gi-card gi-period">
          <div class="gi-icon">📅</div>
          <div class="gi-value">${stats?stats.total_period_months/12+' Years':'-'}</div>
          <div class="gi-label">Total Period</div>
        </div>
        <div class="gi-card gi-interest">
          <div class="gi-icon">📈</div>
          <div class="gi-value">${stats?stats.loan_interest_rate+'% / month':'-'}</div>
          <div class="gi-label">Loan Interest</div>
        </div>
      </div>
    </div>

    <div class="panel">
      <h3 class="section-heading">💰 Financial Overview</h3>
      <div class="stats-grid" style="margin-top:12px">
        <div class="stat-card loan-given"><strong>${stats?formatCurrency(stats.total_lent):'-'}</strong><span>Loan Given</span></div>
        <div class="stat-card hardlocked"><strong>${stats?formatCurrency(stats.cash_on_hand):'-'}</strong><span>Hardlocked / FD</span></div>
        <div class="stat-card available"><strong>${stats?formatCurrency(stats.available_to_lend):'-'}</strong><span>Available to Loan</span></div>
      </div>

      <div class="total-box">
        <div class="total-box-main">
          <div class="total-box-label">Total Collected</div>
          <div class="total-box-amount">${stats?formatCurrency(stats.total_collected):'-'}</div>
          <div class="total-box-desc">Sum of all collection sources below.</div>
        </div>
        <div class="total-box-breakdown">
          <div class="breakdown-item"><span class="breakdown-dot deposits-dot"></span><strong>Initial Deposits:</strong> ${stats?formatCurrency(stats.deposits_total):'-'}</div>
          <div class="breakdown-item"><span class="breakdown-dot shares-dot"></span><strong>Shares:</strong> ${stats?formatCurrency(stats.shares_total):'-'}</div>
          <div class="breakdown-item"><span class="breakdown-dot interest-dot"></span><strong>Loan Interest:</strong> ${stats?formatCurrency(stats.loan_interest_received):'-'}</div>
          <div class="breakdown-item"><span class="breakdown-dot other-dot"></span><strong>Other Income:</strong> ${stats?formatCurrency(stats.others_total):'-'}</div>
        </div>
      </div>
    </div>
  `
  content.innerHTML = html
}

function setView(view) {
  state.activeView = view
  renderView()
}

async function renderAdminPanel() {
  const pendingLoans = state.members
    .flatMap(member => member.id ? [member] : [])
  const html = `
    <div class="panel">
      <h2 class="page-title">Admin Panel</h2>
      <div class="grid-2">
        <div class="panel">
          <h3>Add New Member</h3>
          <div class="input-row"><input id="new-member-name" placeholder="Member name" /></div>
          <div class="input-row"><input id="new-member-phone" placeholder="Phone (optional)" /></div>
          <div class="input-row"><input id="new-member-dob" type="date" placeholder="Date of birth" /></div>
          <div class="input-row"><input id="new-member-address" placeholder="Address (optional)" /></div>
          <div class="input-row"><input id="new-member-photo" placeholder="Photo URL (optional)" /></div>
          <button class="btn primary" id="add-member-btn">Add Member</button>
        </div>
        <div class="panel">
          <h3>Pending Loans</h3>
          <p>Approve loans from members after review.</p>
          <div id="pending-loans"></div>
          <h3 style="margin-top:18px">Pending Payments</h3>
          <div id="pending-payments"></div>
        </div>
      </div>
    </div>
  `
  content.innerHTML = html
  document.getElementById('add-member-btn').onclick = handleAddMember
  await renderPendingLoans()
  await renderPendingPayments()
}


async function renderPendingPayments() {
  const div = document.getElementById('pending-payments')
  div.innerHTML = '<p style="color:#94a3b8">Loading...</p>'
  try {
    const items = await api('/admin/payment_requests', {headers: {'X-ADMIN-PIN': ADMIN_PIN}})
    if (!items || items.length === 0) {
      div.innerHTML = '<p>No pending payments</p>'
      return
    }
    const list = document.createElement('div')
    list.className = 'list-card'
    items.forEach((it, idx) => {
      const row = document.createElement('div')
      row.className = 'list-item'
      row.style.flexWrap = 'wrap'
      row.innerHTML = `
        <div>
          <strong>${it.member_name}</strong><br>
          <small>${it.type} ₹${it.amount} — ${it.note || ''}</small>
        </div>
        <div>${it.screenshot?`<a href="${it.screenshot}" target="_blank" style="color:#7dd3fc">📎 Screenshot</a>`:''}</div>
        <div id="pay-actions-${idx}">
          <button class="btn primary approve-btn" style="padding:6px 12px;font-size:0.85rem">Approve</button>
          <button class="btn secondary reject-btn" style="padding:6px 12px;font-size:0.85rem">Reject</button>
        </div>
        <div id="pay-reject-form-${idx}" class="reject-form hidden">
          <textarea id="pay-reason-${idx}" placeholder="Reason for rejection..." rows="2"></textarea>
          <div class="reject-form-actions">
            <button class="btn primary" id="pay-reject-confirm-${idx}" style="padding:6px 14px;font-size:0.85rem;background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">Confirm Reject</button>
            <button class="btn secondary" id="pay-reject-cancel-${idx}" style="padding:6px 14px;font-size:0.85rem">Cancel</button>
          </div>
        </div>`
      row.querySelector('.approve-btn').onclick = async () => {
        const res = await fetch(`/api/admin/approve_request/${it.id}`, {method:'POST', headers: {'X-ADMIN-PIN': ADMIN_PIN}})
        if (!res.ok) { showToast('Approve failed', 'error'); return }
        showToast('Payment approved', 'success')
        await renderPendingPayments()
      }
      row.querySelector('.reject-btn').onclick = () => {
        document.getElementById('pay-actions-' + idx).classList.add('hidden')
        document.getElementById('pay-reject-form-' + idx).classList.remove('hidden')
      }
      row.querySelector('#pay-reject-cancel-' + idx).onclick = () => {
        document.getElementById('pay-actions-' + idx).classList.remove('hidden')
        document.getElementById('pay-reject-form-' + idx).classList.add('hidden')
      }
      row.querySelector('#pay-reject-confirm-' + idx).onclick = async () => {
        const reason = document.getElementById('pay-reason-' + idx).value.trim()
        if (!reason) { showToast('Enter a reason', 'error'); return }
        const res = await fetch(`/api/admin/reject_request/${it.id}`, {method:'POST', headers: {'Content-Type':'application/json','X-ADMIN-PIN': ADMIN_PIN}, body: JSON.stringify({reason})})
        if (!res.ok) { showToast('Reject failed', 'error'); return }
        showToast('Payment rejected', 'info')
        await renderPendingPayments()
      }
      list.appendChild(row)
    })
    div.appendChild(list)
  } catch (e) {
    div.innerHTML = `<p>Error loading: ${e.error || e}</p>`
  }
}

async function renderPendingLoans() {
  const pendingDiv = document.getElementById('pending-loans')
  pendingDiv.innerHTML = '<p style="color:#94a3b8">Loading...</p>'
  let loans = []
  try {
    loans = await api('/admin/pending_loans', {headers: {'X-ADMIN-PIN': ADMIN_PIN}})
  } catch (e) {
    pendingDiv.innerHTML = '<p>Error loading pending loans</p>'
    return
  }
  if (!loans || loans.length === 0) {
    pendingDiv.innerHTML = '<p>No pending loans at the moment.</p>'
    return
  }
  const list = document.createElement('div')
  list.className = 'list-card'
  loans.forEach((item, idx) => {
    const row = document.createElement('div')
    row.className = 'list-item'
    row.style.flexWrap = 'wrap'
    row.id = 'loan-row-' + idx
    row.innerHTML = `
      <div>
        <strong>${item.member_name}</strong><br>
        <small>Loan ₹${item.principal} for ${item.term_months} mo</small>
      </div>
      <div id="loan-actions-${idx}">
        <button class="btn primary approve-btn" style="padding:6px 12px;font-size:0.85rem">Approve</button>
        <button class="btn secondary reject-btn" style="padding:6px 12px;font-size:0.85rem">Reject</button>
      </div>
      <div id="loan-reject-form-${idx}" class="reject-form hidden">
        <textarea id="reject-reason-${idx}" placeholder="Reason for rejection..." rows="2"></textarea>
        <div class="reject-form-actions">
          <button class="btn primary" id="reject-confirm-${idx}" style="padding:6px 14px;font-size:0.85rem;background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">Confirm Reject</button>
          <button class="btn secondary" id="reject-cancel-${idx}" style="padding:6px 14px;font-size:0.85rem">Cancel</button>
        </div>
      </div>`
    row.querySelector('.approve-btn').onclick = async () => {
      const res = await fetch(`/api/admin/approve_loan/${item.id}`, {method:'POST', headers: {'X-ADMIN-PIN': ADMIN_PIN}})
      if (!res.ok) { showToast('Approve failed', 'error'); return }
      showToast(`${item.member_name}'s loan approved`, 'success')
      await renderPendingLoans()
    }
    row.querySelector('.reject-btn').onclick = () => {
      document.getElementById('loan-actions-' + idx).classList.add('hidden')
      document.getElementById('loan-reject-form-' + idx).classList.remove('hidden')
    }
    row.querySelector('#reject-cancel-' + idx).onclick = () => {
      document.getElementById('loan-actions-' + idx).classList.remove('hidden')
      document.getElementById('loan-reject-form-' + idx).classList.add('hidden')
    }
    row.querySelector('#reject-confirm-' + idx).onclick = async () => {
      const reason = document.getElementById('reject-reason-' + idx).value.trim()
      if (!reason) { showToast('Enter a reason', 'error'); return }
      const res = await fetch(`/api/admin/reject_loan/${item.id}`, {method:'POST', headers: {'Content-Type':'application/json','X-ADMIN-PIN': ADMIN_PIN}, body: JSON.stringify({reason})})
      if (!res.ok) { showToast('Reject failed', 'error'); return }
      showToast(`${item.member_name}'s loan rejected`, 'info')
      await renderPendingLoans()
    }
    list.appendChild(row)
  })
  pendingDiv.appendChild(list)
}

async function renderAllMembers() {
  await loadMembers()
  const rows = state.members.map(m => `
    <tr>
      <td>${m.name}${m.is_admin ? ' ⭐' : ''}</td>
      <td>${m.phone || '-'}</td>
      <td>${formatDate(m.joined_date)}</td>
      <td><button class="btn secondary" onclick="renderMemberProfile(${m.id})">Details</button></td>
    </tr>
  `).join('')
  content.innerHTML = `
    <div class="panel">
      <h2 class="page-title">All Member Details</h2>
      <table class="table">
        <thead><tr><th>Name</th><th>Phone</th><th>Joined</th><th>Action</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `
}

async function renderAllHistory() {
  const m = await api(`/members/${state.currentUser.id}`)
  const requestRows = []
  // Loan applications from m.loans
  ;(m.loans || []).forEach(l => {
    const appliedDate = l.last_accrual_date || l.disbursed_date || ''
    const padSort = (s) => s && !s.includes('T') ? s + 'T00:00:00' : s
    let info = l.status === 'applied' ? 'Pending approval' : (l.status === 'active' ? 'Approved and active' : (l.status === 'rejected' ? (l.reject_reason || 'Rejected') : l.status))
    requestRows.push({ sortKey: padSort(appliedDate), date: appliedDate, type: 'Loan Application', amount: l.principal, status: l.status, info })
  })
  // Payment requests from m.payment_requests
  ;(m.payment_requests || []).forEach(r => {
    let info = r.status === 'rejected' ? (r.reject_reason || 'Rejected') : (r.status === 'approved' ? 'Approved on ' + formatDate(r.approved_date) : 'Pending')
    requestRows.push({ sortKey: r.date_submitted, date: r.date_submitted, type: r.type === 'share' ? 'Share Payment' : 'Loan Payment', amount: r.amount, status: r.status, info })
  })
  requestRows.sort((a, b) => b.sortKey.localeCompare(a.sortKey))
  const rowsHtml = requestRows.length ? requestRows.map(r => `<tr><td>${r.date ? formatDateTime(r.date.includes('T') ? r.date : r.date + 'T00:00:00') : '-'}</td><td>${r.type}</td><td>${formatCurrency(r.amount)}</td><td>${r.status}</td><td>${r.info}</td></tr>`).join('') : `<tr><td colspan="5" style="text-align:center;color:#94a3b8;">No history yet</td></tr>`
  content.innerHTML = `
    <div class="panel">
      <h2 class="page-title">📜 All History</h2>
      <p>All your requests — payments, loan applications, and their statuses.</p>
      <div class="table-scroll">
        <table class="table"><thead><tr><th>Date</th><th>Type</th><th>Amount</th><th>Status</th><th>Comments</th></tr></thead><tbody>${rowsHtml}</tbody></table>
      </div>
    </div>
  `
}

async function renderMemberProfile(memberId) {
  state.selectedMember = memberId
  const m = await api(`/members/${memberId}`)
  const own = state.currentUser.id === m.id
  const canManage = own || state.currentUser.is_admin
  // Calculate repaid amount per loan
  const repaidByLoan = {}
  ;(m.payments || []).forEach(p => {
    if (p.loan_id) repaidByLoan[p.loan_id] = (repaidByLoan[p.loan_id] || 0) + (p.principal_paid || p.amount || 0)
  })
  let loansCardsHtml
  try {
    loansCardsHtml = m.loans && m.loans.filter(l => l.status === 'active').length ? m.loans.filter(l => l.status === 'active').map(l => {
    const statusBadge = l.status === 'active' ? '<span class="badge success">Active</span>' : (l.status === 'applied' ? '<span class="badge warn">Applied</span>' : (l.status === 'rejected' ? '<span class="badge" style="background:rgba(239,68,68,0.15);color:#fca5a5">Rejected</span>' : '<span class="badge">' + l.status + '</span>'))
    const takenDate = l.disbursed_date || l.last_accrual_date || ''
    const repaid = repaidByLoan[l.id] || 0
    let closeDate = '-'
    if (l.disbursed_date && l.term_months) {
      const d = new Date(l.disbursed_date)
      d.setMonth(d.getMonth() + l.term_months)
      closeDate = formatDate(d.toISOString().slice(0, 10))
    }
    const pct = l.principal > 0 ? Math.round((repaid / l.principal) * 100) : 0
    const progressClass = pct >= 80 ? '' : (pct >= 40 ? 'warn' : '')
    const interestRate = l.rate_monthly ? (l.rate_monthly * 100) + '%' : '1%'
    return `
      <div class="loan-card">
        <div class="lc-top">
          <div class="lc-top-left">
            <span class="loan-id">💰 Loan #${l.id}</span>
            ${statusBadge}
            <span style="font-size:0.75rem;color:#64748b;margin-left:4px;">${interestRate}/mo</span>
          </div>
        </div>
        <div class="lc-grid">
          <div class="lc-cell lc-amount"><span class="lc-label">Loan Amount</span><span class="lc-value">${formatCurrency(l.principal)}</span></div>
          <div class="lc-cell lc-taken"><span class="lc-label">Taken Date</span><span class="lc-value">${takenDate ? formatDate(takenDate) : '-'}</span></div>
          <div class="lc-cell lc-close"><span class="lc-label">Close Date</span><span class="lc-value">${closeDate}</span></div>
          <div class="lc-cell lc-term"><span class="lc-label">Term</span><span class="lc-value">${l.term_months ? l.term_months + ' mo' : '-'}</span></div>
          <div class="lc-cell lc-repaid"><span class="lc-label">Repaid</span><span class="lc-value">${formatCurrency(repaid)}</span></div>
          <div class="lc-cell lc-outstanding"><span class="lc-label">Outstanding</span><span class="lc-value">${formatCurrency(l.outstanding)}</span></div>
        </div>
        ${l.status === 'rejected' ? `<div style="margin-bottom:8px;padding:6px 10px;background:rgba(239,68,68,0.08);border-radius:8px;font-size:0.8rem;color:#fca5a5">Reason: ${l.reject_reason || 'Not specified'}</div>` : ''}
        <div class="lc-progress-row">
          <span class="lc-progress-pct">${pct}% repaid</span>
          <div class="progress-bar"><div class="progress-fill ${progressClass}" style="width:${Math.min(pct, 100)}%"></div></div>
        </div>
      </div>`
  }).join('') : '<p style="color:#94a3b8;font-size:0.9rem;text-align:center;padding:12px 0;">No loans yet</p>'
  } catch (e) {
    console.error('Loans render error:', e)
    loansCardsHtml = '<p style="color:#ef4444;font-size:0.9rem;text-align:center;padding:12px 0;">Failed to load loans</p>'
  }
  // clickable avatar with inline edit/upload controls
  const avatarUrl = m.photo_url || ''
  const photoSnippet = `
    <div style="position:relative">
      <div id="profile-avatar" class="profile-avatar ${own || state.currentUser.is_admin ? 'clickable' : ''}" style="background-image: url('${avatarUrl}');">${!avatarUrl ? initials(m.name) : ''}</div>
      <input id="profile-photo-input" type="file" accept="image/*" style="display:none" />
      <div id="avatar-menu" class="avatar-menu hidden">
        <button class="btn" id="avatar-add-btn">Add new profile photo</button>
        ${m.photo_url ? `<button class="btn secondary" id="avatar-remove-btn">Remove profile photo</button>` : ''}
      </div>
      <div id="photo-controls" class="photo-controls">
        ${own ? `<button id="confirm-photo-btn" class="btn" style="display:none">Upload</button><button id="cancel-photo-btn" class="btn secondary" style="display:none">Cancel</button>` : ''}
        ${m.photo_url ? `<button id="remove-photo-btn" class="btn secondary" style="display:none">Remove Photo</button>` : ''}
      </div>
    </div>
  `

  const profileFields = `
    <div class="profile-card">
      ${photoSnippet}
      <div class="profile-copy">
        <h2>${m.name}</h2>
        <p><strong>Phone:</strong> <span class="input-readonly" id="ro-phone">${m.phone || '-'}</span></p>
        <p><strong>DOB:</strong> <span class="input-readonly" id="ro-dob">${m.dob ? formatDate(m.dob) : '-'}</span></p>
        <p><strong>Age:</strong> <span class="input-readonly">${calculateAge(m.dob)}</span></p>
        <p><strong>Address:</strong> <span class="input-readonly" id="ro-address">${m.address || '-'}</span></p>
        ${own ? `<div style="margin-top:8px;"><button class="btn" id="self-edit-btn">Edit Profile</button></div>` : ''}
      </div>
      <div class="profile-summary">
        <div class="stats-grid">
          <div class="stat-card"><strong>${m.contributions.length}</strong><span>Total Contributions</span></div>
          <div class="stat-card"><strong>${m.loans.length}</strong><span>Loans</span></div>
          <div class="stat-card"><strong>${m.dues.filter(d => !d.paid).length}</strong><span>Unpaid Dues</span></div>
        </div>
      </div>
    </div>
  `
  // Build unified payment history (share contributions + loan payments merged by date)
  const historyByDate = {}
  m.contributions.forEach(c => {
    const key = c.date
    if (!historyByDate[key]) historyByDate[key] = { date: c.date, share: 0, deposit: 0, loan: 0 }
    if (c.type === 'deposit') historyByDate[key].deposit += c.amount
    else historyByDate[key].share += c.amount
  })
  ;(m.payments || []).forEach(p => {
    const key = p.date
    if (!historyByDate[key]) historyByDate[key] = { date: p.date, share: 0, deposit: 0, loan: 0 }
    historyByDate[key].loan += p.amount
  })
  const allHistory = Object.values(historyByDate).sort((a, b) => b.date.localeCompare(a.date))
  const paymentHistory = allHistory.filter(r => r.share > 0 || r.loan > 0)
  const totalShare = allHistory.reduce((s, r) => s + r.share, 0)
  const totalDeposit = allHistory.reduce((s, r) => s + r.deposit, 0)
  const totalLoanPaid = allHistory.reduce((s, r) => s + r.loan, 0)
  const historyHeader = `<div style="margin-top:12px;"><strong>Total Share:</strong> ${formatCurrency(totalShare)} &nbsp;|&nbsp; <strong>Total Deposit:</strong> <span style="color:#a78bfa">${formatCurrency(totalDeposit)}</span> &nbsp;|&nbsp; <strong>Total Loan Paid:</strong> ${formatCurrency(totalLoanPaid)}</div>`
  // Admin edit is hidden by default; show an "Edit Member (Admin)" button that reveals the form when clicked
  const adminEdit = (state.currentUser.is_admin && !own) ? `
    <div id="admin-edit-container" class="panel" style="padding:12px;">
      <button class="btn" id="admin-edit-toggle">Edit Member (Admin)</button>
      <div id="admin-edit-form" style="display:none;margin-top:12px"></div>
    </div>
  ` : ''
  const today = new Date().toISOString().slice(0, 10)
  content.innerHTML = `
    <div class="profile-wrapper">
      ${profileFields}
      ${adminEdit}
    </div>

    <div class="grid-2" style="margin-top:18px; gap:20px;">
      <div>
        <div class="panel compact-panel">
          <h3>📤 Submit Proof of Payment</h3>
          <div class="input-row" style="display:flex;gap:12px;">
            <div style="flex:1">
              <label>Share Amount *</label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="share-amount-input" type="text" value="500" /></div>
            </div>
            <div style="flex:1">
              <label>Loan Amount</label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="loan-amount-input" type="text" placeholder="0" /></div>
            </div>
          </div>
          <div class="input-row small-row">
            <label style="flex-basis:100%">Payment Date</label>
            <input id="pay-txn-date" type="date" value="${today}" max="${today}" />
          </div>
          <div class="input-row small-row"><input id="pay-note" placeholder="Note (optional)" /></div>
          <div class="upload-area" id="upload-area">
            <input id="screenshot-input" type="file" accept="image/*" hidden />
            <div class="upload-placeholder">
              <span class="upload-icon">📎</span>
              <span class="upload-text">Tap to upload receipt / proof</span>
              <span class="upload-hint">Image only</span>
            </div>
            <div class="upload-preview hidden">
              <img id="upload-preview-img" />
              <span id="upload-filename"></span>
              <button class="upload-remove" id="upload-remove-btn" type="button">✕</button>
            </div>
          </div>
          <button class="btn primary" id="submit-payment-btn-top">Submit Payment for Approval</button>
        </div>
        <div class="panel compact-panel" style="margin-top:12px;">
          <h3>💰 Request Loan</h3>
          ${canManage ? `
            <div class="input-row"><label style="flex-basis:100%">Loan Amount</label><div class="input-with-currency"><span class="currency">₹</span><input id="request-loan-amount" type="text" placeholder="0" /></div></div>
            <div class="input-row" style="display:flex;gap:12px;">
              <div style="flex:1">
                <label style="font-size:0.8rem;color:#94a3b8;display:block;text-align:center;margin-bottom:2px;">Years</label>
                <div class="stepper">
                  <button class="stepper-btn" id="loan-years-down">−</button>
                  <span class="stepper-value" id="loan-years-display">1</span>
                  <button class="stepper-btn" id="loan-years-up">+</button>
                </div>
              </div>
              <div style="flex:1">
                <label style="font-size:0.8rem;color:#94a3b8;display:block;text-align:center;margin-bottom:2px;">Months</label>
                <div class="stepper">
                  <button class="stepper-btn" id="loan-months-down">−</button>
                  <span class="stepper-value" id="loan-months-display">0</span>
                  <button class="stepper-btn" id="loan-months-up">+</button>
                </div>
              </div>
            </div>
            <div id="loan-period-display" style="text-align:center;font-size:0.85rem;color:#94a3b8;margin-bottom:10px;">1 year 0 months</div>
            <button class="btn primary" id="request-loan-btn">Request Loan</button>
          ` : '<p>This member profile is view-only.</p>'}
        </div>
      </div>
      <div>
        <div class="panel" style="margin-bottom:12px;">
          <h3>📊 Payment History</h3>
          ${historyHeader}
          <div class="table-scroll">
            <table class="table"><thead><tr><th>Date</th><th>Share</th><th>Deposit</th><th>Loan Paid</th><th>Total</th></tr></thead><tbody>${paymentHistory.map(r => `<tr><td>${formatDate(r.date)}</td><td>${r.share ? formatCurrency(r.share) : '-'}</td><td>${r.deposit ? `<span style="color:#a78bfa">${formatCurrency(r.deposit)}</span>` : '-'}</td><td>${r.loan ? formatCurrency(r.loan) : '-'}</td><td>${formatCurrency(r.share + r.deposit + r.loan)}</td></tr>`).join('')}</tbody></table>
          </div>
        </div>
        <div class="panel compact-panel" id="loans-panel">
          <h3 style="margin-bottom:10px;">🏦 Loans</h3>
          ${loansCardsHtml}
        </div>
      </div>
    </div>
  `
    // Attach handlers for inline profile photo and edit/save flow
    const avatar = document.getElementById('profile-avatar')
    const photoInput = document.getElementById('profile-photo-input')
    const confirmBtn = document.getElementById('confirm-photo-btn')
    const cancelBtn = document.getElementById('cancel-photo-btn')
    const removeBtn = document.getElementById('remove-photo-btn')
    const editBtn = document.getElementById('self-edit-btn')
    const submitPaymentBtnTop = document.getElementById('submit-payment-btn-top')
    let stagedBlob = null

    // avatar click opens a small visible menu (owner/admin) with clear actions
    const avatarMenu = document.getElementById('avatar-menu')
    const avatarAddBtn = document.getElementById('avatar-add-btn')
    const avatarRemoveBtn = document.getElementById('avatar-remove-btn')
    if (avatar && photoInput && (own || state.currentUser.is_admin)) {
      avatar.addEventListener('click', (ev) => {
        ev.stopPropagation()
        if (avatarMenu) avatarMenu.classList.toggle('hidden')
      })
      // Add new photo opens file picker
      if (avatarAddBtn) avatarAddBtn.addEventListener('click', () => { photoInput.click(); if (avatarMenu) avatarMenu.classList.add('hidden') })
      // Remove via avatar menu delegates to same remove flow
      if (avatarRemoveBtn) avatarRemoveBtn.addEventListener('click', async () => {
        if (!confirm('Remove photo?')) return
        await api(`/members/${m.id}/self`, {method:'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({photo_url: ''})})
        showToast('Photo removed', 'info')
        renderMemberProfile(m.id)
      })
      // clicking outside hides the menu
      document.addEventListener('click', () => { if (avatarMenu) avatarMenu.classList.add('hidden') })
      photoInput.addEventListener('change', async (ev) => {
        const file = ev.target.files && ev.target.files[0]
        if (!file) return
        // create resized preview 300x300
        const url = URL.createObjectURL(file)
        const img = new Image()
        img.onload = () => {
          const size = 300
          const canvas = document.createElement('canvas')
          canvas.width = size; canvas.height = size
          const ctx = canvas.getContext('2d')
          // center-crop
          const s = Math.min(img.width, img.height)
          const sx = (img.width - s)/2
          const sy = (img.height - s)/2
          ctx.drawImage(img, sx, sy, s, s, 0, 0, size, size)
          const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
          avatar.style.backgroundImage = `url(${dataUrl})`
          // prepare blob for upload when confirmed
          canvas.toBlob((b) => { stagedBlob = b }, 'image/jpeg', 0.9)
          if (confirmBtn) confirmBtn.style.display = 'inline-block'
          if (cancelBtn) cancelBtn.style.display = 'inline-block'
          URL.revokeObjectURL(url)
        }
        img.src = url
      })
    }

    if (confirmBtn) {
      confirmBtn.onclick = async () => {
        if (!stagedBlob) { showToast('No image selected', 'error'); return }
        const fd = new FormData()
        fd.append('photo', stagedBlob, 'photo.jpg')
        const res = await fetch(`/api/members/${m.id}/upload_photo`, {method: 'POST', body: fd})
        if (res.ok) { showToast(t('Photo uploaded'), 'success'); renderMemberProfile(m.id) } else { const e = await res.json().catch(()=>({})); showToast(e.error||t('Upload failed'),'error') }
      }
    }

    if (cancelBtn) {
      cancelBtn.onclick = () => {
        const inp = document.getElementById('profile-photo-input')
        if (inp) inp.value = ''
        stagedBlob = null
        if (m.photo_url) avatar.style.backgroundImage = `url('${m.photo_url}')`
        else avatar.style.backgroundImage = ''
        if (confirmBtn) confirmBtn.style.display = 'none'
        if (cancelBtn) cancelBtn.style.display = 'none'
      }
    }

    if (removeBtn) {
      // hidden until edit mode (legacy inline button)
      removeBtn.style.display = 'none'
      removeBtn.onclick = async () => {
        if (!confirm('Remove photo?')) return
        await api(`/members/${m.id}/self`, {method:'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({photo_url: ''})})
        showToast('Photo removed', 'info')
        renderMemberProfile(m.id)
      }
    }

    // Edit flow: transform readonly fields into inputs when user clicks Edit
    if (editBtn) {
      editBtn.onclick = () => {
        const copy = document.querySelector('.profile-copy')
        const phoneSpan = copy.querySelector('#ro-phone')
        const dobSpan = copy.querySelector('#ro-dob')
        const addrSpan = copy.querySelector('#ro-address')
        if (!phoneSpan || !dobSpan || !addrSpan) return
        phoneSpan.outerHTML = `<input id="self-phone" class="input-edit" value="${m.phone||''}" />`
        dobSpan.outerHTML = `<input id="self-dob" class="input-edit" type="date" value="${m.dob||''}" />`
        addrSpan.outerHTML = `<input id="self-address" class="input-edit" value="${m.address||''}" />`
        editBtn.style.display = 'none'
        const btnWrap = document.createElement('div')
        btnWrap.style.marginTop = '8px'
        btnWrap.innerHTML = `<button class="btn primary" id="self-save-btn">Save</button> <button class="btn" id="self-cancel-btn">Cancel</button>`
        copy.appendChild(btnWrap)
        if (removeBtn) removeBtn.style.display = m.photo_url ? 'inline-block' : 'none'
        // bind save/cancel
        document.getElementById('self-save-btn').onclick = async () => {
          await handleSelfUpdate(m.id)
        }
        document.getElementById('self-cancel-btn').onclick = () => renderMemberProfile(m.id)
      }
    }

    // Apply Indian number formatting to amount inputs
    ;['share-amount-input', 'loan-amount-input', 'request-loan-amount'].forEach(id => {
      const el = document.getElementById(id)
      if (el) indianizeInput(el)
    })

    // Upload area handler
    const uploadArea = document.getElementById('upload-area')
    const screenshotInput = document.getElementById('screenshot-input')
    const uploadPreview = uploadArea?.querySelector('.upload-preview')
    const uploadPlaceholder = uploadArea?.querySelector('.upload-placeholder')
    const previewImg = document.getElementById('upload-preview-img')
    const filenameSpan = document.getElementById('upload-filename')
    const uploadRemoveBtn = document.getElementById('upload-remove-btn')
    if (uploadArea && screenshotInput) {
      uploadArea.addEventListener('click', () => screenshotInput.click())
      screenshotInput.addEventListener('change', () => {
        const file = screenshotInput.files && screenshotInput.files[0]
        if (!file) return
        if (uploadPlaceholder) uploadPlaceholder.classList.add('hidden')
        if (uploadPreview) uploadPreview.classList.remove('hidden')
        if (filenameSpan) filenameSpan.textContent = file.name
        const reader = new FileReader()
        reader.onload = (e) => { if (previewImg) previewImg.src = e.target.result }
        reader.readAsDataURL(file)
      })
      if (uploadRemoveBtn) {
        uploadRemoveBtn.addEventListener('click', (e) => {
          e.stopPropagation()
          screenshotInput.value = ''
          if (uploadPreview) uploadPreview.classList.add('hidden')
          if (uploadPlaceholder) uploadPlaceholder.classList.remove('hidden')
          if (previewImg) previewImg.src = ''
          if (filenameSpan) filenameSpan.textContent = ''
        })
      }
    }

    if (submitPaymentBtnTop) {
      submitPaymentBtnTop.onclick = () => handleSubmitPayment(m.id)
    }
    // loan request button handler
    const requestLoanBtn = document.getElementById('request-loan-btn')
    if (requestLoanBtn) {
      // Set up year/month steppers
      let loanYears = 1, loanMonths = 0
      const yearsDisplay = document.getElementById('loan-years-display')
      const monthsDisplay = document.getElementById('loan-months-display')
      const periodDisplay = document.getElementById('loan-period-display')
      function updatePeriodDisplay() {
        if (yearsDisplay) yearsDisplay.textContent = loanYears
        if (monthsDisplay) monthsDisplay.textContent = loanMonths
        if (periodDisplay) {
          const y = loanYears + ' year' + (loanYears !== 1 ? 's' : '')
          const m = loanMonths + ' month' + (loanMonths !== 1 ? 's' : '')
          periodDisplay.textContent = y + ' ' + m
        }
      }
      document.getElementById('loan-years-up')?.addEventListener('click', () => { loanYears = Math.min(loanYears + 1, 10); updatePeriodDisplay() })
      document.getElementById('loan-years-down')?.addEventListener('click', () => { loanYears = Math.max(loanYears - 1, 0); updatePeriodDisplay() })
      document.getElementById('loan-months-up')?.addEventListener('click', () => { loanMonths = Math.min(loanMonths + 1, 11); updatePeriodDisplay() })
      document.getElementById('loan-months-down')?.addEventListener('click', () => { loanMonths = Math.max(loanMonths - 1, 0); updatePeriodDisplay() })
      updatePeriodDisplay()

      requestLoanBtn.onclick = async () => {
        const raw = document.getElementById('request-loan-amount').value.replace(/,/g, '')
        const amt = Number(raw) || 0
        if (!amt || amt <= 0) { showToast('Enter loan amount', 'error'); return }
        const totalMonths = loanYears * 12 + loanMonths
        if (totalMonths < 1) { showToast('Select at least 1 month term', 'error'); return }
        await api(`/members/${m.id}/apply_loan`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({amount: amt, term_months: totalMonths}),
        })
        showToast('Loan request submitted', 'success')
        renderMemberProfile(m.id)
      }
    }
    // Admin edit toggle: render admin form when requested
    const adminToggle = document.getElementById('admin-edit-toggle')
    if (adminToggle) {
      adminToggle.onclick = () => {
        const formDiv = document.getElementById('admin-edit-form')
        if (!formDiv) return
        if (formDiv.innerHTML.trim()) {
          // already rendered -> toggle visibility
          formDiv.style.display = formDiv.style.display === 'none' ? 'block' : 'none'
          return
        }
        formDiv.innerHTML = `
          <h3>Edit Member Details</h3>
          <div class="input-row"><input id="edit-phone" placeholder="Phone" value="${m.phone || ''}" /></div>
          <div class="input-row"><input id="edit-dob" type="date" value="${m.dob || ''}" /></div>
          <div class="input-row"><input id="edit-address" placeholder="Address" value="${m.address || ''}" /></div>
          <div class="input-row"><input id="edit-photo" placeholder="Photo URL" value="${m.photo_url || ''}" /></div>
          <div style="margin-top:8px;"><button class="btn primary" id="admin-save-btn">Save Details</button> <button class="btn" id="admin-cancel-btn">Cancel</button></div>
        `
        formDiv.style.display = 'block'
        document.getElementById('admin-save-btn').onclick = async () => { await handleUpdateDetails(m.id) }
        document.getElementById('admin-cancel-btn').onclick = () => { formDiv.style.display = 'none' }
      }
    }
}

async function handleAddMember() {
  const name = document.getElementById('new-member-name').value.trim()
  const phone = document.getElementById('new-member-phone').value.trim()
  const dob = document.getElementById('new-member-dob').value
  const address = document.getElementById('new-member-address').value.trim()
  const photo_url = document.getElementById('new-member-photo').value.trim()
  if (!name) { showToast(t('Enter a name'), 'error'); return }
  await api('/members', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name, phone, dob, address, photo_url}),
  })
  await loadMembers()
  renderAdminPanel()
}

async function handlePayShare(memberId) {
  const amount = Number(document.getElementById('share-amount').value) || 500
  const txn_date = document.getElementById('share-date').value || new Date().toISOString().slice(0,10)
  if (new Date(txn_date) > new Date()) { showToast('Txn date cannot be in the future', 'error'); return }
  const fd = new FormData()
  fd.append('amount', amount)
  fd.append('type', 'share')
  fd.append('txn_date', txn_date)
  const res = await fetch(`/api/members/${memberId}/submit_payment_request`, {method: 'POST', body: fd})
  if (res.ok) {
    showToast(t('Share requested'), 'success')
    renderMemberProfile(memberId)
  } else {
    const e = await res.json().catch(()=>({error:'failed'}))
    showToast(e.error || 'Failed', 'error')
  }
}

async function handleApplyLoan(memberId) {
  const amount = Number(document.getElementById('loan-amount').value)
  const term = Number(document.getElementById('loan-term').value) || 12
  const txn_date = document.getElementById('loan-date') ? document.getElementById('loan-date').value : new Date().toISOString().slice(0,10)
  if (!amount || amount <= 0) { showToast(t('Enter loan amount'), 'error'); return }
  // create loan application
  await api(`/members/${memberId}/apply_loan`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({amount, term_months: term}),
  })
  // also create payment request for initial loan payment if amount > 0
  const fd = new FormData()
  fd.append('amount', amount)
  fd.append('type', 'loan')
  fd.append('txn_date', txn_date)
  await fetch(`/api/members/${memberId}/submit_payment_request`, {method: 'POST', body: fd})
  showToast(t('Loan applied'), 'success')
  renderMemberProfile(memberId)
}


async function handlePayDue(memberId, dueId, amount) {
  await api(`/members/${memberId}/pay_due`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({due_id: dueId, amount}),
  })
  renderMemberProfile(memberId)
}

async function handleUpdateDetails(memberId) {
  const phone = document.getElementById('edit-phone').value.trim()
  const dob = document.getElementById('edit-dob').value
  const address = document.getElementById('edit-address').value.trim()
  const photo_url = document.getElementById('edit-photo').value.trim()
  const url = state.currentUser.is_admin ? `/members/${memberId}` : `/members/${memberId}/self`
  await api(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({phone, dob, address, photo_url}),
  })
  renderMemberProfile(memberId)
}

window.handlePayDue = handlePayDue
window.handlePayShare = handlePayShare
window.handleApplyLoan = handleApplyLoan
window.handleUpdateDetails = handleUpdateDetails
window.renderMemberProfile = renderMemberProfile
window.setView = setView

// Member cancels their own pending request
async function handleCancelRequest(memberId, reqId) {
  if (!confirm(t('Confirm cancel?'))) return
  const res = await fetch(`/api/members/${memberId}/cancel_request/${reqId}`, {method:'POST'})
  if (res.ok) {
    showToast('Cancelled', 'success')
    state.activeView === 'my-history' ? renderAllHistory() : renderMemberProfile(memberId)
  } else {
    const e = await res.json().catch(()=>({error:'failed'}))
    showToast(e.error || 'Failed to cancel', 'error')
  }
}
window.handleCancelRequest = handleCancelRequest

async function handleSubmitPayment(memberId) {
  const shareRaw = document.getElementById('share-amount-input').value.replace(/,/g, '')
  const loanRaw = document.getElementById('loan-amount-input').value.replace(/,/g, '')
  const shareAmount = Number(shareRaw) || 0
  const loanAmount = Number(loanRaw) || 0
  const txnDate = document.getElementById('pay-txn-date').value
  const note = document.getElementById('pay-note').value
  if (!txnDate) { showToast('Select a payment date', 'error'); return }
  if (new Date(txnDate) > new Date()) { showToast('Date cannot be in the future', 'error'); return }
  // Share amount is mandatory
  if (!shareAmount || shareAmount <= 0) { showToast('Share amount is required', 'error'); return }
  // submit share payment request
  const screenshotInput = document.getElementById('screenshot-input')
  const screenshotFile = screenshotInput?.files?.[0]
  try {
    const fd1 = new FormData()
    fd1.append('amount', shareAmount)
    fd1.append('type', 'share')
    fd1.append('note', note)
    fd1.append('txn_date', txnDate)
    if (screenshotFile) fd1.append('screenshot', screenshotFile)
    const res1 = await fetch(`/api/members/${memberId}/submit_payment_request`, {method:'POST', body: fd1})
    if (!res1.ok) {
      const e = await res1.json().catch(()=>({error:'failed'}))
      showToast(e.error || 'Failed to submit share request', 'error')
      return
    }
    // if loan amount also provided, submit a separate loan request
    if (loanAmount && loanAmount > 0) {
      const fd2 = new FormData()
      fd2.append('amount', loanAmount)
      fd2.append('type', 'loan')
      fd2.append('note', note)
      fd2.append('txn_date', txnDate)
      const res2 = await fetch(`/api/members/${memberId}/submit_payment_request`, {method:'POST', body: fd2})
      if (!res2.ok) {
        const e = await res2.json().catch(()=>({error:'failed'}))
        showToast(e.error || 'Share submitted; loan request failed', 'warn')
        renderMemberProfile(memberId)
        return
      }
    }
    showToast(t('Submitted for approval'), 'success')
    renderMemberProfile(memberId)
  } catch (err) {
    showToast((err && err.message) || 'Submit failed', 'error')
  }
}

async function handleSelfUpdate(memberId) {
  const phone = document.getElementById('self-phone').value.trim()
  const dob = document.getElementById('self-dob').value
  const address = document.getElementById('self-address').value.trim()
  await api(`/members/${memberId}/self`, {
    method: 'PATCH',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({phone, dob, address}),
  })
  renderMemberProfile(memberId)
}

async function handleUploadPhoto(memberId) {
  const input = document.getElementById('self-photo-file')
  if (!input || !input.files || !input.files[0]) { showToast('Choose a photo file', 'error'); return }
  const fd = new FormData()
  fd.append('photo', input.files[0])
  const res = await fetch(`/api/members/${memberId}/upload_photo`, {method: 'POST', body: fd})
  if (res.ok) {
    showToast(t('Photo uploaded'), 'success')
    renderMemberProfile(memberId)
  } else {
    const e = await res.json().catch(()=>({error:'failed'}))
    showToast(e.error || t('Upload failed'), 'error')
  }
}

const ADMIN_PIN = '1234'

document.addEventListener('DOMContentLoaded', () => {
  try {
    loginScreen = document.getElementById('login-screen')
    mainScreen = document.getElementById('main-screen')
    menuLinks = document.getElementById('menu-links')
    content = document.getElementById('content')
    memberSelect = document.getElementById('member-select')
    adminPin = document.getElementById('admin-pin')
    loginButton = document.getElementById('login-button')
    loginError = document.getElementById('login-error')
    if (loginButton) {
      try { loginButton.type='button' } catch(_){}
      loginButton.onclick = handleLogin
    }
    // Enter key handling for convenience
    if (adminPin) adminPin.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin() })
    if (memberSelect) memberSelect.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin() })
    init()
  } catch (e) {
    try { fetch('/api/client_error', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: 'binding_error', stack: (e && e.stack)||String(e), ua: navigator.userAgent})}) } catch(_){}
  }
})

// Robust delegation: catch clicks on login button even if direct binding failed
document.addEventListener('click', (e) => {
  const target = e.target || e.srcElement
  if (!target) return
  if (target.id === 'login-button' || target.closest && target.closest('#login-button')) {
    showToast('Logging in...', 'info', 1200)
    try { handleLogin() } catch(err) { try { fetch('/api/client_error', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message:'login_click_error', stack: (err && err.stack)||String(err)})}) } catch(_){} }
  }
})

// Client-side error reporting: send errors to server for inspection
window.addEventListener('error', function (ev) {
  try {
    fetch('/api/client_error', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: ev.message, url: ev.filename || ev.filename, line: ev.lineno, col: ev.colno, stack: (ev.error && ev.error.stack) || null, ua: navigator.userAgent, time: new Date().toISOString()})
    })
  } catch (e) {}
})
window.addEventListener('unhandledrejection', function (ev) {
  try {
    const reason = ev.reason && (ev.reason.stack || ev.reason.message) || String(ev.reason)
    fetch('/api/client_error', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: 'unhandledrejection', url: location.href, line: null, col: null, stack: reason, ua: navigator.userAgent, time: new Date().toISOString()})})
  } catch (e) {}
})
