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

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'})
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
    {id: 'all-members', label: t('All Members')},
  ]
  if (state.currentUser.is_admin) {
    items.splice(2, 0, {id: 'admin-panel', label: 'Admin Panel'})
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
  if (view === 'all-members') return renderAllMembers()
  return renderHome()
}

async function renderHome() {
  const stats = await api('/admin/stats', {headers: {'X-ADMIN-PIN': ADMIN_PIN}}).catch(()=>null)
  const html = `
    <div class="panel">
      <h2 class="page-title">Welcome, ${state.currentUser.name}</h2>
      <p>Overview: incoming collections, loans, and available funds.</p>
      <div class="stats-grid" style="margin-top:12px">
        <div class="stat-card loan-given"><strong>${stats?formatCurrency(stats.total_lent):'-'}</strong><span>Loan Given</span></div>
        <div class="stat-card hardlocked"><strong>${stats?formatCurrency(stats.cash_on_hand):'-'}</strong><span>Hardlocked / FD</span></div>
        <div class="stat-card available"><strong>${stats?formatCurrency(stats.available_to_lend):'-'}</strong><span>Available to Loan</span></div>
      </div>

      <!-- Big Total box with inline breakdown -->
      <div class="panel" style="margin-top:14px;padding:18px;">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
          <div style="flex:1;min-width:220px">
            <div style="font-size:20px;color:#374151">Total Collected</div>
            <div style="font-size:28px;font-weight:700;margin-top:6px">${stats?formatCurrency(stats.total_collected):'-'}</div>
            <div style="color:#6b7280;margin-top:8px">This is the sum of all collection sources below.</div>
          </div>
          <div style="flex:1;min-width:220px">
            <ul style="list-style:none;padding:0;margin:0">
              <li style="margin-bottom:6px"><strong>Initial Deposits:</strong> ${stats?formatCurrency(stats.deposits_total):'-'}</li>
              <li style="margin-bottom:6px"><strong>Shares:</strong> ${stats?formatCurrency(stats.shares_total):'-'}</li>
              <li style="margin-bottom:6px"><strong>Loan Interest:</strong> ${stats?formatCurrency(stats.loan_interest_received):'-'}</li>
              <li style="margin-bottom:6px"><strong>Other Income:</strong> ${stats?formatCurrency(stats.others_total):'-'}</li>
            </ul>
          </div>
        </div>
      </div>
      <!-- removed separate "All Members" and "Admin Panel" cards; use menu links instead -->
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
          <h3 style="margin-top:18px">Server Logs</h3>
          <div id="admin-logs"></div>
          <div style="margin-top:8px;"><button class="btn" id="refresh-logs">Refresh Logs</button></div>
        </div>
      </div>
    </div>
  `
  content.innerHTML = html
  document.getElementById('add-member-btn').onclick = handleAddMember
  await renderPendingLoans()
  await renderPendingPayments()
  document.getElementById('refresh-logs').onclick = renderAdminLogs
  await renderAdminLogs()
}


async function renderPendingPayments() {
  const div = document.getElementById('pending-payments')
  div.innerHTML = ''
  try {
    const items = await api('/admin/payment_requests', {headers: {'X-ADMIN-PIN': ADMIN_PIN}})
    if (!items || items.length === 0) {
      div.innerHTML = '<p>No pending payments</p>'
      return
    }
    const list = document.createElement('div')
    list.className = 'list-card'
    items.forEach(it => {
      const row = document.createElement('div')
      row.className = 'list-item'
      row.innerHTML = `<div><strong>${it.member_name}</strong><br><small>${it.type} ₹${it.amount} — ${it.note || ''}</small></div><div>${it.screenshot?`<a href="${it.screenshot}" target="_blank">Screenshot</a>`:''}</div><div><button class="btn primary approve-btn">Approve</button> <button class="btn secondary reject-btn">Reject</button></div>`
      row.querySelector('.approve-btn').onclick = async () => {
        await fetch(`/api/admin/approve_request/${it.id}`, {method:'POST', headers: {'X-ADMIN-PIN': ADMIN_PIN}})
        await renderPendingPayments()
      }
      row.querySelector('.reject-btn').onclick = async () => {
        const reason = prompt('Reason for rejection')
        if (reason === null) return
        await fetch(`/api/admin/reject_request/${it.id}`, {method:'POST', headers: {'Content-Type':'application/json','X-ADMIN-PIN': ADMIN_PIN}, body: JSON.stringify({reason})})
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
  const loans = []
  const pendingDiv = document.getElementById('pending-loans')
  pendingDiv.innerHTML = ''
  for (const member of state.members) {
    const detail = await api(`/members/${member.id}`)
    detail.loans.filter(l => l.status === 'applied').forEach(loan => loans.push({member, loan}))
  }
  if (loans.length === 0) {
    pendingDiv.innerHTML = '<p>No pending loans at the moment.</p>'
    return
  }
  const list = document.createElement('div')
  list.className = 'list-card'
  loans.forEach(item => {
    const row = document.createElement('div')
    row.className = 'list-item'
    row.innerHTML = `<div><strong>${item.member.name}</strong><br><small>Loan ₹${item.loan.principal} for ${item.loan.term_months} mo</small></div><button class="btn secondary">View</button>`
    row.querySelector('button').onclick = () => renderMemberProfile(item.member.id)
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

async function renderMemberProfile(memberId) {
  state.selectedMember = memberId
  const m = await api(`/members/${memberId}`)
  const own = state.currentUser.id === m.id
  const canManage = own || state.currentUser.is_admin
  const duesHtml = m.dues.map(d => {
    const dueDate = formatDate(d.due_date)
    const paid = d.paid ? 'Yes' : 'No'
    const lateDays = d.paid ? 0 : Math.max(0, Math.floor((new Date() - new Date(d.due_date)) / 86400000))
    const lateFee = lateDays * 50
    return `<tr><td>${dueDate}</td><td>${formatCurrency(d.amount)}</td><td>${paid}</td><td>${lateFee ? formatCurrency(lateFee) : '-'}</td><td>${!d.paid && canManage ? `<button class="btn secondary" onclick="handlePayDue(${m.id}, ${d.id}, ${d.amount})">Pay</button>` : '-'}</td></tr>`
  }).join('')
  const loansHtml = m.loans.map(l => {
    const statusBadge = l.status === 'active' ? '<span class="badge success">Active</span>' : '<span class="badge warn">Applied</span>'
    const showApprove = state.currentUser.is_admin && l.status === 'applied'
    const showPay = l.status === 'active' && (own || state.currentUser.is_admin)
    const action = showApprove
      ? `<button class="btn secondary" onclick="handleLoanAction(${m.id}, ${l.id}, '${l.status}')">Approve</button>`
      : showPay
        ? `<button class="btn secondary" onclick="handleLoanAction(${m.id}, ${l.id}, '${l.status}')">Pay</button>`
        : '-'
    return `
      <tr>
        <td>${l.id}</td>
        <td>${formatCurrency(l.principal)}</td>
        <td>${formatCurrency(l.outstanding)}</td>
        <td>${l.term_months} mo</td>
        <td>${statusBadge}</td>
        <td>${action}</td>
      </tr>`
  }).join('')
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
    </div>
  `
  const requestsHtml = m.payment_requests && m.payment_requests.length ? `
    <div class="panel" style="margin-top:12px;">
      <h3>Payment Requests</h3>
      <table class="table"><thead><tr><th>Date</th><th>Txn Date</th><th>Amount</th><th>Type</th><th>Status</th><th>Info</th><th>Action</th></tr></thead><tbody>
      ${m.payment_requests.map(r => `<tr><td>${formatDate(r.date_submitted)}</td><td>${r.txn_date||'-'}</td><td>${formatCurrency(r.amount)}</td><td>${r.type}</td><td>${r.status}</td><td>${r.status==='rejected'? (r.reject_reason||'Rejected') : (r.status==='approved'?('Approved on '+formatDate(r.approved_date)): 'Pending')}</td><td>${(r.status==='pending' && own) ? `<button class="btn secondary" onclick="handleCancelRequest(${m.id}, ${r.id})">${t('Cancel')}</button>` : '-'}</td></tr>`).join('')}
      </tbody></table>
    </div>
  ` : ''
  // contributions: put deposit at top
  const deposits = m.contributions.filter(c => c.type === 'deposit')
  const shares = m.contributions.filter(c => c.type !== 'deposit')
  const expectedMonths = monthsBetweenInclusive(m.joined_date)
  const paidMonths = shares.length
  const contributionHeader = `<div style="margin-top:12px;"><strong>Total contributions:</strong> ${paidMonths}/${expectedMonths}</div>`
  // Admin edit is hidden by default; show an "Edit Member (Admin)" button that reveals the form when clicked
  const adminEdit = (state.currentUser.is_admin && !own) ? `
    <div id="admin-edit-container" class="panel" style="padding:12px;">
      <button class="btn" id="admin-edit-toggle">Edit Member (Admin)</button>
      <div id="admin-edit-form" style="display:none;margin-top:12px"></div>
    </div>
  ` : ''
  content.innerHTML = `
    <div class="panel">
      ${profileFields}
      ${adminEdit}
      <div class="panel" style="margin-top:12px;">
        <h3>Submit Payment / Receipt</h3>
        <div class="input-row"><select id="pay-type"><option value="share">Share</option><option value="loan">Loan payment</option></select></div>
        <div class="input-row"><input id="pay-amount" type="number" placeholder="Amount" /></div>
        <div class="input-row"><input id="pay-note" placeholder="Note (optional)" /></div>
        <div class="input-row"><input id="pay-screenshot" type="file" accept="image/*" /></div>
        <button class="btn primary" id="submit-payment-btn-top">Submit Payment for Approval</button>
      </div>
      <div class="grid-2" style="margin-top:18px;">
        <div>
          <h3>Summary</h3>
          <p><strong>Joined:</strong> ${formatDate(m.joined_date)}</p>
          <p><strong>Deposit:</strong> ${formatCurrency(m.deposit_amount)}</p>
          <p><strong>Role:</strong> ${m.is_admin ? 'Admin' : 'Member'}</p>
        </div>
        <div class="stats-grid">
          <div class="stat-card"><strong>${m.contributions.length}</strong><span>Total Contributions</span></div>
          <div class="stat-card"><strong>${m.loans.length}</strong><span>Loans</span></div>
          <div class="stat-card"><strong>${m.dues.filter(d => !d.paid).length}</strong><span>Unpaid Dues</span></div>
        </div>
      </div>
      <div class="grid-2" style="margin-top:18px;">
        <div class="panel">
          <h3>Actions</h3>
          ${canManage ? `
            <div class="input-row"><input id="share-amount" type="number" placeholder="₹500" value="500" /></div>
              <div class="input-row"><label>Date</label><input id="share-date" type="date" value="${new Date().toISOString().slice(0,10)}" /></div>
              <button class="btn primary" onclick="handlePayShare(${m.id})">Request Share Payment</button>
            <div class="input-row" style="margin-top:14px;"><input id="loan-amount" type="number" placeholder="Loan amount" /><input id="loan-term" type="number" placeholder="Term months" value="12" /></div>
              <div class="input-row"><label>Loan payment date</label><input id="loan-date" type="date" value="${new Date().toISOString().slice(0,10)}" /></div>
            <button class="btn primary" onclick="handleApplyLoan(${m.id})">Apply Loan</button>
          ` : '<p>This member profile is view-only.</p>'}
        </div>
        <div class="panel">
          <h3>Contribution History</h3>
          ${contributionHeader}
          <table class="table"><thead><tr><th>Date</th><th>Amount</th><th>Type</th></tr></thead><tbody>${[...deposits, ...shares].map(c => `<tr><td>${formatDate(c.date)}</td><td>${formatCurrency(c.amount)}</td><td>${c.type}</td></tr>`).join('')}</tbody></table>
        </div>
      </div>
      <div class="grid-2" style="margin-top:18px;">
        <div class="panel">
          <h3>Monthly Dues</h3>
          <table class="table"><thead><tr><th>Due Date</th><th>Amount</th><th>Paid</th><th>Late Fee</th><th>Action</th></tr></thead><tbody>${duesHtml}</tbody></table>
        </div>
        <div class="panel">
          <h3>Loans</h3>
          <table class="table"><thead><tr><th>ID</th><th>Principal</th><th>Outstanding</th><th>Term</th><th>Status</th><th>Action</th></tr></thead><tbody>${loansHtml}</tbody></table>
        </div>
      </div>
      <!-- bottom submit payment removed; primary submit panel above -->
      ${requestsHtml}
    </div>
  `
    // Attach handlers for inline profile photo and edit/save flow
    const avatar = document.getElementById('profile-avatar')
    const photoInput = document.getElementById('profile-photo-input')
    const confirmBtn = document.getElementById('confirm-photo-btn')
    const cancelBtn = document.getElementById('cancel-photo-btn')
    const removeBtn = document.getElementById('remove-photo-btn')
    const editBtn = document.getElementById('self-edit-btn')
    const submitPaymentBtn = document.getElementById('submit-payment-btn')
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

    if (submitPaymentBtn) {
      submitPaymentBtn.onclick = () => handleSubmitPayment(m.id)
    }
    if (submitPaymentBtnTop) {
      submitPaymentBtnTop.onclick = () => handleSubmitPayment(m.id)
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

async function handleLoanAction(memberId, loanId, status) {
  if (status === 'applied') {
    if (!state.currentUser.is_admin) {
      return showToast(t('Only admin'), 'error')
    }
    await api(`/admin/approve_loan/${loanId}`, {method: 'POST', headers: {'X-ADMIN-PIN': ADMIN_PIN}})
  } else {
    const amount = Number(prompt('Enter payment amount'))
    if (!amount || amount <= 0) return
    await api(`/members/${memberId}/pay_loan`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({loan_id: loanId, amount}),
    })
  }
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

window.handleLoanAction = handleLoanAction
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
    renderMemberProfile(memberId)
  } else {
    const e = await res.json().catch(()=>({error:'failed'}))
    showToast(e.error || 'Failed to cancel', 'error')
  }
}
window.handleCancelRequest = handleCancelRequest

async function handleSubmitPayment(memberId) {
  const amount = Number(document.getElementById('pay-amount').value)
  const type = document.getElementById('pay-type').value
  const note = document.getElementById('pay-note').value
  const file = document.getElementById('pay-screenshot').files[0]
  if (!amount || amount <= 0) { showToast(t('Enter amount'), 'error'); return }
  // validate txn date if present
  const shareDateInput = document.getElementById('share-date')
  if (shareDateInput && shareDateInput.value && new Date(shareDateInput.value) > new Date()) { showToast('Txn date cannot be in the future', 'error'); return }
  const fd = new FormData()
  fd.append('amount', amount)
  fd.append('type', type)
  fd.append('note', note)
  if (file) fd.append('screenshot', file)
  const res = await fetch(`/api/members/${memberId}/submit_payment_request`, {method:'POST', body: fd})
  if (res.ok) {
    showToast(t('Submitted for approval'), 'success')
    renderMemberProfile(memberId)
  } else {
    const err = await res.json().catch(()=>({error:'failed'}))
    showToast(err.error || 'Submit failed', 'error')
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
