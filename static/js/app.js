const api = async (path, opts = {}) => {
  const headers = Object.assign({}, opts.headers || {})
  if (state.adminToken) headers['X-ADMIN-TOKEN'] = state.adminToken
  const res = await fetch('/api' + path, Object.assign({}, opts, {headers}))
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    if (res.status === 401 && err && err.error === 'session_expired') handleSessionExpired()
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

// Static map of member English names -> correct Kannada spellings (whole-name translation)
const KN_NAME_MAP = {
  'govindrao kulkarni': 'ಗೋವಿಂದರಾವ್ ಕುಲಕರ್ಣಿ',
  'bharat kulkarni': 'ಭರತ ಕುಲಕರ್ಣಿ',
  'bhargav kulkarni': 'ಭಾರ್ಗವ ಕುಲಕರ್ಣಿ',
  'sangeeta kulkarni': 'ಸಂಗೀತಾ ಕುಲಕರ್ಣಿ',
  'rohan kulkarni': 'ರೋಹನ ಕುಲಕರ್ಣಿ',
  'nachiket bhenki': 'ನಚಿಕೇತ ಭೇಂಕಿ',
  'indiresh joshi': 'ಇಂದಿರೇಶ ಜೋಷಿ',
  'kiran joshi': 'ಕಿರಣ ಜೋಷಿ',
  'suchiket bhenki': 'ಸುಚಿಕೇತ ಭೇಂಕಿ',
  'sanjeev joshi': 'ಸಂಜೀವ ಜೋಷಿ',
  'indira sarnad': 'ಇಂದಿರಾ ಸರನಾಡ್',
  'bhimbhatt bhenki': 'ಭೀಮಭಟ್ ಭೇಂಕಿ',
}

function kanName(name) {
  const key = String(name || '').trim().toLowerCase()
  return KN_NAME_MAP[key] || name
}

function mName(name) {
  return state.lang === 'kn' ? kanName(name) : String(name || '')
}

// Welcome overlay shown once right after login
function showWelcomeOverlay(name) {
  const existing = document.querySelector('.welcome-overlay')
  if (existing) existing.remove()
  const overlay = document.createElement('div')
  overlay.className = 'welcome-overlay'
  overlay.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-text">
        <div class="welcome-name">${t('Welcome,')} ${escHtml(name)}</div>
        <div class="welcome-name kn">ಸ್ವಾಗತ, ${escHtml(kanName(name))}</div>
      </div>
      <div class="welcome-gesture">🙏</div>
    </div>`
  document.body.appendChild(overlay)
  setTimeout(() => {
    overlay.classList.add('hide')
    setTimeout(() => overlay.remove(), 500)
  }, 2400)
}

// Loading spinner helpers
function setLoading(btn, loading) {
  if (!btn) return
  if (loading) {
    btn.disabled = true
    btn.classList.add('loading')
    btn._origHtml = btn.innerHTML
    btn.innerHTML = '<span class="spinner"></span>'
  } else {
    btn.disabled = false
    btn.classList.remove('loading')
    if (btn._origHtml) btn.innerHTML = btn._origHtml
  }
}

function loadingHtml() {
  return '<div style="display:flex;align-items:center;justify-content:center;padding:24px"><span class="spinner"></span></div>'
}

// Simple i18n map (English + simple Kannada for common people)
const I18N = {
  en: {
    'Welcome,': 'Welcome,',
    '📜 My Activity': '📜 My Activity',
    '📒 Passbook': '📒 Passbook',
    'Totals': 'Totals',
    'Admin Panel': 'Admin Panel',
    'Choose a section': 'Choose a section',
    'Pending Requests': 'Pending Requests',
    'Direct Entry': 'Direct Entry',
    '＋ Add New Member': '＋ Add New Member',
    'Export Report (PDF)': 'Export Report (PDF)',
    'Back': 'Back',
    'History': 'History',
    'Add Investment': 'Add Investment',
    'Approve or reject member requests.': 'Approve or reject member requests.',
    'Create a new member account.': 'Create a new member account.',
    'Record an auto-approved payment.': 'Record an auto-approved payment.',
    'Add income & expense records.': 'Add income & expense records.',
    'Active investments, schemes & history.': 'Active investments, schemes & history.',
    'Fix or delete a wrong entry.': 'Fix or delete a wrong entry.',
    'Download monthly or period summary PDF.': 'Download monthly or period summary PDF.',
    'Session expired. Please log in again.': 'Session expired. Please log in again.',
    'Logged out due to inactivity': 'Logged out due to inactivity',
    'You will be logged out soon due to inactivity.': 'You will be logged out soon due to inactivity.',
    "I'm here": "I'm here",
    'Login to SLV Finance': 'Login to SLV Finance',
    'Select Member': 'Select Member',
    'Login': 'Login',
    'Enter password': 'Enter password',
    'Password is needed': 'Password is needed',
    'Incorrect password': 'Incorrect password',
    '💰 Financial Overview': '💰 Financial Overview',
    'Total Collected': 'Total Collected',
    'Sum of all collection sources below (net of expenses).': 'Sum of all collection sources below (net of expenses).',
    'Entry Deposit:': 'Entry Deposit:',
    'Other Income:': 'Other Income:',
    'Fine:': 'Fine:',
    'Expenses:': 'Expenses:',
    'Loans Disbursed': 'Loans Disbursed',
    'Hardlock / FD': 'Hardlock / FD',
    'Available to Lend': 'Available to Lend',
    '📋 Group Information': '📋 Group Information',
    'Started': 'Started',
    'Members': 'Members',

    'Tenure': 'Tenure',
    'Loan Interest': 'Loan Interest',
    'FD Gain': 'FD Gain',
    'Loan Disbursed': 'Loan Disbursed',
    'Other Income': 'Other Income',
    'FD Deposit': 'FD Deposit',
    'Group Fund': 'Group Fund',
    'Insufficient funds': 'Insufficient funds',
    'Available': 'Available',
    'Requested': 'Requested',
    'Add failed': 'Add failed',
    'Download Backup': 'Download Backup',
    'Backup downloaded': 'Backup downloaded',
    'Download failed': 'Download failed',
    'Safety copies of all data are made daily. Download one to keep it outside the server.': 'Safety copies of all data are made daily. Download one to keep it outside the server.',
    '📊 Monthly & Yearly Summary': '📊 Monthly & Yearly Summary',
    'Monthly': 'Monthly',
    'Yearly': 'Yearly',

    'Loan Principal': 'Loan Principal',
    'Fine': 'Fine',
    'Set the full split for this member on this date.': 'Set the full split for this member on this date.',
    'No data for this period': 'No data for this period',
    '✏️ Edit / Correct Entries': '✏️ Edit / Correct Entries',
    'Find a wrong entry, fix its amount/date/member, or delete it.': 'Find a wrong entry, fix its amount/date/member, or delete it.',
    'All types': 'All types',
    'Share / Loan': 'Share / Loan',
    'Total': 'Total',
    'All members': 'All members',
    'Search member or description...': 'Search member or description...',
    'None': 'None',
    'No entries found.': 'No entries found.',
    'Select a type or member, or search, to show entries.': 'Select a type or member, or search, to show entries.',
    'Edit': 'Edit',
    'Delete': 'Delete',
    'Delete Entry': 'Delete Entry',
    'Delete this entry permanently?': 'Delete this entry permanently?',
    'Entry updated': 'Entry updated',
    'Entry deleted': 'Entry deleted',
    'Edit failed': 'Edit failed',
    'Delete failed': 'Delete failed',
    'Share': 'Share',
    'Entry Deposit': 'Entry Deposit',
    'Add New Member': 'Add New Member',
    'After adding, the member can fill in their details.': 'After adding, the member can fill in their details.',
    'Member name': 'Member name',
    'Phone (optional)': 'Phone (optional)',
    'Add Member': 'Add Member',
    'Approve loans from members after review.': 'Approve loans from members after review.',
    '🏦 FD Management': '🏦 FD Management',
    'FD Amount': 'FD Amount',
    'Start Date': 'Start Date',
    'End / Maturity': 'End / Maturity',
    'Interest Rate': 'Interest Rate',
    'Bank Name': 'Bank Name',
    'Add FD': 'Add FD',
    'Active': 'Active',
    'Record': 'Record',
    'FD No.': 'FD No.',
    'Show installments': 'Show installments',
    'Hide installments': 'Hide installments',
    'Income / Expenses': 'Income / Expenses',
    'Income (Gains)': 'Income (Gains)',
    'Expenses': 'Expenses',
    '+ Add Income': '+ Add Income',
    '+ Add Expense': '+ Add Expense',
    '− Cancel': '− Cancel',
    'Amount': 'Amount',
    'Date': 'Date',
    'Reason': 'Reason',
    'Save': 'Save',
    'Income': 'Income',
    'Expense': 'Expense',
    'Hardlock / Investment': 'Hardlock / Investment',
    'Date & Time': 'Date & Time',
    'Type': 'Type',
    'Member': 'Member',
    'From': 'From',
    'To': 'To',
    'Apply': 'Apply',
    'Clear column filter': 'Clear column filter',
    'Filter by Type': 'Filter by Type',
    'Filter by Member': 'Filter by Member',
    'Filter by Date Range': 'Filter by Date Range',
    'Filter by Amount': 'Filter by Amount',
    'Credit': 'Credit',
    'Debit': 'Debit',
    'Min amount': 'Min amount',
    'Max amount': 'Max amount',
    'Exact amount': 'Exact amount',
    'Min:': 'Min:',
    'Max:': 'Max:',
    'Exact: ₹': 'Exact: ₹',
    '✕ Clear all filters': '✕ Clear all filters',
    'Close FD': 'Close FD',
    'Confirm Close': 'Confirm Close',
    'Confirm Withdraw': 'Confirm Withdraw',
    'All your requests — payments, loan applications, and their statuses.': 'All your requests — payments, loan applications, and their statuses.',
    'All transactions in one place.': 'All transactions in one place.',
    'Withdraw': 'Withdraw',
    '▲ Ascending': '▲ Ascending',
    '▼ Descending': '▼ Descending',
    'All': 'All',
    'No entries match filters.': 'No entries match filters.',
    'Loading...': 'Loading...',
    'No income or expense entries yet.': 'No income or expense entries yet.',
    'Error loading transactions': 'Error loading transactions',
    'Error loading passbook': 'Error loading passbook',
    'Error loading FD entries': 'Error loading FD entries',
    'No FD entries yet.': 'No FD entries yet.',
    'No active FDs.': 'No active FDs.',
    'No closed FDs.': 'No closed FDs.',
    'Logging in...': 'Logging in...',
    'e.g. SBI': 'e.g. SBI',
    'e.g. Donation from X': 'e.g. Donation from X',
    'e.g. Meeting snacks': 'e.g. Meeting snacks',
    'Login failed. Check your name/password.': 'Login failed. Check your name/password.',
    'Dashboard': 'Dashboard',
    'My Profile': 'My Profile',
    'All Members': 'All Members',
    'Sign Out': 'Sign Out',
    'Enter a name': 'Enter a name',
    'Share requested': 'Share payment requested for approval',
    'Submitted for approval': 'Submitted for approval',
    'Loan applied': 'Loan applied and payment requested for approval',
    'Only admin': 'Only admin can approve loans.',
    'Enter amount': 'Enter amount',
    'Photo uploaded': 'Photo uploaded',
    'Upload failed': 'Upload failed',
    'Cancel': 'Cancel',
    'Confirm cancel?': 'Confirm cancel?',
    'Approved and active': 'Approved and active',
    'Rejected': 'Rejected',
    'Loan Application': 'Loan Application',
    'Approved on ': 'Approved on ',
    'Submitted': 'Submitted',

    'Combined Payment': 'Combined Payment',
    'Approved': 'Approved',
    'Cancelled': 'Cancelled',
    'No history yet': 'No history yet',
    'Status': 'Status',
    'Comments': 'Comments',
    'Approve': 'Approve',
    'Approve failed': 'Approve failed',
    'Payment approved': 'Payment approved',
    'Reject failed': 'Reject failed',
    'Payment rejected': 'Payment rejected',
    'Enter a reason': 'Enter a reason',
    'Reason for rejection...': 'Reason for rejection...',
    'Confirm Reject': 'Confirm Reject',
    '📎 Screenshot': '📎 Screenshot',
    'Error loading': 'Error loading',
    'Deleted': 'Deleted',
    'Edited': 'Edited',
    'No changes recorded yet.': 'No changes recorded yet.',
    'FD not found': 'FD not found',
    'FD closed. Interest added to Other Income.': 'FD closed. Interest added to Other Income.',
    'Enter valid FD amount': 'Enter valid FD amount',
    'Enter valid start date': 'Enter valid start date',
    'Enter valid maturity date': 'Enter valid maturity date',
    'Enter valid rate': 'Enter valid rate',
    'Maturity must be after start date': 'Maturity must be after start date',
    'FD added': 'FD added',
    'Enter valid return amount': 'Enter valid return amount',
    'Income recorded': 'Income recorded',
    'Expense recorded': 'Expense recorded',
    'Enter a valid amount': 'Enter a valid amount',
    'Loan': 'Loan',
    'for': 'for',
    'mo': 'mo',
    "'s loan approved": "'s loan approved",
    'Loan rejected': 'Loan rejected',
    'Start': 'Start',
    'Maturity': 'Maturity',
    'Rate': 'Rate',
    'Bank': 'Bank',
    'Interest': 'Interest',
    'Term': 'Term',
    'Interest / Return Amount': 'Interest / Return Amount',
    'Term too short': 'Term too short',
    'entries': 'entries',
    'You have unsaved information in forms.': 'You have unsaved information in forms.',
    'These will not be submitted.': 'These will not be submitted.',
    'Are you sure you want to logout?': 'Are you sure you want to logout?',
    'Create Account': 'Create Account',
    'Entry Deposit Amount': 'Entry Deposit Amount',
    'Entry Deposit Date': 'Entry Deposit Date',
    'Password': 'Password',
    'Set member password': 'Set member password',
    'View Profile': 'View Profile',
    'Change Password': 'Change Password',
    'View details': 'View details',
    'Hide details': 'Hide details',
    'My Account': 'My Account',
    'My Activity': 'My Activity',
    'Passbook': 'Passbook',
    'Your payments and active loans.': 'Your payments and active loans.',
    'Change your password': 'Change your password',
    'Current password': 'Current password',
    'New password': 'New password',
    'Confirm new password': 'Confirm new password',
    'Password changed': 'Password changed',
    'Passwords do not match': 'Passwords do not match',
    'Fill all fields': 'Fill all fields',
    'Reset Password': 'Reset Password',
    'Set a new password if a member forgets theirs.': 'Set a new password if a member forgets theirs.',
    'Select member': 'Select member',
    'Reset': 'Reset',
    'Password reset': 'Password reset',
    'Failed to change password': 'Failed to change password',
    'Confirm': 'Confirm',
    '📄 Export Report (PDF)': '📄 Export Report (PDF)',
    'Download a monthly or custom-period summary PDF to share with members.': 'Download a monthly or custom-period summary PDF to share with members.',
    'Custom period': 'Custom period',
    'Month': 'Month',
    '⬇ Export PDF': '⬇ Export PDF',
    'Generating...': 'Generating...',
    'Report downloaded': 'Report downloaded',
    'Export failed': 'Export failed',
    'Select a month': 'Select a month',
    'Select From and To dates': 'Select From and To dates',
    'To date must be on or after From date': 'To date must be on or after From date',
    'Add': 'Add',
    'Add monthly installments using the + button in Active section.': 'Add monthly installments using the + button in Active section.',
    'Approve or reject member requests after review.': 'Approve or reject member requests after review.',
    'Bank / Scheme': 'Bank / Scheme',
    'Close': 'Close',
    'Close Scheme': 'Close Scheme',
    'Closed Scheme': 'Closed Scheme',
    'Closed. Return added.': 'Closed. Return added.',
    'Create Scheme': 'Create Scheme',
    'Edit / Correct Entries': 'Edit / Correct Entries',
    'Enter at least share or loan amount': 'Enter at least share or loan amount',
    'Enter valid amount': 'Enter valid amount',
    'Entry not found': 'Entry not found',
    'Entry recorded successfully': 'Entry recorded successfully',
    'Error loading entries': 'Error loading entries',
    'Installment added': 'Installment added',
    'Installments': 'Installments',
    'Invested': 'Invested',
    'Investment added': 'Investment added',
    'Loan Request': 'Loan Request',
    'Loan approved': 'Loan approved',
    'Maturity must not be before start date': 'Maturity must not be before start date',
    'Monthly Scheme': 'Monthly Scheme',
    'No active entries.': 'No active entries.',
    'No closed entries.': 'No closed entries.',
    'No entries yet.': 'No entries yet.',
    'No installments yet': 'No installments yet',
    'No submitted requests yet.': 'No submitted requests yet.',
    'Note (optional)': 'Note (optional)',
    'One-time': 'One-time',
    'Payment': 'Payment',
    'Period': 'Period',
    'Provider': 'Provider',
    'Record payment on behalf of a member (auto-approved).': 'Record payment on behalf of a member (auto-approved).',
    'Reject': 'Reject',
    'Return': 'Return',
    'Return Amount': 'Return Amount',
    'Scheme Name': 'Scheme Name',
    'Scheme closed. Return added.': 'Scheme closed. Return added.',
    'Scheme created': 'Scheme created',
    'Select a date': 'Select a date',
    'Select a member': 'Select a member',
    'Submit': 'Submit',
    'Submit & Auto-Approve': 'Submit & Auto-Approve',
    'Total Amount': 'Total Amount',
    'Submit Proof of Payment': 'Submit Proof of Payment',
    '₹50/day after 10th': '₹50/day after 10th',
    'Payment Date': 'Payment Date',
    'Submit Payment for Approval': 'Submit Payment for Approval',
    'Submit Payment': 'Submit Payment',
    'Request Loan': 'Request Loan',
    'Loan Amount': 'Loan Amount',
    'Years': 'Years',
    'Months': 'Months',
    'year': 'year',
    'years': 'years',
    'month': 'month',
    'months': 'months',
    'Tap to upload receipt / proof': 'Tap to upload receipt / proof',
    'Image only': 'Image only',
    'Enter loan amount': 'Enter loan amount',
    'Select at least 1 month term': 'Select at least 1 month term',
    'Loan request submitted': 'Loan request submitted',
    'Select a payment date': 'Select a payment date',
    'Date cannot be in the future': 'Date cannot be in the future',
    'Share is required': 'Share is required',
    'Total Invested': 'Total Invested',
    'installments': 'installments',
  },
  kn: {
    'Welcome,': 'ಸ್ವಾಗತ,',
    '📜 My Activity': '📜 ನನ್ನ ಚಟುವಟಿಕೆ',
    '📒 Passbook': '📒 ಪಾಸ್‌ಬುಕ್',
    'Totals': 'ಒಟ್ಟು',
    'Admin Panel': 'ಆಡಳಿತ ಫಲಕ',
    'Choose a section': 'ಒಂದು ವಿಭಾಗವನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',
    'Pending Requests': 'ಬಾಕಿ ವಿನಂತಿಗಳು',
    'Direct Entry': 'ನೇರ ನಮೂದು',
    '＋ Add New Member': '＋ ಹೊಸ ಸದಸ್ಯರನ್ನು ಸೇರಿಸಿ',
    'Export Report (PDF)': 'ವರದಿ (PDF)',
    'Back': 'ಹಿಂದೆ',
    'History': 'ಇತಿಹಾಸ',
    'Add Investment': 'ಹೂಡಿಕೆ ಸೇರಿಸಿ',
    'Approve or reject member requests.': 'ಸದಸ್ಯರ ವಿನಂತಿಗಳನ್ನು ಅನುಮೋದಿಸಿ ಅಥವಾ ತಿರಸ್ಕರಿಸಿ.',
    'Create a new member account.': 'ಹೊಸ ಸದಸ್ಯರ ಖಾತೆಯನ್ನು ತೆರೆಯಿರಿ.',
    'Record an auto-approved payment.': 'ಸದಸ್ಯರ ಪರವಾಗಿ ಪಾವತಿ ದಾಖಲಿಸಿ (ಸ್ವಯಂ ಅನುಮೋದಿತ).',
    'Add income & expense records.': 'ಆದಾಯ ಮತ್ತು ಖರ್ಚಿನ ದಾಖಲೆಗಳನ್ನು ಸೇರಿಸಿ.',
    'Active investments, schemes & history.': 'ಸಕ್ರಿಯ ಹೂಡಿಕೆಗಳು ಮತ್ತು ದಾಖಲೆಗಳು.',
    'Fix or delete a wrong entry.': 'ತಪ್ಪಾದ ನಮೂದನ್ನು ಸರಿಪಡಿಸಿ ಅಥವಾ ಅಳಿಸಿ.',
    'Download monthly or period summary PDF.': 'ಮಾಸಿಕ ಅಥವಾ ಅವಧಿಯ ಸಾರಾಂಶ PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.',
    'Session expired. Please log in again.': 'ಅವಧಿ ಮೀರಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಲಾಗಿನ್ ಮಾಡಿ.',
    'Logged out due to inactivity': 'ಜಡತ್ವದಿಂದ ಲಾಗ್ ಔಟ್ ಮಾಡಲಾಗಿದೆ',
    'You will be logged out soon due to inactivity.': 'ಜಡತ್ವದಿಂದ ಶೀಘ್ರವೇ ಲಾಗ್ ಔಟ್ ಆಗುತ್ತದೆ.',
    "I'm here": 'ನಾನು ಇಲ್ಲಿದ್ದೇನೆ',
    'Login to SLV Finance': 'ಎಸ್‌ಎಲ್‌ವಿ ಫೈನಾನ್ಸ್‌ಗೆ ಲಾಗಿನ್ ಮಾಡಿ',
    'Select Member': 'ಸದಸ್ಯರನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',
    'Login': 'ಲಾಗಿನ್',
    'Enter password': 'ಪಾಸ್ವರ್ಡ್ ನಮೂದಿಸಿ',
    'Password is needed': 'ಪಾಸ್ವರ್ಡ್ ಅಗತ್ಯವಿದೆ',
    'Incorrect password': 'ತಪ್ಪು ಪಾಸ್ವರ್ಡ್',
    '💰 Financial Overview': '💰 ಹಣಕಾಸಿನ ಮಾಹಿತಿ',
    'Total Collected': 'ಒಟ್ಟು ಸಂಗ್ರಹ',
    'Sum of all collection sources below (net of expenses).': 'ಕೆಳಗಿನ ಎಲ್ಲಾ ಸಂಗ್ರಹ ಮೂಲಗಳ ಮೊತ್ತ (ಖರ್ಚು ಕಳೆದು).',
    'Entry Deposit:': 'ಪ್ರವೇಶ ಠೇವಣಿ:',
    'Other Income:': 'ಇತರೆ ಆದಾಯ:',
    'Fine:': 'ದಂಡ:',
    'Expenses:': 'ಖರ್ಚುಗಳು:',
    'Loans Disbursed': 'ನೀಡಿರುವ ಸಾಲ',
    'Hardlock / FD': 'ಹಾರ್ಡ್‌ಲಾಕ್ / ಎಫ್‌ಡಿ',
    'Available to Lend': 'ಸಾಲ ಕೊಡಲು ಲಭ್ಯ',
    '📋 Group Information': '📋 ಗುಂಪಿನ ಮಾಹಿತಿ',
    'Started': 'ಪ್ರಾರಂಭ',
    'Members': 'ಸದಸ್ಯರು',
    'Tenure': 'ಅವಧಿ',
    'Loan Interest': 'ಸಾಲದ ಬಡ್ಡಿ',
    'FD Gain': 'ಎಫ್‌ಡಿ ಲಾಭ',
    'Loan Disbursed': 'ಸಾಲ ನೀಡಲಾಗಿದೆ',
    'Other Income': 'ಇತರ ಆದಾಯ',
    'FD Deposit': 'ಎಫ್‌ಡಿ ಠೇವಣಿ',
    'Group Fund': 'ಗುಂಪು ನಿಧಿ',
    'Insufficient funds': 'ಹಣ ಸಾಲದು',
    'Available': 'ಲಭ್ಯವಿರುವ ಹಣ',
    'Requested': 'ಕೇಳಿದ ಹಣ',
    'Add failed': 'ಸೇರಿಸಲು ವಿಫಲವಾಗಿದೆ',
    'Download Backup': 'ಬ್ಯಾಕಪ್ ಡೌನ್‌ಲೋಡ್',
    'Backup downloaded': 'ಬ್ಯಾಕಪ್ ಡೌನ್‌ಲೋಡ್ ಆಗಿದೆ',
    'Download failed': 'ಡೌನ್‌ಲೋಡ್ ವಿಫಲವಾಗಿದೆ',
    'Safety copies of all data are made daily. Download one to keep it outside the server.': 'ಎಲ್ಲಾ ದತ್ತಾಂಶದ ಸುರಕ್ಷಿತ ಪ್ರತಿಗಳು ದೈನಂದಿನ ಮಾಡಲಾಗುತ್ತದೆ. ಸರ್ವರ್ ಹೊರಗೆ ಇಡಲು ಒಂದನ್ನು ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.',
    '📊 Monthly & Yearly Summary': '📊 ಮಾಸಿಕ ಮತ್ತು ವಾರ್ಷಿಕ ಸಾರಾಂಶ',
    'Monthly': 'ಮಾಸಿಕ',
    'Yearly': 'ವಾರ್ಷಿಕ',
    'Loan Principal': 'ಸಾಲದ ಮೂಲಬಂಡವಾಳ',
    'Fine': 'ದಂಡ',
    'Set the full split for this member on this date.': 'ಈ ದಿನಾಂಕದ ಈ ಸದಸ್ಯರ ಸಂಪೂರ್ಣ ವಿಭಾಗವನ್ನು ಹೊಂದಿಸಿ.',
    'No data for this period': 'ಈ ಅವಧಿಗೆ ಯಾವುದೇ ದತ್ತಾಂಶವಿಲ್ಲ',
    '✏️ Edit / Correct Entries': '✏️ ನಮೂದುಗಳನ್ನು ಸರಿಪಡಿಸಿ',
    'Find a wrong entry, fix its amount/date/member, or delete it.': 'ತಪ್ಪಾದ ನಮೂದನ್ನು ಹುಡುಕಿ, ಅದರ ಮೊತ್ತ/ದಿನಾಂಕ/ಸದಸ್ಯರನ್ನು ಸರಿಪಡಿಸಿ, ಅಥವಾ ಅಳಿಸಿ.',
    'All types': 'ಎಲ್ಲಾ ಪ್ರಕಾರಗಳು',
    'Share / Loan': 'ಷೇರು / ಸಾಲ',
    'Total': 'ಒಟ್ಟು',
    'All members': 'ಎಲ್ಲಾ ಸದಸ್ಯರು',
    'Search member or description...': 'ಸದಸ್ಯ ಅಥವಾ ವಿವರಣೆ ಹುಡುಕಿ...',
    'None': 'ಯಾವುದೂ ಇಲ್ಲ',
    'No entries found.': 'ಯಾವುದೇ ನಮೂದುಗಳು ಕಂಡುಬಂದಿಲ್ಲ.',
    'Select a type or member, or search, to show entries.': 'ನಮೂದುಗಳನ್ನು ತೋರಿಸಲು ಪ್ರಕಾರ ಅಥವಾ ಸದಸ್ಯರನ್ನು ಆಯ್ಕೆಮಾಡಿ, ಅಥವಾ ಹುಡುಕಿ.',
    'Edit': 'ಸರಿಪಡಿಸಿ',
    'Delete': 'ಅಳಿಸಿ',
    'Delete Entry': 'ನಮೂದನ್ನು ಅಳಿಸಿ',
    'Delete this entry permanently?': 'ಈ ನಮೂದನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸುವುದೇ?',
    'Entry updated': 'ನಮೂದು ನವೀಕರಿಸಲಾಗಿದೆ',
    'Entry deleted': 'ನಮೂದು ಅಳಿಸಲಾಗಿದೆ',
    'Edit failed': 'ಸರಿಪಡಿಸಲು ವಿಫಲವಾಗಿದೆ',
    'Delete failed': 'ಅಳಿಸಲು ವಿಫಲವಾಗಿದೆ',
    'Share': 'ಷೇರು',
    'Entry Deposit': 'ಪ್ರವೇಶ ಠೇವಣಿ',
    'Add New Member': 'ಹೊಸ ಸದಸ್ಯರನ್ನು ಸೇರಿಸಿ',
    'After adding, the member can fill in their details.': 'ಸೇರಿಸಿದ ನಂತರ, ಸದಸ್ಯರು ತಮ್ಮ ವಿವರಗಳನ್ನು ತುಂಬಬಹುದು.',
    'Member name': 'ಸದಸ್ಯರ ಹೆಸರು',
    'Phone (optional)': 'ಫೋನ್ (ಐಚ್ಛಿಕ)',
    'Add Member': 'ಸದಸ್ಯರನ್ನು ಸೇರಿಸಿ',
    'Approve loans from members after review.': 'ಸದಸ್ಯರ ಸಾಲಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಅನುಮೋದಿಸಿ.',
    '🏦 FD Management': '🏦 ಎಫ್‌ಡಿ ನಿರ್ವಹಣೆ',
    'FD Amount': 'ಎಫ್‌ಡಿ ಮೊತ್ತ',
    'Start Date': 'ಪ್ರಾರಂಭ ದಿನಾಂಕ',
    'End / Maturity': 'ಅಂತ್ಯ / ಮೆಚೂರಿಟಿ',
    'Interest Rate': 'ಬಡ್ಡಿ ದರ',
    'Bank Name': 'ಬ್ಯಾಂಕ್ ಹೆಸರು',
    'Add FD': 'ಎಫ್‌ಡಿ ಸೇರಿಸಿ',
    'Active': 'ಸಕ್ರಿಯ',
    'Record': 'ದಾಖಲೆ',
    'FD No.': 'ಎಫ್‌ಡಿ ಸಂಖ್ಯೆ',
    'Show installments': 'ಕಂತುಗಳನ್ನು ತೋರಿಸಿ',
    'Hide installments': 'ಕಂತುಗಳನ್ನು ಮರೆಮಾಡಿ',
    'Income / Expenses': 'ಆದಾಯ / ಖರ್ಚು',
    'Income (Gains)': 'ಆದಾಯ',
    'Expenses': 'ಖರ್ಚುಗಳು',
    '+ Add Income': '+ ಆದಾಯ ಸೇರಿಸಿ',
    '+ Add Expense': '+ ಖರ್ಚು ಸೇರಿಸಿ',
    '− Cancel': '− ರದ್ದು',
    'Amount': 'ಮೊತ್ತ',
    'Date': 'ದಿನಾಂಕ',
    'Reason': 'ಕಾರಣ',
    'Save': 'ಉಳಿಸಿ',
    'Income': 'ಆದಾಯ',
    'Expense': 'ಖರ್ಚು',
    'Hardlock / Investment': 'ಹಾರ್ಡ್‌ಲಾಕ್ / ಹೂಡಿಕೆ',
    'Date & Time': 'ದಿನಾಂಕ ಮತ್ತು ಸಮಯ',
    'Type': 'ಪ್ರಕಾರ',
    'Member': 'ಸದಸ್ಯ',
    'From': 'ಇಂದ',
    'To': 'ವರೆಗೆ',
    'Apply': 'ಅನ್ವಯಿಸು',
    'Clear column filter': 'ಕಾಲಮ್ ಫಿಲ್ಟರ್ ತೆಗೆದುಹಾಕಿ',
    'Filter by Type': 'ಪ್ರಕಾರದಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ',
    'Filter by Member': 'ಸದಸ್ಯರಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ',
    'Filter by Date Range': 'ದಿನಾಂಕ ವ್ಯಾಪ್ತಿಯಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ',
    'Filter by Amount': 'ಮೊತ್ತದಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ',
    'Credit': 'ಜಮಾ',
    'Debit': 'ಖರ್ಚು',
    'Min amount': 'ಕಡಿಮೆ ಮೊತ್ತ',
    'Max amount': 'ಹೆಚ್ಚು ಮೊತ್ತ',
    'Exact amount': 'ನಿಖರ ಮೊತ್ತ',
    'Min:': 'ಕಡಿಮೆ:',
    'Max:': 'ಹೆಚ್ಚು:',
    'Exact: ₹': 'ನಿಖರ: ₹',
    '✕ Clear all filters': '✕ ಎಲ್ಲಾ ಫಿಲ್ಟರ್ ತೆಗೆದುಹಾಕಿ',
    'Close FD': 'ಎಫ್‌ಡಿ ಮುಚ್ಚಿ',
    'Confirm Close': 'ಮುಚ್ಚುವುದನ್ನು ಖಚಿತಪಡಿಸಿ',
    'All your requests — payments, loan applications, and their statuses.': 'ನಿಮ್ಮ ಎಲ್ಲಾ ವಿನಂತಿಗಳು — ಪಾವತಿಗಳು, ಸಾಲದ ಅರ್ಜಿಗಳು ಮತ್ತು ಅವುಗಳ ಸ್ಥಿತಿ.',
    'All transactions in one place.': 'ಎಲ್ಲಾ ವಹಿವಾಟುಗಳು ಒಂದೇ ಸ್ಥಳದಲ್ಲಿ.',
    '▲ Ascending': '▲ ಏರಿಕೆ',
    '▼ Descending': '▼ ಇಳಿಕೆ',
    'All': 'ಎಲ್ಲಾ',
    'No entries match filters.': 'ಫಿಲ್ಟರ್‌ಗೆ ಹೊಂದಾಣಿಕೆಯ ನಮೂದುಗಳಿಲ್ಲ.',
    'Loading...': 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...',
    'No income or expense entries yet.': 'ಇನ್ನೂ ಆದಾಯ ಅಥವಾ ಖರ್ಚು ನಮೂದುಗಳಿಲ್ಲ.',
    'Error loading transactions': 'ವಹಿವಾಟುಗಳನ್ನು ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ',
    'Error loading passbook': 'ಪಾಸ್‌ಬುಕ್ ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ',
    'Error loading FD entries': 'ಎಫ್‌ಡಿ ನಮೂದುಗಳನ್ನು ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ',
    'No FD entries yet.': 'ಇನ್ನೂ ಎಫ್‌ಡಿ ನಮೂದುಗಳಿಲ್ಲ.',
    'No active FDs.': 'ಸಕ್ರಿಯ ಎಫ್‌ಡಿಗಳಿಲ್ಲ.',
    'No closed FDs.': 'ಎಫ್‌ಡಿಗಳಿಲ್ಲ.',
    'Logging in...': 'ಲಾಗಿನ್ ಆಗುತ್ತಿದೆ...',
    'e.g. SBI': 'ಉದಾ: ಎಸ್‌ಬಿಐ',
    'e.g. Donation from X': 'ಉದಾ: X ರಿಂದ ದೇಣಿಗೆ',
    'e.g. Meeting snacks': 'ಉದಾ: ಸಭೆ ತಿಂಡಿ',
    'Login failed. Check your name/password.': 'ಲಾಗಿನ್ ವಿಫಲ. ನಿಮ್ಮ ಹೆಸರು/ಪಾಸ್ವರ್ಡ್ ಪರಿಶೀಲಿಸಿ.',
    'Dashboard': 'ಮುಖಪುಟ',
    'My Profile': 'ನನ್ನ ಪ್ರೊಫೈಲ್',
    'All Members': 'ಎಲ್ಲಾ ಸದಸ್ಯರು',
    'Sign Out': 'ನಿರ್ಗಮಿಸಿ',
    'Enter a name': 'ಹೆಸರನ್ನು ನಮೂದಿಸಿ',
    'Share requested': 'ಷೇರು ಪಾವತಿ ಅನುಮೋದನೆಗೆ ವಿನಂತಿಸಲಾಗಿದೆ',
    'Submitted for approval': 'ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಲಾಗಿದೆ',
    'Loan applied': 'ಸಾಲ ಮತ್ತು ಪಾವತಿ ಅನುಮೋದನೆಗೆ ವಿನಂತಿಸಲಾಗಿದೆ',
    'Only admin': 'ಆಡಳಿತಗಾರರು ಮಾತ್ರ ಅನುಮೋದಿಸಬಹುದು.',
    'Enter loan amount': 'ಸಾಲದ ಮೊತ್ತ ನಮೂದಿಸಿ',
    'Enter amount': 'ಮೊತ್ತ ನಮೂದಿಸಿ',
    'Photo uploaded': 'ಫೋಟೋ ಅಪ್ಲೋಡ್ ಆಯಿತು',
    'Upload failed': 'ಅಪ್ಲೋಡ್ ವಿಫಲವಾಗಿದೆ',
    'Cancel': 'ರದ್ದುಮಾಡಿ',
    'Confirm cancel?': 'ರದ್ದುಗೊಳಿಸುವುದೇ?',
    'Approved and active': 'ಅನುಮೋದಿಸಲಾಗಿದೆ',
    'Rejected': 'ತಿರಸ್ಕರಿಸಲಾಗಿದೆ',
    'Loan Application': 'ಸಾಲದ ಅರ್ಜಿ',
    'Approved on ': 'ಅನುಮೋದಿಸಿದ ದಿನ ',
    'Submitted': 'ಸಲ್ಲಿಸಲಾಗಿದೆ',
    'Combined Payment': 'ಸಂಯೋಜಿತ ಪಾವತಿ',
    'Approved': 'ಅನುಮೋದಿಸಲಾಗಿದೆ',
    'Cancelled': 'ರದ್ದಾಗಿದೆ',
    'No history yet': 'ಇನ್ನೂ ಇತಿಹಾಸವಿಲ್ಲ',
    'Status': 'ಸ್ಥಿತಿ',
    'Comments': 'ಟಿಪ್ಪಣಿ',
    'Approve': 'ಅನುಮೋದಿಸಿ',
    'Approve failed': 'ಅನುಮೋದನೆ ವಿಫಲ',
    'Payment approved': 'ಪಾವತಿ ಅನುಮೋದಿಸಲಾಗಿದೆ',
    'Reject failed': 'ತಿರಸ್ಕರಿಸುವಲ್ಲಿ ವಿಫಲ',
    'Payment rejected': 'ಪಾವತಿ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ',
    'Enter a reason': 'ಕಾರಣ ನಮೂದಿಸಿ',
    'Reason for rejection...': 'ತಿರಸ್ಕರಿಸಲು ಕಾರಣ...',
    'Confirm Reject': 'ತಿರಸ್ಕರಿಸುವುದನ್ನು ಖಚಿತಪಡಿಸಿ',
    '📎 Screenshot': '📎 ಸ್ಕ್ರೀನ್ಶಾಟ್',
    'Error loading': 'ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ',
    'Deleted': 'ಅಳಿಸಲಾಗಿದೆ',
    'Edited': 'ಸಂಪಾದಿಸಲಾಗಿದೆ',
    'No changes recorded yet.': 'ಇನ್ನೂ ಬದಲಾವಣೆಗಳಿಲ್ಲ.',
    'FD not found': 'ಎಫ್‌ಡಿ ಕಂಡುಬಂದಿಲ್ಲ',
    'FD closed. Interest added to Other Income.': 'ಎಫ್‌ಡಿ ಮುಚ್ಚಲಾಗಿದೆ. ಬಡ್ಡಿಯನ್ನು ಇತರೆ ಆದಾಯಕ್ಕೆ ಸೇರಿಸಲಾಗಿದೆ.',
    'Enter valid FD amount': 'ಸರಿಯಾದ ಎಫ್‌ಡಿ ಮೊತ್ತ ನಮೂದಿಸಿ',
    'Enter valid start date': 'ಸರಿಯಾದ ಪ್ರಾರಂಭ ದಿನಾಂಕ ನಮೂದಿಸಿ',
    'Enter valid maturity date': 'ಸರಿಯಾದ ಮೆಚೂರಿಟಿ ದಿನಾಂಕ ನಮೂದಿಸಿ',
    'Enter valid rate': 'ಸರಿಯಾದ ಬಡ್ಡಿ ದರ ನಮೂದಿಸಿ',
    'Maturity must be after start date': 'ಮೆಚೂರಿಟಿ ಪ್ರಾರಂಭ ದಿನಾಂಕದ ನಂತರ ಇರಬೇಕು',
    'FD added': 'ಎಫ್‌ಡಿ ಸೇರಿಸಲಾಗಿದೆ',
    'Enter valid return amount': 'ಸರಿಯಾದ ಬಡ್ಡಿ ಮೊತ್ತ ನಮೂದಿಸಿ',
    'Income recorded': 'ಆದಾಯ ದಾಖಲಿಸಲಾಗಿದೆ',
    'Expense recorded': 'ಖರ್ಚು ದಾಖಲಿಸಲಾಗಿದೆ',
    'Enter a valid amount': 'ಸರಿಯಾದ ಮೊತ್ತ ನಮೂದಿಸಿ',
    'Loan': 'ಸಾಲ',
    'for': 'ಗೆ',
    'mo': 'ತಿಂಗಳು',
    "'s loan approved": " ರ ಸಾಲ ಅನುಮೋದಿಸಲಾಗಿದೆ",
    'Loan rejected': 'ಸಾಲ ತಿರಸ್ಕರಿಸಲಾಗಿದೆ',
    'Start': 'ಪ್ರಾರಂಭ',
    'Maturity': 'ಮೆಚೂರಿಟಿ',
    'Rate': 'ದರ',
    'Bank': 'ಬ್ಯಾಂಕ್',
    'Interest': 'ಬಡ್ಡಿ',
    'Term': 'ಅವಧಿ',
    'Interest / Return Amount': 'ಬಡ್ಡಿ / ಮರುಪಾವತಿ ಮೊತ್ತ',
    'Term too short': 'ಅವಧಿ ತುಂಬಾ ಕಡಿಮೆ',
    'entries': 'ನಮೂದುಗಳು',
    'You have unsaved information in forms.': 'ಫಾರ್ಮ್‌ಗಳಲ್ಲಿ ಉಳಿಸದ ಮಾಹಿತಿ ಇದೆ.',
    'These will not be submitted.': 'ಇವುಗಳು ಸಲ್ಲಿಕೆಯಾಗುವುದಿಲ್ಲ.',
    'Are you sure you want to logout?': 'ನೀವು ಖಚಿತವಾಗಿ ನಿರ್ಗಮಿಸಲು ಬಯಸುವಿರಾ?',
    'Create Account': 'ಖಾತೆ ರಚಿಸಿ',
    'Entry Deposit Amount': 'ಪ್ರವೇಶ ಠೇವಣಿ ಮೊತ್ತ',
    'Entry Deposit Date': 'ಪ್ರವೇಶ ಠೇವಣಿ ದಿನಾಂಕ',
    'Password': 'ಪಾಸ್‌ವರ್ಡ್',
    'Set member password': 'ಸದಸ್ಯರ ಪಾಸ್‌ವರ್ಡ್ ಹೊಂದಿಸಿ',
    'View Profile': 'ಪ್ರೊಫೈಲ್ ವೀಕ್ಷಿಸಿ',
    'Change Password': 'ಪಾಸ್‌ವರ್ಡ್ ಬದಲಾಯಿಸಿ',
    'View details': 'ವಿವರಗಳನ್ನು ನೋಡಿ',
    'Hide details': 'ವಿವರಗಳನ್ನು ಮರೆಮಾಡಿ',
    'My Account': 'ನನ್ನ ಖಾತೆ',
    'My Activity': 'ನನ್ನ ಚಟುವಟಿಕೆ',
    'Passbook': 'ಪಾಸ್‌ಬುಕ್',
    'Your payments and active loans.': 'ನಿಮ್ಮ ಪಾವತಿಗಳು ಮತ್ತು ಸಕ್ರಿಯ ಸಾಲಗಳು.',
    'Change your password': 'ನಿಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ಬದಲಾಯಿಸಿ',
    'Current password': 'ಪ್ರಸ್ತುತ ಪಾಸ್‌ವರ್ಡ್',
    'New password': 'ಹೊಸ ಪಾಸ್‌ವರ್ಡ್',
    'Confirm new password': 'ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ದೃಢೀಕರಿಸಿ',
    'Password changed': 'ಪಾಸ್‌ವರ್ಡ್ ಬದಲಾಗಿದೆ',
    'Passwords do not match': 'ಪಾಸ್‌ವರ್ಡ್ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ',
    'Fill all fields': 'ಎಲ್ಲಾ ಕ್ಷೇತ್ರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ',
    'Reset Password': 'ಪಾಸ್‌ವರ್ಡ್ ಮರುಹೊಂದಿಸಿ',
    'Set a new password if a member forgets theirs.': 'ಯಾವುದಾದರೂ ಸದಸ್ಯರು ತಮ್ಮ ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿದ್ದರೆ ಹೊಸ ಪಾಸ್‌ವರ್ಡ್ ಹೊಂದಿಸಿ.',
    'Select member': 'ಸದಸ್ಯರನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    'Reset': 'ಮರುಹೊಂದಿಸಿ',
    'Password reset': 'ಪಾಸ್‌ವರ್ಡ್ ಮರುಹೊಂದಾಣಿಕೆಯಾಗಿದೆ',
    'Failed to change password': 'ಪಾಸ್‌ವರ್ಡ್ ಬದಲಾಯಿಸಲು ವಿಫಲವಾಗಿದೆ',
    'Confirm': 'ಖಚಿತಪಡಿಸಿ',
    '📄 Export Report (PDF)': '📄 ವರದಿ ರಫ್ತು (PDF)',
    'Download a monthly or custom-period summary PDF to share with members.': 'ಸದಸ್ಯರೊಂದಿಗೆ ಹಂಚಿಕೊಳ್ಳಲು ಮಾಸಿಕ ಅಥವಾ ಆಯ್ದ ಅವಧಿಯ ಸಾರಾಂಶ PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ.',
    'Custom period': 'ಆಯ್ದ ಅವಧಿ',
    'Month': 'ತಿಂಗಳು',
    '⬇ Export PDF': '⬇ PDF ರಫ್ತು',
    'Generating...': 'ತಯಾರಿಸಲಾಗುತ್ತಿದೆ...',
    'Report downloaded': 'ವರದಿ ಡೌನ್‌ಲೋಡ್ ಆಯಿತು',
    'Export failed': 'ರಫ್ತು ವಿಫಲವಾಗಿದೆ',
    'Select a month': 'ತಿಂಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',
    'Select From and To dates': 'ಇಂದ ಮತ್ತು ವರೆಗೆ ದಿನಾಂಕಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',
    'To date must be on or after From date': 'ವರೆಗೆ ದಿನಾಂಕವು ಇಂದ ದಿನಾಂಕದ ನಂತರ ಅಥವಾ ಅದೇ ದಿನ ಇರಬೇಕು',
    'Add': 'ಸೇರಿಸಿ',
    'Add monthly installments using the + button in Active section.': 'ಸಕ್ರಿಯ ವಿಭಾಗದಲ್ಲಿ + ಬಟನ್ ಬಳಸಿ ಮಾಸಿಕ ಕಂತುಗಳನ್ನು ಸೇರಿಸಿ.',
    'Approve or reject member requests after review.': 'ಪರಿಶೀಲಿಸಿದ ನಂತರ ಸದಸ್ಯರ ವಿನಂತಿಗಳನ್ನು ಅಂಗೀಕರಿಸಿ ಅಥವಾ ತಿರಸ್ಕರಿಸಿ.',
    'Bank / Scheme': 'ಬ್ಯಾಂಕ್ / ಯೋಜನೆ',
    'Close': 'ಮುಚ್ಚಿ',
    'Close Scheme': 'ಯೋಜನೆ ಮುಚ್ಚಿ',
    'Closed Scheme': 'ಮುಚ್ಚಿದ ಯೋಜನೆ',
    'Closed. Return added.': 'ಮುಚ್ಚಲಾಗಿದೆ. ವಾಪಸಾತಿ ಸೇರಿಸಲಾಗಿದೆ.',
    'Create Scheme': 'ಯೋಜನೆ ರಚಿಸಿ',
    'Edit / Correct Entries': 'ನಮೂದುಗಳನ್ನು ಸರಿಪಡಿಸಿ',
    'Enter at least share or loan amount': 'ಕನಿಷ್ಠ ಷೇರು ಅಥವಾ ಸಾಲದ ಮೊತ್ತವನ್ನು ನಮೂದಿಸಿ',
    'Enter valid amount': 'ಸರಿಯಾದ ಮೊತ್ತವನ್ನು ನಮೂದಿಸಿ',
    'Entry not found': 'ನಮೂದು ಸಿಗಲಿಲ್ಲ',
    'Entry recorded successfully': 'ನಮೂದು ಯಶಸ್ವಿಯಾಗಿ ದಾಖಲಾಗಿದೆ',
    'Error loading entries': 'ನಮೂದುಗಳನ್ನು ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ',
    'Installment added': 'ಕಂತು ಸೇರಿಸಲಾಗಿದೆ',
    'Installments': 'ಕಂತುಗಳು',
    'Invested': 'ಹೂಡಿಕೆ',
    'Investment added': 'ಹೂಡಿಕೆ ಸೇರಿಸಲಾಗಿದೆ',
    'Loan Request': 'ಸಾಲದ ವಿನಂತಿ',
    'Loan approved': 'ಸಾಲ ಅಂಗೀಕೃತವಾಗಿದೆ',
    'Maturity must not be before start date': 'ಮುಕ್ತಾಯ ದಿನಾಂಕವು ಪ್ರಾರಂಭ ದಿನಾಂಕಕ್ಕಿಂತ ಮೊದಲಾಗಬಾರದು',
    'Monthly Scheme': 'ಮಾಸಿಕ ಯೋಜನೆ',
    'No active entries.': 'ಸಕ್ರಿಯ ನಮೂದುಗಳಿಲ್ಲ.',
    'No closed entries.': 'ಮುಚ್ಚಿದ ನಮೂದುಗಳಿಲ್ಲ.',
    'No entries yet.': 'ಇನ್ನೂ ನಮೂದುಗಳಿಲ್ಲ.',
    'No installments yet': 'ಇನ್ನೂ ಕಂತುಗಳಿಲ್ಲ',
    'No submitted requests yet.': 'ಇನ್ನೂ ಸಲ್ಲಿಸಿದ ವಿನಂತಿಗಳಿಲ್ಲ.',
    'Note (optional)': 'ಟಿಪ್ಪಣಿ (ಐಚ್ಛಿಕ)',
    'One-time': 'ಒಂದೇ ಬಾರಿ',
    'Payment': 'ಪಾವತಿ',
    'Period': 'ಅವಧಿ',
    'Provider': 'ಒದಗಿಸುವವರು',
    'Record payment on behalf of a member (auto-approved).': 'ಸದಸ್ಯರ ಪರವಾಗಿ ಪಾವತಿ ದಾಖಲಿಸಿ (ಸ್ವಯಂ ಅಂಗೀಕೃತ).',
    'Reject': 'ತಿರಸ್ಕರಿಸಿ',
    'Return': 'ವಾಪಸಾತಿ',
    'Return Amount': 'ವಾಪಸಾತಿ ಮೊತ್ತ',
    'Scheme Name': 'ಯೋಜನೆಯ ಹೆಸರು',
    'Scheme closed. Return added.': 'ಯೋಜನೆ ಮುಚ್ಚಲಾಗಿದೆ. ವಾಪಸಾತಿ ಸೇರಿಸಲಾಗಿದೆ.',
    'Scheme created': 'ಯೋಜನೆ ರಚಿಸಲಾಗಿದೆ',
    'Select a date': 'ದಿನಾಂಕ ಆಯ್ಕೆಮಾಡಿ',
    'Select a member': 'ಸದಸ್ಯರನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    'Submit': 'ಸಲ್ಲಿಸಿ',
    'Submit & Auto-Approve': 'ಸಲ್ಲಿಸಿ ಮತ್ತು ಸ್ವಯಂ ಅಂಗೀಕರಿಸಿ',
    'Total Amount': 'ಒಟ್ಟು ಮೊತ್ತ',
    'Submit Proof of Payment': 'ಪಾವತಿಯ ಪುರಾವೆ ಸಲ್ಲಿಸಿ',
    '₹50/day after 10th': '10 ನೇ ದಿನಾಂಕದ ನಂತರ ದಿನಕ್ಕೆ ₹50',
    'Payment Date': 'ಪಾವತಿ ದಿನಾಂಕ',
    'Submit Payment for Approval': 'ಅನುಮೋದನೆಗಾಗಿ ಪಾವತಿ ಸಲ್ಲಿಸಿ',
    'Submit Payment': 'ಪಾವತಿ ಸಲ್ಲಿಸಿ',
    'Request Loan': 'ಸಾಲ ಕೋರಿ',
    'Loan Amount': 'ಸಾಲದ ಮೊತ್ತ',
    'Years': 'ವರ್ಷಗಳು',
    'Months': 'ತಿಂಗಳುಗಳು',
    'year': 'ವರ್ಷ',
    'years': 'ವರ್ಷಗಳು',
    'month': 'ತಿಂಗಳು',
    'months': 'ತಿಂಗಳುಗಳು',
    'Tap to upload receipt / proof': 'ರಶೀದಿ / ಪುರಾವೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
    'Image only': 'ಚಿತ್ರ ಮಾತ್ರ',
    'Select at least 1 month term': 'ಕನಿಷ್ಠ 1 ತಿಂಗಳ ಅವಧಿ ಆಯ್ಕೆಮಾಡಿ',
    'Loan request submitted': 'ಸಾಲದ ವಿನಂತಿ ಸಲ್ಲಿಸಲಾಗಿದೆ',
    'Select a payment date': 'ಪಾವತಿ ದಿನಾಂಕವನ್ನು ಆಯ್ಕೆಮಾಡಿ',
    'Date cannot be in the future': 'ದಿನಾಂಕವು ಭವಿಷ್ಯದ್ದಾಗಿರಬಾರದು',
    'Share is required': 'ಷೇರು ಕಡ್ಡಾಯ',
    'Total Invested': 'ಒಟ್ಟು ಹೂಡಿಕೆ',
    'installments': 'ಕಂತುಗಳು',
    'Withdraw': 'ಹಿಂತೆಗೆದುಕೊಳ್ಳಿ',
    'Confirm Withdraw': 'ಹಿಂತೆಗೆದುಕೊಳ್ಳುವುದನ್ನು ಖಚಿತಪಡಿಸಿ',
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
  const lt = e.target && e.target.closest ? e.target.closest('#lang-toggle') : null
  if (lt) {
    state.lang = state.lang === 'en' ? 'kn' : 'en'
    const label = lt.querySelector('.lang-loop-label')
    if (label) label.textContent = state.lang === 'kn' ? 'EN' : 'ಕನ್ನಡ'
    translatePage()
    if (state.currentUser) renderView()
  }
})

function translatePage() {
  const els = document.querySelectorAll('[data-i18n]')
  els.forEach(el => el.textContent = t(el.dataset.i18n))
  // translate login fields
  const labels = document.querySelectorAll('.login-fields label')
  if (labels[0]) labels[0].textContent = t('Select Member')
  if (labels[1]) labels[1].textContent = t('Password')
  const pin = document.getElementById('admin-pin')
  if (pin) pin.placeholder = t('Enter password')
  const btn = document.getElementById('login-button')
  if (btn) btn.textContent = t('Login')
}

let topbar = null
let mainScreen = null
let menuLinks = null
let content = null
let memberSelect = null
let adminPin = null
let loginButton = null
let loginError = null

function showScreen(screenId) {
  mainScreen.classList.add('hidden')
  if (screenId === 'login') {
    topbar.classList.add('login-mode')
  } else {
    topbar.classList.remove('login-mode')
    mainScreen.classList.remove('hidden')
  }
}

function formatCurrency(amount) {
  return '₹' + Number(amount || 0).toLocaleString('en-IN', {maximumFractionDigits: 2})
}

function escHtml(str) {
  if (!str) return ''
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
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
  function format() {
    let start = this.selectionStart
    let raw = this.value.replace(/,/g, '')
    let formatted = toIndianNumber(raw)
    let added = formatted.length - this.value.length
    this.value = formatted
    this.setSelectionRange(start + added, start + added)
  }
  input.addEventListener('input', format)
  // format immediately for initial values
  format.call(input)
}

function formatDate(d) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'})
}

function formatDateCompact(d) {
  if (!d) return '-'
  const dt = new Date(d)
  const dd = String(dt.getDate()).padStart(2, '0')
  const mon = dt.toLocaleDateString('en-IN', {month: 'short'})
  return `${dd} ${mon}<br>${dt.getFullYear()}`
}

function formatDateTime(d) {
  if (!d) return '-'
  const dt = new Date(d)
  return dt.toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'})
    + ' ' + dt.toLocaleTimeString('en-IN', {hour: '2-digit', minute: '2-digit'})
}

function formatDateParts(d) {
  if (!d) return { date: '-', time: '' }
  const dt = new Date(d)
  return {
    date: dt.toLocaleDateString('en-IN', {day: '2-digit', month: 'short', year: 'numeric'}),
    time: dt.toLocaleTimeString('en-IN', {hour: '2-digit', minute: '2-digit'})
  }
}

function smartDateInput(input) {
  input.addEventListener('input', function () {
    let raw = this.value.replace(/[^0-9]/g, '').slice(0, 8)
    let formatted = ''
    for (let i = 0; i < raw.length; i++) {
      if (i === 2 || i === 4) formatted += '/'
      formatted += raw[i]
    }
    this.value = formatted
  })
  input.addEventListener('blur', function () {
    const d = parseSmartDate(this.value)
    if (d) this.value = d.toLocaleDateString('en-IN', {day: '2-digit', month: '2-digit', year: 'numeric'})
  })
}

function parseSmartDate(str) {
  if (!str) return null
  const clean = str.replace(/[^0-9]/g, '')
  if (clean.length === 8) {
    const d = parseInt(clean.slice(0,2), 10)
    const m = parseInt(clean.slice(2,4), 10) - 1
    const y = parseInt(clean.slice(4,8), 10)
    return new Date(y, m, d)
  }
  const d2 = new Date(str)
  if (!isNaN(d2.getTime())) return d2
  return null
}

function toISODate(val) {
  const d = parseSmartDate(val)
  if (!d) return val
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function dualDateInput(input) {
  smartDateInput(input)
  createDatePicker(input, {dateFormat: 'd/m/Y', allowInput: true})
}

let navListListenerAttached = false
function closeNavLists() {
  document.querySelectorAll('.flatpickr-nav-pop.open').forEach(pop => pop.classList.remove('open'))
}

function createDatePicker(input, opts = {}) {
  if (typeof flatpickr === 'undefined') return
  let wrapper = input.parentElement
  if (!wrapper.classList.contains('dp-wrap')) {
    wrapper = document.createElement('div')
    wrapper.className = 'dp-wrap'
    wrapper.style.cssText = 'position:relative;display:block'
    input.parentNode.insertBefore(wrapper, input)
    wrapper.appendChild(input)
  }
  if (!input.hasAttribute('data-input')) input.setAttribute('data-input', '')
  if (input.style.flex) wrapper.style.flex = input.style.flex
  if (input.style.minWidth) wrapper.style.minWidth = input.style.minWidth
  if (input.closest('.ee-filters')) {
    wrapper.style.display = 'inline-flex'
    wrapper.style.flex = '0 1 auto'
  }
  let icon = wrapper.querySelector('.cal-icon[data-open]')
  if (!icon) {
    icon = document.createElement('span')
    icon.className = 'cal-icon'
    icon.textContent = '📅'
    icon.setAttribute('data-open', '')
    wrapper.appendChild(icon)
  }
  const cfg = {
    wrap: true,
    disableMobile: true,
    allowInput: false,
    dateFormat: 'Y-m-d',
    appendTo: document.body,
    showDaysInNextAndPreviousMonths: false,
    onChange: (sel, dateStr) => input.dispatchEvent(new Event('change', {bubbles: true})),
    onClose: (sel, dateStr, fp) => { if (fp._closeNav) fp._closeNav() },
    onReady: (sel, dateStr, fp) => {
      const currentMonthEl = fp.calendarContainer.querySelector('.flatpickr-current-month')
      if (!currentMonthEl || currentMonthEl.querySelector('.flatpickr-prev-year')) return
      const prevMonth = fp.calendarContainer.querySelector('.flatpickr-prev-month')
      const nextMonth = fp.calendarContainer.querySelector('.flatpickr-next-month')
      const monthSelect = currentMonthEl.querySelector('.flatpickr-monthDropdown-months')
      const yearWrap = currentMonthEl.querySelector('.numInputWrapper')
      if (!prevMonth || !nextMonth || !monthSelect || !yearWrap) return
      const makeDropdown = (popClass, options, onPick) => {
        const btn = document.createElement('button')
        btn.type = 'button'
        btn.className = 'flatpickr-nav-btn ' + (popClass === 'month-pop' ? 'nav-btn-month' : 'nav-btn-year')
        const pop = document.createElement('div')
        pop.className = 'flatpickr-nav-pop ' + popClass
        document.body.appendChild(pop)
        // The popup lives outside the calendar container; without this,
        // flatpickr treats option taps as "clicked outside" and slams the
        // whole calendar shut before the choice registers.
        ;['mousedown', 'mouseup', 'click', 'touchstart', 'focusin'].forEach(ev =>
          pop.addEventListener(ev, (e) => e.stopPropagation())
        )
        // Wheel/touch over a popup that can't scroll (or is already at its
        // edge) would otherwise chain to the page behind the calendar.
        pop.addEventListener('wheel', (e) => {
          const room = pop.scrollHeight - pop.clientHeight
          if (room <= 0 || (e.deltaY > 0 ? pop.scrollTop >= room - 1 : pop.scrollTop <= 1)) e.preventDefault()
        }, { passive: false })
        let touchY = 0
        pop.addEventListener('touchstart', (e) => { touchY = e.touches[0].clientY }, { passive: true })
        pop.addEventListener('touchmove', (e) => {
          const room = pop.scrollHeight - pop.clientHeight
          const goingUp = touchY - e.touches[0].clientY > 0
          if (room <= 0 || (goingUp ? pop.scrollTop >= room - 1 : pop.scrollTop <= 1)) e.preventDefault()
        }, { passive: false })
        const setSelected = (value) => {
          const opt = pop.querySelector('[data-value="' + value + '"]')
          if (!opt) return
          const prev = pop.querySelector('.selected')
          if (prev) prev.classList.remove('selected')
          opt.classList.add('selected')
          btn.textContent = opt.textContent
        }
        options.forEach(item => {
          const opt = document.createElement('button')
          opt.type = 'button'
          opt.className = 'flatpickr-nav-opt'
          opt.dataset.value = item.value
          opt.textContent = item.label
          if (item.selected) opt.classList.add('selected')
          opt.addEventListener('click', () => {
            onPick(item.value)
            close()
          })
          pop.appendChild(opt)
        })
        const open = () => {
          closeNavLists()
          const rect = btn.getBoundingClientRect()
          const sx = window.scrollX || window.pageXOffset
          const sy = window.scrollY || window.pageYOffset
          pop.classList.add('open')
          // Anchor in document coordinates so the list travels with the
          // calendar header when the page scrolls behind it.
          const h = pop.offsetHeight
          let vpTop = rect.bottom + 4
          if (vpTop + h > window.innerHeight - 8) vpTop = Math.max(8, rect.top - h - 4)
          pop.style.left = (rect.left + sx) + 'px'
          pop.style.top = (vpTop + sy) + 'px'
          const cur = pop.querySelector('.selected')
          if (cur) pop.scrollTop = cur.offsetTop - pop.clientHeight / 2 + cur.clientHeight / 2
        }
        const close = () => pop.classList.remove('open')
        btn.addEventListener('click', (e) => {
          e.preventDefault()
          e.stopPropagation()
          if (pop.classList.contains('open')) close()
          else open()
        })
        return { btn, setSelected, close }
      }
      if (!navListListenerAttached) {
        document.addEventListener('mousedown', (e) => {
          const t = e.target
          if (t && t.closest && !t.closest('.flatpickr-nav-btn') && !t.closest('.flatpickr-nav-pop')) closeNavLists()
        })
        navListListenerAttached = true
      }
      const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
      const monthOptions = []
      for (let m = 0; m < 12; m++) {
        monthOptions.push({ value: m, label: monthNames[m], selected: m === fp.currentMonth })
      }
      const endY = new Date().getFullYear() + 20
      const yearOptions = []
      for (let y = 1900; y <= endY; y++) {
        yearOptions.push({ value: y, label: y, selected: y === fp.currentYear })
      }
      const monthNav = makeDropdown('month-pop', monthOptions, (m) => fp.changeMonth(m - fp.currentMonth))
      const yearNav = makeDropdown('year-pop', yearOptions, (y) => fp.changeYear(y))
      monthNav.setSelected(fp.currentMonth)
      yearNav.setSelected(fp.currentYear)
      fp._syncNav = () => {
        monthNav.setSelected(fp.currentMonth)
        yearNav.setSelected(fp.currentYear)
      }
      fp._closeNav = () => { monthNav.close(); yearNav.close() }
      const addBtn = (cls, arrow, delta) => {
        const b = document.createElement('span')
        b.className = cls
        b.setAttribute('tabindex', '-1')
        b.setAttribute('aria-label', delta < 0 ? 'Previous year' : 'Next year')
        b.textContent = arrow
        b.addEventListener('click', (e) => {
          e.preventDefault()
          e.stopPropagation()
          fp.changeYear(fp.currentYear + delta)
        })
        return b
      }
      const prevYear = addBtn('flatpickr-prev-year', '‹', -1)
      const nextYear = addBtn('flatpickr-next-year', '›', 1)
      currentMonthEl.appendChild(prevMonth)
      currentMonthEl.appendChild(monthNav.btn)
      currentMonthEl.appendChild(nextMonth)
      currentMonthEl.appendChild(prevYear)
      currentMonthEl.appendChild(yearNav.btn)
      currentMonthEl.appendChild(nextYear)
      monthSelect.remove()
      yearWrap.remove()
    },
    onMonthChange: (m, d, fp) => { if (fp._syncNav) fp._syncNav() },
    onYearChange: (y, d, fp) => { if (fp._syncNav) fp._syncNav() },
  }
  if (input.dataset.max) cfg.maxDate = input.dataset.max
  Object.assign(cfg, opts)
  return flatpickr(wrapper, cfg)
}

// Custom confirmation overlay
function showConfirm(title, msg) {
  return new Promise(resolve => {
    const overlay = document.createElement('div')
    overlay.className = 'confirm-overlay'
    overlay.innerHTML = `<div class="confirm-box"><h3>${title}</h3><p>${msg}</p><div class="confirm-actions"><button class="btn primary" id="confirm-yes">Yes</button><button class="btn secondary" id="confirm-no">Cancel</button></div></div>`
    document.body.appendChild(overlay)
    document.getElementById('confirm-yes').onclick = () => { overlay.remove(); resolve(true) }
    document.getElementById('confirm-no').onclick = () => { overlay.remove(); resolve(false) }
    overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(false) } })
  })
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

function renderMenu() {
  menuLinks.innerHTML = ''
  const viewTitles = {
    'home': t('Dashboard'),
    'my-accounts': t('My Account'),
    'submit': t('Submit'),
    'my-history': t('My Activity'),
    'all-members': t('All Members'),
    'admin-panel': t('Admin Panel'),
    'admin-pending': '⏳ ' + t('Pending Requests'),
    'admin-add-member': '➕ ' + t('Add New Member'),
    'admin-direct-entry': '⚡ ' + t('Direct Entry'),
    'admin-edit-entries': '✏️ ' + t('Edit / Correct Entries'),
    'admin-export': '📄 ' + t('Export Report (PDF)'),
    'admin-income-expense': '💰 ' + t('Income / Expenses'),
    'admin-hardlock': '🔒 ' + t('Hardlock / Investment'),
    'admin-reset-password': '🔑 ' + t('Reset Password'),
    'passbook': t('Passbook'),
    'my-profile': t('View Profile'),
    'change-password': t('Change Password'),
  }
  const titleEl = document.getElementById('navbar-title')
  if (titleEl) titleEl.textContent = viewTitles[state.activeView] || ''
  const items = [
    {id: 'home', label: t('Dashboard')},
    {id: 'my-accounts', label: t('My Account')},
    {id: 'submit', label: t('Submit')},
    {id: 'my-history', label: t('My Activity')},
    {id: 'all-members', label: t('All Members')},
  ]
  if (state.currentUser.is_admin) {
    items.splice(3, 0, {id: 'admin-panel', label: t('Admin Panel')})
  }
  items.splice(4, 0, {id: 'passbook', label: t('Passbook')})
  items.forEach(item => {
    const a = document.createElement('a')
    const isActive = item.id === 'admin-panel'
      ? state.activeView === 'admin-panel' || ADMIN_SUB_VIEWS.includes(state.activeView)
      : state.activeView === item.id
    a.href = '#'
    a.className = 'nav-link' + (isActive ? ' active' : '')
    a.textContent = item.label
    a.onclick = (e) => {
      e.preventDefault()
      state.activeView = item.id
      persistActiveView()
      renderView()
    }
    menuLinks.appendChild(a)
  })
  const langBtn = document.createElement('button')
  langBtn.type = 'button'
  langBtn.id = 'lang-toggle'
  langBtn.className = 'nav-link lang-toggle'
  langBtn.innerHTML = `
    <svg class="lang-loop-svg" viewBox="0 0 56 46" aria-hidden="true">
      <defs>
        <linearGradient id="lang-loop-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#8b5cf6" />
          <stop offset="100%" stop-color="#22c55e" />
        </linearGradient>
      </defs>
      <path class="lang-loop-arc" d="M34 4 H44 Q52 4 52 14 V32 Q52 42 44 42 H12 Q4 42 4 32 V14 Q4 4 12 4 H22" />
      <path class="lang-loop-arrow" d="M31.5 4 L21.5 0.8 L21.5 7.2 Z" />
    </svg>
    <span class="lang-loop-label">${state.lang === 'kn' ? 'EN' : 'ಕನ್ನಡ'}</span>`
  menuLinks.appendChild(langBtn)

  // Mobile hamburger menu: open/close the dropdown
  const menuBtn = document.getElementById('menu-btn')
  if (menuBtn) {
    menuBtn.onclick = (e) => {
      e.stopPropagation()
      menuBtn.classList.toggle('open')
      menuLinks.classList.toggle('open')
      // Mobile has no hover: play the loop-arrow animation once each time the
      // menu opens so users notice the Kannada/English toggle.
      if (menuLinks.classList.contains('open')) {
        const lt = document.getElementById('lang-toggle')
        if (lt) {
          lt.classList.remove('lang-loop-demo')
          void lt.offsetWidth
          lt.classList.add('lang-loop-demo')
          setTimeout(() => lt.classList.remove('lang-loop-demo'), 1000)
        }
      }
    }
  }
  // Selecting any item (incl. Sign Out / language) closes the menu
  menuLinks.querySelectorAll('.nav-link').forEach(a => {
    a.addEventListener('click', () => {
      menuLinks.classList.remove('open')
      if (menuBtn) menuBtn.classList.remove('open')
    })
  })

  // ── Top-right profile avatar (mobile) ──
  const avatarBtn = document.getElementById('user-avatar-btn')
  const userMenu = document.getElementById('user-menu')
  if (avatarBtn && userMenu) {
    const u = state.currentUser
    avatarBtn.hidden = false
    if (u && u.photo_url) {
      avatarBtn.style.backgroundImage = `url('${u.photo_url}')`
      avatarBtn.textContent = ''
      avatarBtn.classList.add('has-photo')
    } else {
      avatarBtn.style.backgroundImage = ''
      avatarBtn.textContent = u ? initials(u.name) : ''
      avatarBtn.classList.remove('has-photo')
    }
    userMenu.innerHTML = `
      <button type="button" class="user-menu-item" id="user-view-profile">👤 <span>${t('View Profile')}</span></button>
      <button type="button" class="user-menu-item" id="user-change-pw">🔒 <span>${t('Change Password')}</span></button>
      <div class="user-menu-divider"></div>
      <button type="button" class="user-menu-item danger" id="user-sign-out">🚪 <span>${t('Sign Out')}</span></button>
    `
    avatarBtn.onclick = (e) => {
      e.stopPropagation()
      userMenu.classList.toggle('open')
      if (menuBtn) menuBtn.classList.remove('open')
      menuLinks.classList.remove('open')
    }
    document.getElementById('user-view-profile').onclick = () => {
      userMenu.classList.remove('open')
      setView('my-profile')
    }
    document.getElementById('user-change-pw').onclick = () => {
      userMenu.classList.remove('open')
      state.activeView = 'change-password'
      persistActiveView()
      renderView()
    }
    document.getElementById('user-sign-out').onclick = () => {
      userMenu.classList.remove('open')
      showLogoutConfirm()
    }
  }
}

async function loadMembers() {
  state.members = await api('/members')
  memberSelect.innerHTML = state.members.map(m => `<option value="${m.name}">${m.name}${m.is_admin ? ' (Admin)' : ''}</option>`).join('')
  const last = localStorage.getItem('finance_last_user')
  if (last && state.members.some(m => m.name === last)) memberSelect.value = last
}

async function init() {
  // Close the mobile menu when tapping anywhere outside it
  document.addEventListener('click', (e) => {
    const navbar = document.getElementById('navbar')
    if (navbar && !navbar.contains(e.target)) {
      const btn = document.getElementById('menu-btn')
      const links = document.getElementById('menu-links')
      const avatarBtn = document.getElementById('user-avatar-btn')
      const userMenu = document.getElementById('user-menu')
      if (btn) btn.classList.remove('open')
      if (links) links.classList.remove('open')
      if (userMenu) userMenu.classList.remove('open')
    }
  })
  // Inactivity tracking: any interaction keeps the session alive
  ;['pointerdown', 'keydown', 'touchstart', 'scroll'].forEach(evt =>
    document.addEventListener(evt, markUserActive, {passive: true})
  )
  setInterval(idleTick, 1000)
  await loadMembers()
  try {
    const user = await api('/me')
    if (user && user.member_id) {
      state.currentUser = user
      state.adminToken = user.token || ''
      state.activeView = readActiveView() || 'home'
      renderMenu()
      renderView()
      showScreen('main')
      return
    }
  } catch (e) {}
  showScreen('login')
}

async function handleLogin() {
  const btn = document.getElementById('login-button')
  setLoading(btn, true)
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
    try { localStorage.setItem('finance_last_user', user.name) } catch (e) {}
    state.adminToken = user.token || ''
    state.activeView = 'home'
    persistActiveView()
    renderMenu()
    renderView()
    showScreen('main')
    showWelcomeOverlay(user.name)
  } catch (err) {
    loginError.textContent = t(err.error || 'Login failed. Check your name/password.')
    loginError.classList.remove('hidden')
  } finally {
    setLoading(btn, false)
  }
}

function logout() {
  api('/logout', {method: 'POST'}).catch(() => {})
  state.currentUser = null
  state.adminToken = ''
  adminPin.value = ''
  state.activeView = 'home'
  try { localStorage.removeItem('slv_last_view') } catch (e) {}
  showScreen('login')
}

// ── Session expiry / inactivity auto-logout ──
// Server ends sessions after 30 min of inactivity (12 h absolute).
// The client mirrors this: a warning banner appears 2 minutes before
// logout; any click/touch/keypress/scroll resets the timer.

const IDLE_LIMIT_MS = 30 * 60 * 1000
const IDLE_WARN_MS = 2 * 60 * 1000
let lastActivityAt = Date.now()
let idleWarningEl = null

function handleSessionExpired(message) {
  if (!state.currentUser) return
  state.currentUser = null
  state.adminToken = ''
  adminPin.value = ''
  hideIdleWarning()
  document.querySelectorAll('.modal-overlay').forEach(o => o.remove())
  showToast(t(message || 'Session expired. Please log in again.'), 'info', 5000)
  showScreen('login')
}

function markUserActive() {
  lastActivityAt = Date.now()
  if (idleWarningEl) hideIdleWarning()
}

function hideIdleWarning() {
  if (idleWarningEl) {
    idleWarningEl.remove()
    idleWarningEl = null
  }
}

function showIdleWarning(remainingMs) {
  const mins = Math.floor(remainingMs / 60000)
  const secs = Math.floor((remainingMs % 60000) / 1000)
  if (!idleWarningEl) {
    idleWarningEl = document.createElement('div')
    idleWarningEl.className = 'idle-warning'
    document.body.appendChild(idleWarningEl)
  }
  idleWarningEl.innerHTML =
    `⏳ ${t('You will be logged out soon due to inactivity.')} ` +
    `<strong>${mins}:${String(secs).padStart(2, '0')}</strong> · ` +
    `<button type="button" class="btn secondary" id="idle-stay-btn">${t("I'm here")}</button>`
  const stayBtn = document.getElementById('idle-stay-btn')
  if (stayBtn) stayBtn.onclick = markUserActive
}

function idleTick() {
  if (!state.currentUser) return
  const remaining = IDLE_LIMIT_MS - (Date.now() - lastActivityAt)
  if (remaining <= 0) {
    api('/logout', {method: 'POST'}).catch(() => {})
    handleSessionExpired('Logged out due to inactivity')
    return
  }
  if (remaining <= IDLE_WARN_MS) showIdleWarning(remaining)
}

function showLogoutConfirm() {
  const existing = document.getElementById('logout-overlay')
  if (existing) existing.remove()
  const inputs = document.querySelectorAll('#content input, #content textarea, #content select')
  let unsavedMsg = ''
  inputs.forEach(el => {
    if (el.type === 'file') return
    if (el.tagName === 'SELECT') { if (el.selectedIndex > 0) unsavedMsg = 'You have unsaved information in forms.'; return }
    if (el.value && el.value.trim()) unsavedMsg = 'You have unsaved information in forms.'
  })
  const overlay = document.createElement('div')
  overlay.id = 'logout-overlay'
  overlay.className = 'modal-overlay'
  overlay.innerHTML = `
    <div class="modal-box">
      <p style="margin:0 0 6px;font-weight:600">${t('Sign Out')}</p>
      ${unsavedMsg ? `<p style="margin:0 0 12px;font-size:0.85rem;color:#fbbf24">${t(unsavedMsg)} ${t('These will not be submitted.')}</p>` : ''}
      <p style="margin:0 0 16px;font-size:0.9rem;color:#94a3b8">${t('Are you sure you want to logout?')}</p>
      <div class="reject-form-actions">
        <button class="btn primary" id="logout-confirm-btn" style="background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">${t('Confirm')}</button>
        <button class="btn secondary" id="logout-cancel-btn">${t('Cancel')}</button>
      </div>
    </div>
  `
  document.body.appendChild(overlay)
  document.getElementById('logout-confirm-btn').onclick = () => { overlay.remove(); logout() }
  document.getElementById('logout-cancel-btn').onclick = () => overlay.remove()
}

function renderView() {
  renderMenu()
  const view = state.activeView
  // Safety: never show admin pages to non-admins (e.g. stale saved view)
  if (String(view).startsWith('admin') && !(state.currentUser && state.currentUser.is_admin)) {
    state.activeView = 'home'
    persistActiveView()
    return renderHome()
  }
  if (view === 'admin-panel') return renderAdminPanel()
  if (view === 'admin-pending') return renderAdminPending()
  if (view === 'admin-add-member') return renderAdminAddMember()
  if (view === 'admin-direct-entry') return renderAdminDirectEntry()
  if (view === 'admin-edit-entries') return renderAdminEditEntries()
  if (view === 'admin-export') return renderAdminExport()
  if (view === 'admin-income-expense') return renderAdminIncomeExpense()
  if (view === 'admin-hardlock') return renderAdminHardlock()
  if (view === 'admin-reset-password') return renderAdminResetPassword()
  if (view === 'my-profile') return renderMemberProfile(state.currentUser.member_id, 'details')
  if (view === 'my-accounts') return renderMemberProfile(state.currentUser.member_id, 'accounts')
  if (view === 'change-password') return renderChangePassword()
  if (view === 'submit') return renderSubmitView()
  if (view === 'my-history') return renderAllHistory()
  if (view === 'all-members') return renderAllMembers()
  if (view === 'passbook') return renderPassbook()
  return renderHome()
}

let summaryData = null

async function renderHome() {
  const stats = await api('/admin/stats', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}}).catch(()=>null)
  summaryData = await api('/admin/period_summary', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}}).catch(()=>null)
  const months = (summaryData && summaryData.months) || []
  const years = (summaryData && summaryData.years) || []
  const defMonth = months.length ? months[months.length - 1] : ''
  const defYear = years.length ? years[years.length - 1] : ''
  const html = `
    <div class="panel">
      <h3 class="section-heading">${t('💰 Financial Overview')}</h3>
      <div class="total-box" style="margin-bottom:16px">
        <div class="total-box-main">
          <div class="total-box-label">${t('Total Collected')}</div>
          <div class="total-box-amount">${stats?formatCurrency(stats.total_collected):'-'}</div>
        </div>
        <div class="total-box-breakdown">
          <div class="breakdown-item"><span class="breakdown-dot deposits-dot"></span><span><span class="breakdown-label">${t('Entry Deposit')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.entry_deposit_total):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot shares-dot"></span><span><span class="breakdown-label">${t('Share')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.shares_total):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot interest-dot"></span><span><span class="breakdown-label">${t('Loan Interest')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.loan_interest_received):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot fine-dot"></span><span><span class="breakdown-label">${t('Fine')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.fines_total):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot fdm-dot"></span><span><span class="breakdown-label">${t('FD Gain')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.fd_interest_returned || 0):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot other-dot"></span><span><span class="breakdown-label">${t('Other Income')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.others_total):'-'}</strong></span></div>
          <div class="breakdown-item"><span class="breakdown-dot expense-dot"></span><span><span class="breakdown-label">${t('Expenses')}</span><strong class="breakdown-value">${stats?formatCurrency(stats.expenses_total):'-'}</strong></span></div>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat-card loan-given"><strong>${stats?formatCurrency(stats.total_lent):'-'}</strong><span>${t('Loans Disbursed')}</span></div>
        <div class="stat-card hardlocked"><strong>${stats?formatCurrency(stats.hardlocked_fd):'-'}</strong><span>${t('Hardlock / FD')}</span></div>
        <div class="stat-card available"><strong>${stats?formatCurrency(stats.available_to_lend):'-'}</strong><span>${t('Available to Lend')}</span></div>
      </div>
    </div>

    <div class="panel">
      <h3 class="section-heading">${t('📊 Monthly & Yearly Summary')}</h3>
      <div class="summary-grid">
        <div class="summary-card">
          <div class="summary-card-head">
            <span class="summary-card-title">${t('Monthly')}</span>
            <select id="sum-month" class="summary-select" onchange="updateMonthlySummary(this.value)">${months.length ? months.map(m => `<option value="${m}" ${m===defMonth?'selected':''}>${monthLabel(m)}</option>`).join('') : '<option value="">-</option>'}</select>
          </div>
          <div class="summary-rows" id="sum-month-rows">${summaryData ? summaryRows(summaryData.monthly[defMonth]) : loadingHtml()}</div>
        </div>
        <div class="summary-card">
          <div class="summary-card-head">
            <span class="summary-card-title">${t('Yearly')}</span>
            <select id="sum-year" class="summary-select" onchange="updateYearlySummary(this.value)">${years.length ? years.map(y => `<option value="${y}" ${y===defYear?'selected':''}>${y}</option>`).join('') : '<option value="">-</option>'}</select>
          </div>
          <div class="summary-rows" id="sum-year-rows">${summaryData ? summaryRows(summaryData.yearly[defYear]) : loadingHtml()}</div>
        </div>
      </div>
    </div>

    <div class="group-info">
      <h3 class="section-heading">${t('📋 Group Information')}</h3>
      <div class="group-info-grid">
        <div class="gi-card gi-started">
          <div class="gi-icon">🚀</div>
          <div class="gi-value">${stats?stats.group_start_date:'-'}</div>
          <div class="gi-label">${t('Started')}</div>
        </div>
        <div class="gi-card gi-members">
          <div class="gi-icon">👥</div>
          <div class="gi-value">${stats?stats.member_count:'-'}</div>
          <div class="gi-label">${t('Members')}</div>
        </div>
        <div class="gi-card gi-share">
          <div class="gi-icon">📊</div>
          <div class="gi-value">${stats?formatCurrency(stats.monthly_share):'-'}</div>
          <div class="gi-label">${t('Share')}</div>
        </div>
        <div class="gi-card gi-onetime">
          <div class="gi-icon">💰</div>
          <div class="gi-value">${stats?formatCurrency(stats.entry_deposit_total):'-'}</div>
          <div class="gi-label">${t('Entry Deposit')}</div>
        </div>
        <div class="gi-card gi-period">
          <div class="gi-icon">📅</div>
          <div class="gi-value">${stats?stats.total_period_months/12+' Years':'-'}</div>
          <div class="gi-label">${t('Tenure')}</div>
        </div>
        <div class="gi-card gi-interest">
          <div class="gi-icon">📈</div>
          <div class="gi-value">${stats?stats.loan_interest_rate+'% / month':'-'}</div>
          <div class="gi-label">${t('Loan Interest')}</div>
        </div>
      </div>
    </div>
  `
  content.innerHTML = html
}

function monthLabel(m) {
  if (!m) return ''
  const parts = m.split('-')
  const names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const idx = parseInt(parts[1], 10) - 1
  return (idx >= 0 && idx < 12 ? names[idx] : m) + ' ' + parts[0]
}

function summaryRows(d) {
  d = d || {}
  const items = [
    ['Share', d.share],
    ['Loan Principal', d.loan_principal],
    ['Loan Interest', d.loan_interest],
    ['Fine', d.fine],
  ]
  if (!items.some(([, v]) => Number(v) > 0)) return '<div class="summary-empty">' + t('No data for this period') + '</div>'
  return items.map(([label, val]) =>
    `<div class="summary-row"><span>${t(label)}</span><strong>${formatCurrency(val)}</strong></div>`
  ).join('')
}

function updateMonthlySummary(m) { document.getElementById('sum-month-rows').innerHTML = summaryRows(summaryData && summaryData.monthly[m]) }

function updateYearlySummary(y) { document.getElementById('sum-year-rows').innerHTML = summaryRows(summaryData && summaryData.yearly[y]) }

function readActiveView() {
  try { return localStorage.getItem('slv_last_view') } catch (e) { return null }
}

function persistActiveView() {
  try { localStorage.setItem('slv_last_view', state.activeView) } catch (e) {}
}

function setView(view) {
  state.activeView = view
  persistActiveView()
  renderView()
}

// ── Admin Panel: hub-and-spoke navigation ──────────────────────────
// The hub shows one box per task (same idea as All Members). Tapping
// a box opens a dedicated page showing only that section, with a
// Back button to return. Only one thing is ever on screen.

const ADMIN_SUB_VIEWS = [
  'admin-pending',
  'admin-direct-entry',
  'admin-income-expense',
  'admin-hardlock',
  'admin-edit-entries',
  'admin-export',
  'admin-reset-password',
  'admin-add-member',
]

const ADMIN_HUB_CARDS = [
  {id: 'admin-pending', icon: '⏳', label: 'Pending Requests', desc: 'Approve or reject member requests.', rgb: '245,158,11'},
  {id: 'admin-direct-entry', icon: '⚡', label: 'Direct Entry', desc: 'Record an auto-approved payment.', rgb: '139,92,246'},
  {id: 'admin-income-expense', icon: '💰', label: 'Income / Expenses', desc: 'Add income & expense records.', rgb: '52,211,153'},
  {id: 'admin-hardlock', icon: '🔒', label: 'Hardlock / Investment', desc: 'Active investments, schemes & history.', rgb: '244,114,182'},
  {id: 'admin-edit-entries', icon: '✏️', label: 'Edit / Correct Entries', desc: 'Fix or delete a wrong entry.', rgb: '96,165,250'},
  {id: 'admin-export', icon: '📄', label: 'Export Report (PDF)', desc: 'Download monthly or period summary PDF.', rgb: '34,211,238'},
  {id: 'admin-reset-password', icon: '🔑', label: 'Reset Password', desc: 'Set a new password if a member forgets theirs.', rgb: '251,113,133'},
  {id: 'admin-add-member', icon: '➕', label: 'Add New Member', desc: 'Create a new member account.', rgb: '16,185,129'},
]

async function renderAdminPanel() {
  let pendingCount = 0
  try {
    const items = await api('/admin/submitted_requests', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
    pendingCount = Array.isArray(items) ? items.length : 0
  } catch (e) {}
  const cards = ADMIN_HUB_CARDS.map(c => `
    <div class="admin-hub-card" onclick="setView('${c.id}')">
      ${c.id === 'admin-pending' && pendingCount > 0 ? `<span class="ahc-badge">${pendingCount}</span>` : ''}
      <div class="ahc-icon" style="background:rgba(${c.rgb},0.14);border-color:rgba(${c.rgb},0.35)">${c.icon}</div>
      <div class="ahc-name">${t(c.label)}</div>
      <div class="ahc-desc">${t(c.desc)}</div>
    </div>`).join('')
  content.innerHTML = `
    <div class="panel">
      <div class="admin-hub-grid">${cards}</div>
    </div>
    <div class="panel" style="margin-top:14px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
      <div style="font-size:0.85rem;color:#94a3b8">💾 ${t('Safety copies of all data are made daily. Download one to keep it outside the server.')}</div>
      <button type="button" class="btn secondary" id="admin-download-backup">⬇️ ${t('Download Backup')}</button>
    </div>`
  const dlBtn = document.getElementById('admin-download-backup')
  if (dlBtn) dlBtn.onclick = () => downloadBackup()
}

async function downloadBackup() {
  try {
    const res = await fetch('/api/admin/backup/download', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
    if (!res.ok) throw new Error('failed')
    const blob = await res.blob()
    const m = (res.headers.get('Content-Disposition') || '').match(/filename="?([^"]+)"?/)
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = (m && m[1]) || 'finance-backup.db'
    document.body.appendChild(a)
    a.click()
    a.remove()
    setTimeout(() => URL.revokeObjectURL(a.href), 5000)
    showToast(t('Backup downloaded'), 'success')
  } catch (e) {
    showToast(t('Download failed'), 'error')
  }
}

// Shared shell for admin sub-pages: back button on top, one panel below.
function adminSubPage(bodyHtml) {
  content.innerHTML = `
    <div class="admin-panel">
      <button type="button" class="btn secondary admin-back-btn" id="admin-back-btn">← ${t('Back')}</button>
      <div class="panel" style="margin-top:12px">
        ${bodyHtml}
      </div>
    </div>`
  const backBtn = document.getElementById('admin-back-btn')
  if (backBtn) backBtn.onclick = () => setView('admin-panel')
}

// ── Admin ▸ Add New Member ──
function renderAdminAddMember() {
  adminSubPage(`
    <h3 class="section-heading">➕ ${t('Add New Member')}</h3>
    <div class="input-row"><input id="new-member-name" placeholder="${t('Member name')}" /></div>
    <div class="input-row"><input id="new-member-phone" placeholder="${t('Phone (optional)')}" inputmode="tel" /></div>
    <div class="input-row" style="display:flex;gap:12px">
      <div style="flex:1"><label style="font-size:0.75rem;color:#94a3b8">${t('Entry Deposit Amount')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="new-member-deposit" type="text" inputmode="decimal" value="25000" /></div></div>
      <div style="flex:1"><label style="font-size:0.75rem;color:#94a3b8">${t('Entry Deposit Date')}</label><input id="new-member-date" type="text" value="${istTodayStr()}" class="admin-input" readonly /></div>
    </div>
    <div class="input-row"><label style="font-size:0.75rem;color:#94a3b8">${t('Password')}</label><div class="input-with-icon"><span class="input-icon">🔒</span><input id="new-member-password" type="password" placeholder="${t('Set member password')}" /><span id="new-member-pw-toggle" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);cursor:pointer;color:#94a3b8;font-size:14px;user-select:none">👁</span></div></div>
    <button class="btn primary" id="add-member-btn">${t('Create Account')}</button>
  `)
  document.getElementById('add-member-btn').onclick = handleAddMember
  const nmDate = document.getElementById('new-member-date')
  if (nmDate) createDatePicker(nmDate)
  const nmDep = document.getElementById('new-member-deposit')
  if (nmDep) indianizeInput(nmDep)
  const nmPwToggle = document.getElementById('new-member-pw-toggle')
  const nmPwInput = document.getElementById('new-member-password')
  if (nmPwToggle && nmPwInput) {
    nmPwToggle.onclick = () => {
      nmPwInput.type = nmPwInput.type === 'password' ? 'text' : 'password'
      nmPwToggle.textContent = nmPwInput.type === 'password' ? '👁' : '🙈'
    }
  }
}

// ── Admin ▸ Reset Password ──
function renderAdminResetPassword() {
  const memberOptions = state.members.map(m => `<option value="${m.member_id}">${escHtml(m.name)}</option>`).join('')
  adminSubPage(`
    <h3 class="section-heading">🔑 ${t('Reset Password')}</h3>
    <div class="input-row"><label style="font-size:0.75rem;color:#94a3b8">${t('Select member')}</label><select id="arp-member" style="width:100%;padding:10px;background:#1e1b2e;border:1px solid rgba(148,163,184,0.2);border-radius:8px;color:#e2e8f0;font-size:0.9rem">${memberOptions}</select></div>
    <div class="input-row"><label style="font-size:0.75rem;color:#94a3b8">${t('New password')}</label><div class="input-with-icon"><span class="input-icon">🔒</span><input id="arp-new" type="password" placeholder="${t('New password')}" autocomplete="new-password" /><span id="arp-new-toggle" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);cursor:pointer;color:#94a3b8;font-size:14px;user-select:none">👁</span></div></div>
    <div class="input-row"><label style="font-size:0.75rem;color:#94a3b8">${t('Confirm new password')}</label><div class="input-with-icon"><span class="input-icon">🔒</span><input id="arp-confirm" type="password" placeholder="${t('Confirm new password')}" autocomplete="new-password" /><span id="arp-confirm-toggle" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);cursor:pointer;color:#94a3b8;font-size:14px;user-select:none">👁</span></div></div>
    <button class="btn primary" id="arp-save">${t('Reset')}</button>
  `)
  const wireToggle = (toggleId, inputId) => {
    const tog = document.getElementById(toggleId)
    const inp = document.getElementById(inputId)
    if (tog && inp) {
      tog.onclick = () => {
        inp.type = inp.type === 'password' ? 'text' : 'password'
        tog.textContent = inp.type === 'password' ? '👁' : '🙈'
      }
    }
  }
  wireToggle('arp-new-toggle', 'arp-new')
  wireToggle('arp-confirm-toggle', 'arp-confirm')
  document.getElementById('arp-save').onclick = async () => {
    const sel = document.getElementById('arp-member')
    const nw = document.getElementById('arp-new').value
    const conf = document.getElementById('arp-confirm').value
    if (!sel.value || !nw || !conf) { showToast(t('Fill all fields'), 'error'); return }
    if (nw !== conf) { showToast(t('Passwords do not match'), 'error'); return }
    const btn = document.getElementById('arp-save')
    setLoading(btn, true)
    try {
      await api(`/members/${sel.value}/reset_password`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({new_password: nw}),
      })
      document.getElementById('arp-new').value = ''
      document.getElementById('arp-confirm').value = ''
      showToast(t('Password reset'), 'success')
    } catch (err) {
      showToast(err.error || 'Failed to reset password', 'error')
    } finally {
      setLoading(btn, false)
    }
  }
}

// ── Admin ▸ Direct Entry ──
function renderAdminDirectEntry() {
  adminSubPage(`
    <h3 class="section-heading">⚡ ${t('Direct Entry')}</h3>
    <div class="de-panel">
      <div class="input-row"><select id="de-member" style="width:100%;padding:10px;background:#1e1b2e;border:1px solid rgba(148,163,184,0.2);border-radius:8px;color:#e2e8f0;font-size:0.9rem">${state.members.map(m => `<option value="${m.member_id}">${m.name}</option>`).join('')}</select></div>
      <div class="input-row" style="display:flex;gap:12px">
        <div style="flex:1"><label>${t('Share')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="de-share" type="text" inputmode="decimal" value="500" /></div></div>
        <div style="flex:1"><label>${t('Fine')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="de-fine" type="text" inputmode="decimal" value="0" /></div></div>
      </div>
      <div class="input-row" style="display:flex;gap:12px">
        <div style="flex:1"><label>${t('Loan Principal')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="de-loan-principal" type="text" inputmode="decimal" placeholder="0" /></div></div>
        <div style="flex:1"><label>${t('Loan Interest')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="de-loan-interest" type="text" inputmode="decimal" placeholder="0" /></div></div>
      </div>
      <div class="input-row" style="margin-top:4px">
        <div style="flex:1;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;">
          <span style="font-weight:600">${t('Total Amount')}</span>
          <strong id="de-total-amount" style="font-size:1.1rem;color:#34d399">₹0</strong>
        </div>
      </div>
      <div class="input-row"><label>${t('Date')}</label><input id="de-date" type="text" value="${istTodayStr()}" class="admin-input" readonly /></div>
      <div class="input-row"><input id="de-note" placeholder="${t('Note (optional)')}" /></div>
      <button class="btn primary" id="de-submit-btn">${t('Submit & Auto-Approve')}</button>
    </div>
  `)
  const deBtn = document.getElementById('de-submit-btn')
  if (deBtn) deBtn.onclick = handleDirectEntry
  ;['de-share', 'de-fine', 'de-loan-principal', 'de-loan-interest'].forEach(id => {
    const el = document.getElementById(id)
    if (el) indianizeInput(el)
  })
  const deDate = document.getElementById('de-date')
  if (deDate) createDatePicker(deDate)
  const deTotalEl = document.getElementById('de-total-amount')
  const updateDeTotal = () => {
    const sum = ['de-share', 'de-fine', 'de-loan-principal', 'de-loan-interest'].reduce((acc, id) => {
      const el = document.getElementById(id)
      return acc + (Number((el ? el.value : '').replace(/,/g, '')) || 0)
    }, 0)
    if (deTotalEl) deTotalEl.textContent = formatCurrency(sum)
  }
  ;['de-share', 'de-fine', 'de-loan-principal', 'de-loan-interest'].forEach(id => {
    const el = document.getElementById(id)
    if (el) el.addEventListener('input', updateDeTotal)
  })
  updateDeTotal()
}

// ── Admin ▸ Pending Requests ──
function renderAdminPending() {
  adminSubPage(`
    <h3 class="section-heading">⏳ ${t('Pending Requests')}</h3>
    <div id="submitted-requests"></div>
  `)
  renderSubmittedRequests()
}

// ── Admin ▸ Edit / Correct Entries ──
function renderAdminEditEntries() {
  const eeTypeOptions = [
    ['all', t('All types')], ['split', t('Share / Loan')],
    ['entry_deposit', t('Entry Deposit')], ['loan_disbursed', t('Loan Disbursed')],
    ['income', t('Income')], ['expense', t('Expense')], ['fd', t('FD Gain')],
  ].map(([v, l]) => `<option value="${v}">${l}</option>`).join('')
  adminSubPage(`
    <h3 class="section-heading">✏️ ${t('Edit / Correct Entries')}</h3>
    <div class="ee-filters">
      <select id="ee-type" class="admin-input" style="flex:1;min-width:120px">${eeTypeOptions}</select>
      <select id="ee-member" class="admin-input" style="flex:1;min-width:120px"><option value="">${t('All members')}</option>${state.members.map(m => `<option value="${m.member_id}">${escHtml(m.name)}</option>`).join('')}</select>
      <input id="ee-q" class="admin-input" style="flex:1.5;min-width:160px" placeholder="${t('Search member or description...')}" />
    </div>
    <div class="ee-filters" style="margin-top:8px">
      <label class="ee-date-label">${t('From')}:</label>
      <input type="text" id="ee-from" class="admin-input" style="flex:1;min-width:0" readonly />
      <label class="ee-date-label">${t('To')}:</label>
      <input type="text" id="ee-to" class="admin-input" style="flex:1;min-width:0" readonly />
    </div>
    <div id="ee-list" style="margin-top:12px"></div>
  `)
  const eeType = document.getElementById('ee-type')
  const eeMember = document.getElementById('ee-member')
  const eeQ = document.getElementById('ee-q')
  const eeFrom = document.getElementById('ee-from')
  const eeTo = document.getElementById('ee-to')
  if (eeFrom) createDatePicker(eeFrom)
  if (eeTo) createDatePicker(eeTo)
  if (eeType && eeMember && eeQ && eeFrom && eeTo) {
    eeType.onchange = eeLoad
    eeMember.onchange = eeLoad
    eeFrom.onchange = eeLoad
    eeTo.onchange = eeLoad
    let eeDebounce
    eeQ.oninput = () => { clearTimeout(eeDebounce); eeDebounce = setTimeout(eeLoad, 400) }
    eeLoad()
  }
}

// ── Admin ▸ Export Report (PDF) ──
function renderAdminExport() {
  adminSubPage(`
    <h3 class="section-heading">📄 ${t('Export Report (PDF)')}</h3>
    <div class="ee-filters" style="align-items:center">
      <label class="inv-type-label" style="flex:1;display:flex;align-items:center;gap:6px;padding:8px 12px;background:rgba(199,210,254,0.08);border-radius:8px;cursor:pointer">
        <input type="radio" name="export-type" value="month" checked onchange="window.toggleExportType()" /> ${t('Monthly')}
      </label>
      <label class="inv-type-label" style="flex:1;display:flex;align-items:center;gap:6px;padding:8px 12px;background:rgba(199,210,254,0.08);border-radius:8px;cursor:pointer">
        <input type="radio" name="export-type" value="custom" onchange="window.toggleExportType()" /> ${t('Custom period')}
      </label>
    </div>
    <div class="ee-filters" style="margin-top:8px;align-items:center">
      <div id="export-month-wrap" style="flex:1;min-width:0">
        <label class="ee-date-label">${t('Month')}:</label>
        <input type="text" id="export-month" class="admin-input" readonly />
      </div>
      <div id="export-custom-wrap" style="display:none;flex:1;min-width:0;align-items:center">
        <label class="ee-date-label">${t('From')}:</label>
        <input type="text" id="export-from" class="admin-input" style="flex:1;min-width:0" readonly />
        <label class="ee-date-label">${t('To')}:</label>
        <input type="text" id="export-to" class="admin-input" style="flex:1;min-width:0" readonly />
      </div>
      <button class="btn primary" id="export-btn" style="justify-content:center;white-space:nowrap">${t('⬇ Export PDF')}</button>
    </div>
  `)
  const exportMonth = document.getElementById('export-month')
  if (exportMonth) {
    exportMonth.value = isoDateString(new Date())
    createDatePicker(exportMonth)
  }
  const exportFrom = document.getElementById('export-from')
  if (exportFrom) createDatePicker(exportFrom)
  const exportTo = document.getElementById('export-to')
  if (exportTo) createDatePicker(exportTo)
  const exportBtn = document.getElementById('export-btn')
  if (exportBtn) exportBtn.onclick = handleExportReport
  window.toggleExportType = () => {
    const type = document.querySelector('input[name="export-type"]:checked')
    if (!type) return
    const isMonth = type.value === 'month'
    const mw = document.getElementById('export-month-wrap')
    const cw = document.getElementById('export-custom-wrap')
    if (mw) mw.style.display = isMonth ? 'block' : 'none'
    if (cw) cw.style.display = isMonth ? 'none' : 'flex'
  }
  window.toggleExportType()
}

// ── Admin ▸ Income / Expenses ──
function renderAdminIncomeExpense() {
  const ieFormFields = (type) => {
    const isInc = type === 'income'
    const col = isInc ? 'rgba(52,211,153,0.15)' : 'rgba(239,68,68,0.15)'
    const txt = isInc ? '#34d399' : '#fca5a5'
    const bdr = isInc ? 'rgba(52,211,153,0.25)' : 'rgba(239,68,68,0.25)'
    return `
      <div style="margin-bottom:8px"><label style="font-size:0.8rem;color:#94a3b8">${t('Amount')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="${type}-amount" type="text" inputmode="decimal" /></div></div>
      <div style="margin-bottom:8px"><label style="font-size:0.8rem;color:#94a3b8">${t('Date')}</label><input id="${type}-date" type="text" value="${istTodayStr()}" class="admin-input" readonly /></div>
      <div style="margin-bottom:8px"><label style="font-size:0.8rem;color:#94a3b8">${t('Reason')}</label><input id="${type}-reason" class="admin-input" placeholder="${t(isInc ? 'e.g. Donation from X' : 'e.g. Meeting snacks')}" /></div>
      <button class="btn primary" id="save-${type}-btn" style="background:${col};color:${txt};border:1px solid ${bdr}">${t('Save')}</button>`
  }
  const ieSection = window.innerWidth <= 640
    ? `
      <div class="admin-toggle-row" style="margin-bottom:14px">
        <button class="btn btn-admin-toggle" id="toggle-income-form" style="background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.25)">${t('+ Add Income')}</button>
        <button class="btn btn-admin-toggle" id="toggle-expense-form" style="background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">${t('+ Add Expense')}</button>
      </div>
      <div id="income-form" style="display:none;margin-top:10px">${ieFormFields('income')}</div>
      <div id="expense-form" style="display:none;margin-top:10px">${ieFormFields('expense')}</div>`
    : `
      <div class="grid-2" style="gap:16px;margin-bottom:14px">
        <div class="panel" style="margin:0">
          <h4 style="color:#34d399;margin:0 0 8px">${t('Income (Gains)')}</h4>
          <button class="btn primary btn-shine" id="toggle-income-form" style="background:rgba(52,211,153,0.15);color:#34d399;border:1px solid rgba(52,211,153,0.25)">${t('+ Add Income')}</button>
          <div id="income-form" style="display:none;margin-top:10px">${ieFormFields('income')}</div>
        </div>
        <div class="panel" style="margin:0">
          <h4 style="color:#fca5a5;margin:0 0 8px">${t('Expenses')}</h4>
          <button class="btn primary btn-shine" id="toggle-expense-form" style="background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">${t('+ Add Expense')}</button>
          <div id="expense-form" style="display:none;margin-top:10px">${ieFormFields('expense')}</div>
        </div>
      </div>`
  adminSubPage(`
    <h3 class="section-heading">💰 ${t('Income / Expenses')}</h3>
    ${ieSection}
    <div id="ie-list"></div>
  `)
  document.getElementById('toggle-income-form').onclick = () => toggleForm('income')
  document.getElementById('toggle-expense-form').onclick = () => toggleForm('expense')
  document.getElementById('save-income-btn').onclick = () => handleSaveIe('credit')
  document.getElementById('save-expense-btn').onclick = () => handleSaveIe('debit')
  const incAmt = document.getElementById('income-amount')
  if (incAmt) indianizeInput(incAmt)
  const expAmt = document.getElementById('expense-amount')
  if (expAmt) indianizeInput(expAmt)
  const incDate = document.getElementById('income-date')
  if (incDate) createDatePicker(incDate)
  const expDate = document.getElementById('expense-date')
  if (expDate) createDatePicker(expDate)
  renderIeList()
}

// ── Admin ▸ Hardlock / Investment ──
let adminFdTab = 'active'

function renderAdminHardlock() {
  adminSubPage(`
    <h3 class="section-heading">🔒 ${t('Hardlock / Investment')}</h3>
    <button class="btn btn-admin-toggle" id="fd-toggle-btn" style="width:100%;justify-content:center;gap:8px;margin-bottom:12px">＋ ${t('Add Investment')} <span class="fd-chevron" id="fd-toggle-chevron">▾</span></button>
    <div id="fd-form-body" style="display:none;margin-bottom:16px">
      <div class="fd-card-form">
        <div style="display:flex;gap:10px;margin-bottom:12px">
          <label class="inv-type-label" style="flex:1;display:flex;align-items:center;gap:6px;padding:8px 12px;background:rgba(199,210,254,0.08);border-radius:8px;cursor:pointer">
            <input type="radio" name="inv-type" value="one_time" checked onchange="window.toggleInvType()" /> ${t('One-time')}
          </label>
          <label class="inv-type-label" style="flex:1;display:flex;align-items:center;gap:6px;padding:8px 12px;background:rgba(199,210,254,0.08);border-radius:8px;cursor:pointer">
            <input type="radio" name="inv-type" value="monthly" onchange="window.toggleInvType()" /> ${t('Monthly Scheme')}
          </label>
        </div>
        <div class="fd-form-grid">
          <div class="fd-field" id="inv-amount-field">
            <label>${t('Amount')}</label>
            <div class="input-group"><span class="input-prefix">₹</span><input id="fd-amount" type="text" inputmode="decimal" placeholder="0" /></div>
          </div>
          <div class="fd-field">
            <label>${t('Start Date')}</label>
            <div class="input-group"><input id="fd-start" class="dual-date" type="text" placeholder="DD/MM/YYYY" value="${new Date().toLocaleDateString('en-IN', {day:'2-digit',month:'2-digit',year:'numeric'})}" /></div>
          </div>
          <div class="fd-field">
            <label>${t('End / Maturity')}</label>
            <div class="input-group"><input id="fd-end" class="dual-date" type="text" placeholder="DD/MM/YYYY" /></div>
          </div>
          <div class="fd-field" id="inv-rate-field">
            <label>${t('Interest Rate')}</label>
            <div class="input-group"><input id="fd-rate" type="text" inputmode="decimal" value="7" /><span class="input-suffix">%</span></div>
          </div>
          <div class="fd-field">
            <label id="inv-provider-label">${t('Bank / Scheme')}</label>
            <div class="input-group"><input id="fd-bank" placeholder="${t('e.g. SBI')}" /></div>
          </div>
          <div class="fd-field fd-field-btn">
            <label>&nbsp;</label>
            <button class="btn primary" id="fd-add-btn">${t('Add')}</button>
          </div>
        </div>
        <p id="inv-monthly-note" style="display:none;color:#94a3b8;font-size:0.85rem;margin:8px 0 0">${t('Add monthly installments using the + button in Active section.')}</p>
      </div>
    </div>
    <div class="fd-tabs">
      <button type="button" class="fd-tab" id="fd-tab-btn-active">🟢 ${t('Active')}</button>
      <button type="button" class="fd-tab" id="fd-tab-btn-history">🗄️ ${t('History')}</button>
    </div>
    <div id="fd-tab-active">
      <div class="fd-section">
        <div id="fd-keeping"></div>
      </div>
    </div>
    <div id="fd-tab-history" style="display:none">
      <div class="fd-section">
        <div id="fd-record"></div>
      </div>
    </div>
  `)
  const fdToggleBtn = document.getElementById('fd-toggle-btn')
  if (fdToggleBtn) {
    fdToggleBtn.onclick = () => {
      toggleAdminSection('fd-toggle-btn', 'fd-form-body')
      const ch = document.getElementById('fd-toggle-chevron')
      if (ch) ch.textContent = fdToggleBtn.classList.contains('active') ? '▴' : '▾'
    }
  }
  document.getElementById('fd-add-btn').onclick = handleAddFd
  const fdAmt = document.getElementById('fd-amount')
  if (fdAmt) indianizeInput(fdAmt)
  const fdStart = document.getElementById('fd-start')
  if (fdStart) dualDateInput(fdStart)
  const fdEnd = document.getElementById('fd-end')
  if (fdEnd) dualDateInput(fdEnd)
  const setActiveTab = (tab) => {
    adminFdTab = tab
    const actPane = document.getElementById('fd-tab-active')
    const histPane = document.getElementById('fd-tab-history')
    const bA = document.getElementById('fd-tab-btn-active')
    const bH = document.getElementById('fd-tab-btn-history')
    if (!actPane || !histPane) return
    actPane.style.display = tab === 'active' ? 'block' : 'none'
    histPane.style.display = tab === 'history' ? 'block' : 'none'
    if (bA) bA.classList.toggle('active', tab === 'active')
    if (bH) bH.classList.toggle('active', tab === 'history')
  }
  const tabBtnA = document.getElementById('fd-tab-btn-active')
  const tabBtnH = document.getElementById('fd-tab-btn-history')
  if (tabBtnA) tabBtnA.onclick = () => setActiveTab('active')
  if (tabBtnH) tabBtnH.onclick = () => setActiveTab('history')
  setActiveTab(adminFdTab)
  window.toggleInvType()
  renderFdEntries()
}

function dateFromInputValue(v) {
  if (!v) return null
  const iso = v.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (iso) return new Date(+iso[1], +iso[2] - 1, +iso[3])
  const d = parseSmartDate(v)
  return d && !isNaN(d.getTime()) ? d : null
}

function isoDateString(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

async function handleExportReport() {
  const btn = document.getElementById('export-btn')
  const setBusy = (b) => {
    if (!btn) return
    btn.disabled = b
    btn.textContent = b ? t('Generating...') : t('⬇ Export PDF')
  }
  const typeEl = document.querySelector('input[name="export-type"]:checked')
  const type = typeEl ? typeEl.value : 'month'
  let from, to
  if (type === 'month') {
    const d = dateFromInputValue(document.getElementById('export-month').value)
    if (!d) { showToast(t('Select a month'), 'error'); return }
    from = isoDateString(new Date(d.getFullYear(), d.getMonth(), 1))
    to = isoDateString(new Date(d.getFullYear(), d.getMonth() + 1, 0))
  } else {
    const df = dateFromInputValue(document.getElementById('export-from').value)
    const dt = dateFromInputValue(document.getElementById('export-to').value)
    if (!df || !dt) { showToast(t('Select From and To dates'), 'error'); return }
    if (dt < df) { showToast(t('To date must be on or after From date'), 'error'); return }
    from = isoDateString(df)
    to = isoDateString(dt)
  }
  setBusy(true)
  try {
    const headers = {}
    if (state.adminToken) headers['X-ADMIN-TOKEN'] = state.adminToken
    const res = await fetch(`/api/admin/export_report?from=${from}&to=${to}`, {headers})
    if (!res.ok) {
      const j = await res.json().catch(() => ({}))
      throw new Error(j.message || t('Export failed'))
    }
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `SLV_Finance_Report_${from}_to_${to}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(a.href)
    showToast(t('Report downloaded'))
  } catch (err) {
    showToast(err.message || t('Export failed'), 'error')
  } finally {
    setBusy(false)
  }
}


let eeEntries = []

const SPLIT_KINDS = ['share', 'fine', 'loan_principal', 'split']
function isSplitKind(kind) { return SPLIT_KINDS.includes(kind) }

function fundErrMsg(e) {
  if (e && e.error === 'insufficient_funds' && e.available != null) {
    return t('Insufficient funds') + ': ' + t('Available') + ' ' + formatCurrency(e.available) + ', ' + t('Requested') + ' ' + formatCurrency(e.requested)
  }
  return ''
}

function eeKindLabel(kind) {
  if (isSplitKind(kind)) return t('Share / Loan')
  const map = {deposit: 'Entry Deposit', entry_deposit: 'Entry Deposit', loan_disbursed: 'Loan Disbursed', share: 'Share', fine: 'Fine', loan_principal: 'Loan Principal', income: 'Income', expense: 'Expense', fd: 'Hardlock / Investment'}
  return t(map[kind] || kind)
}

async function eeLoad() {
  const list = document.getElementById('ee-list')
  if (!list) return
  const type = document.getElementById('ee-type').value
  const member = document.getElementById('ee-member').value
  const q = document.getElementById('ee-q').value.trim()
  const from = document.getElementById('ee-from').value
  const to = document.getElementById('ee-to').value
  if (!type || (type === 'all' && !member && !q && !from && !to)) {
    eeEntries = []
    list.innerHTML = '<p style="color:#64748b;text-align:center;padding:16px">' + t('Select a type or member, or search, to show entries.') + '</p>'
    return
  }
  list.innerHTML = loadingHtml()
  let url = '/admin/entries?type=' + encodeURIComponent(type) + (member ? '&member_id=' + encodeURIComponent(member) : '') + (q ? '&q=' + encodeURIComponent(q) : '')
  if (from) url += '&date_from=' + encodeURIComponent(from)
  if (to) url += '&date_to=' + encodeURIComponent(to)
  try {
    eeEntries = await api(url, {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
  } catch (err) {
    list.innerHTML = '<p style="color:#fca5a5;text-align:center;padding:16px">' + t('Error loading') + '</p>'
    return
  }
  if (!eeEntries.length) { list.innerHTML = '<p style="color:#64748b;text-align:center;padding:16px">' + t('No entries found.') + '</p>'; return }
  list.innerHTML = eeEntries.map(eeRowHtml).join('')
}

function eeRowHtml(e) {
  let detail = ''
  let amountHtml = `<div class="ee-amount">${e.kind === 'expense' ? '−' : ''}${formatCurrency(e.amount)}</div>`
  if (isSplitKind(e.kind)) {
    const sp = e.split || {}
    const cell = (label, val, cls) => `<span class="ee-split-cell${cls ? ' ' + cls : ''}"><span class="ee-split-label">${label}</span><span class="ee-split-val">${formatCurrency(val || 0)}</span></span>`
    const total = (sp.share || 0) + (sp.fine || 0) + (sp.loan_interest || 0) + (sp.loan_principal || 0)
    amountHtml = `<div class="ee-split">${cell(t('Share'), sp.share)}${cell(t('Fine'), sp.fine)}${cell(t('Loan Interest'), sp.loan_interest)}${cell(t('Loan Principal'), sp.loan_principal)}${cell(t('Total'), total, 'ee-split-total')}</div>`
  } else if (e.description) {
    detail = `<div class="ee-sub">${escHtml(e.description)}</div>`
  }
  const badge = isSplitKind(e.kind) ? 'ee-badge-split' : (e.kind === 'expense' || (e.debit_credit === 'debit') ? 'ee-badge-expense' : 'ee-badge-' + e.kind)
  return `<div class="ee-row">
    <div class="ee-main">
      <span class="ee-badge ${badge}">${eeKindLabel(e.kind)}</span>
      <strong>${escHtml(e.member_name)}</strong>
      <span class="ee-date">${formatDate(e.date)}</span>
    </div>
    ${amountHtml}
    <div class="ee-actions">
      ${e.kind === 'fd' ? '' : `<button class="btn secondary" style="padding:5px 12px;font-size:0.8rem" onclick="eeEdit('${e.id}')">✏️ ${t('Edit')}</button>
      <button class="btn secondary" style="padding:5px 12px;font-size:0.8rem;color:#fca5a5" onclick="eeDelete('${e.id}')">🗑 ${t('Delete')}</button>`}
    </div>
    ${detail}
  </div>`
}

function eeEdit(id) {
  const e = eeEntries.find(x => x.id === id)
  if (!e) return
  let fields
  if (isSplitKind(e.kind)) {
    const sp = e.split || {}
    const num = (k, fallback) => sp[k] != null ? sp[k] : (fallback || 0)
    const total = (sp.share || 0) + (sp.fine || 0) + (sp.loan_interest || 0) + (sp.loan_principal || 0)
    fields = `<div class="input-row"><label>${t('Date')}</label><input id="ee-edit-date" type="text" class="admin-input" value="${e.date}" readonly /></div>
      <div class="ee-edit-total">${t('Total')}: <strong id="ee-edit-total-val">${formatCurrency(total)}</strong></div>
      <div class="input-row"><label>${t('Share')}</label><input id="ee-edit-share" type="text" inputmode="decimal" class="admin-input" value="${num('share', e.amount)}" /></div>
      <div class="input-row"><label>${t('Fine')}</label><input id="ee-edit-fine" type="text" inputmode="decimal" class="admin-input" value="${num('fine', e.fine)}" /></div>
      <div class="input-row"><label>${t('Loan Interest')}</label><input id="ee-edit-loan-interest" type="text" inputmode="decimal" class="admin-input" value="${num('loan_interest', e.loan_interest)}" /></div>
      <div class="input-row"><label>${t('Loan Principal')}</label><input id="ee-edit-loan-principal" type="text" inputmode="decimal" class="admin-input" value="${num('loan_principal', e.loan_principal)}" /></div>`
  } else {
    fields = `<div class="input-row"><label>${t('Date')}</label><input id="ee-edit-date" type="text" class="admin-input" value="${e.date}" readonly /></div>
      <div class="input-row"><label>${t('Amount')}</label><input id="ee-edit-amount" type="text" inputmode="decimal" class="admin-input" value="${e.amount}" /></div>`
  }
  const overlay = document.createElement('div')
  overlay.className = 'modal-overlay'
  overlay.id = 'ee-modal'
  overlay.innerHTML = `<div class="modal-box">
    <h3 style="margin:0 0 12px">${t('Edit')}: ${eeKindLabel(e.kind)} — ${escHtml(e.member_name)}</h3>
    ${isSplitKind(e.kind) ? `<p style="color:#94a3b8;font-size:0.8rem;margin:0 0 10px">${t('Set the full split for this member on this date.')}</p>` : ''}
    ${fields}
    <div class="reject-form-actions" style="margin-top:14px">
      <button class="btn primary" id="ee-save-btn">${t('Save')}</button>
      <button class="btn secondary" id="ee-cancel-btn">${t('Cancel')}</button>
    </div>
  </div>`
  document.body.appendChild(overlay)
  overlay.addEventListener('click', ev => { if (ev.target === overlay) overlay.remove() })
  document.getElementById('ee-save-btn').onclick = () => eeSave(e, overlay)
  document.getElementById('ee-cancel-btn').onclick = () => overlay.remove()
  const dateInput = document.getElementById('ee-edit-date')
  if (dateInput) createDatePicker(dateInput)
  ;['ee-edit-amount', 'ee-edit-share', 'ee-edit-fine', 'ee-edit-loan-principal', 'ee-edit-loan-interest'].forEach(id2 => {
    const el = document.getElementById(id2)
    if (el) indianizeInput(el)
  })
  const totalVal = document.getElementById('ee-edit-total-val')
  if (totalVal) {
    const recalcTotal = () => {
      const sum = ['ee-edit-share', 'ee-edit-fine', 'ee-edit-loan-interest', 'ee-edit-loan-principal'].reduce((acc, id2) => {
        const el = document.getElementById(id2)
        return acc + (Number((el && el.value || '').replace(/,/g, '')) || 0)
      }, 0)
      totalVal.textContent = formatCurrency(sum)
    }
    ;['ee-edit-share', 'ee-edit-fine', 'ee-edit-loan-interest', 'ee-edit-loan-principal'].forEach(id2 => {
      const el = document.getElementById(id2)
      if (el) el.addEventListener('input', recalcTotal)
    })
  }
}

async function eeSave(e, overlay) {
  const payload = {
    kind: e.kind,
    member_id: e.member_id,
    date: document.getElementById('ee-edit-date').value,
    contribution_id: e.contribution_id,
    transaction_id: e.transaction_id,
    payment_id: e.payment_id,
    changed_by: (state.currentUser && state.currentUser.member_id) || null,
  }
  if (isSplitKind(e.kind)) {
    const num = id2 => Number(document.getElementById(id2).value.replace(/,/g, '')) || 0
    payload.share = num('ee-edit-share')
    payload.fine = num('ee-edit-fine')
    payload.loan_interest = num('ee-edit-loan-interest')
    payload.loan_principal = num('ee-edit-loan-principal')
  } else {
    payload.amount = Number(document.getElementById('ee-edit-amount').value.replace(/,/g, '')) || 0
  }
  try {
    const res = await api('/admin/entries/edit', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify(payload),
    })
    if (res.error) throw new Error(res.error)
    showToast(t('Entry updated'), 'success')
    overlay.remove()
    eeLoad()
  } catch (err) {
    showToast(t('Edit failed'), 'error')
  }
}

async function eeDelete(id) {
  const e = eeEntries.find(x => x.id === id)
  if (!e) return
  if (!(await showConfirm(t('Delete Entry'), t('Delete this entry permanently?') + ' ' + eeKindLabel(e.kind) + ' — ' + formatCurrency(e.amount)))) return
  try {
    const payload = e.kind === 'split'
      ? {kind: 'split', member_id: e.member_id, date: e.date, changed_by: (state.currentUser && state.currentUser.member_id) || null}
      : {
          kind: e.kind,
          member_id: e.member_id,
          contribution_id: e.contribution_id,
          transaction_id: e.transaction_id,
          payment_id: e.payment_id,
          changed_by: (state.currentUser && state.currentUser.member_id) || null,
        }
    const res = await api('/admin/entries/delete', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify(payload),
    })
    if (res.error) throw new Error(res.error)
    showToast(t('Entry deleted'), 'success')
    eeLoad()
  } catch (err) {
    showToast(t('Delete failed'), 'error')
  }
}

function toggleForm(type) {
  const mobile = window.innerWidth <= 640
  const pairs = [
    ['income', 'income-form', 'toggle-income-form'],
    ['expense', 'expense-form', 'toggle-expense-form'],
  ]
  const label = cur => cur === 'income' ? t('+ Add Income') : t('+ Add Expense')
  const cancelText = t('− Cancel')
  for (const [cur, formId, btnId] of pairs) {
    const form = document.getElementById(formId)
    const btn = document.getElementById(btnId)
    if (!form || !btn) continue
    if (cur === type) {
      const isVisible = form.style.display !== 'none'
      form.style.display = isVisible ? 'none' : 'block'
      btn.textContent = isVisible ? label(cur) : cancelText
    } else if (mobile) {
      form.style.display = 'none'
      btn.textContent = label(cur)
    }
  }
}

window.toggleInvType = function() {
  const isMonthly = document.querySelector('input[name="inv-type"]:checked')?.value === 'monthly'
  const amtField = document.getElementById('inv-amount-field')
  const rateField = document.getElementById('inv-rate-field')
  const label = document.getElementById('inv-provider-label')
  const note = document.getElementById('inv-monthly-note')
  const btn = document.getElementById('fd-add-btn')
  if (amtField) amtField.style.display = isMonthly ? 'none' : ''
  if (rateField) rateField.style.display = isMonthly ? 'none' : ''
  if (label) label.textContent = isMonthly ? t('Scheme Name') : t('Bank / Scheme')
  if (note) note.style.display = isMonthly ? '' : 'none'
  if (btn) btn.textContent = isMonthly ? t('Create Scheme') : t('Add')
}


async function renderIeList() {
  const div = document.getElementById('ie-list')
  if (!div) return
  div.innerHTML = loadingHtml()
  try {
    const rows = await api('/admin/transactions', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
    if (!rows || !rows.length) { div.innerHTML = '<p style="color:#64748b">' + t('No income or expense entries yet.') + '</p>'; return }
    div.innerHTML = '<table class="table"><thead><tr><th>' + t('Date') + '</th><th>' + t('Type') + '</th><th>' + t('Reason') + '</th><th style="text-align:right">' + t('Amount') + '</th></tr></thead><tbody>' +
      rows.slice(0, 30).map(r => `<tr>
        <td style="white-space:nowrap">${formatDate(r.timestamp)}</td>
        <td><span style="color:${r.debit_credit === 'credit' ? '#34d399' : '#fca5a5'}">${r.debit_credit === 'credit' ? t('Income') : t('Expense')}</span></td>
        <td style="color:#94a3b8">${r.description || '-'}</td>
        <td style="text-align:right;font-weight:600;color:${r.debit_credit === 'credit' ? '#34d399' : '#fca5a5'}">${r.debit_credit === 'credit' ? '+' : '-'}${formatCurrency(r.amount)}</td>
      </tr>`).join('') + '</tbody></table>'
  } catch (e) {
    div.innerHTML = '<p style="color:#ef4444">' + t('Error loading transactions') + '</p>'
  }
}


async function handleSaveIe(type) {
  const prefix = type === 'credit' ? 'income' : 'expense'
  const btn = document.getElementById(`save-${prefix}-btn`)
  const amount = Number(document.getElementById(`${prefix}-amount`).value.replace(/,/g,''))
  const desc = document.getElementById(`${prefix}-reason`).value.trim()
  const entry_date = document.getElementById(`${prefix}-date`).value
  if (!amount || amount <= 0) { showToast('Enter a valid amount', 'error'); return }
  if (!desc) { showToast('Enter a reason', 'error'); return }
  if (!(await showConfirm(type === 'credit' ? 'Record Income' : 'Record Expense', `${formatCurrency(amount)} — ${desc}${entry_date ? ' on '+formatDate(entry_date) : ''}?`))) return
  setLoading(btn, true)
  try {
    await api('/admin/income-expense/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify({type, amount, description: desc, entry_date}),
    })
    showToast(type === 'credit' ? 'Income recorded' : 'Expense recorded', 'success')
    document.getElementById(`${prefix}-amount`).value = ''
    document.getElementById(`${prefix}-reason`).value = ''
    toggleForm(prefix === 'income' ? 'income' : 'expense')
    renderView()
  } finally {
    setLoading(btn, false)
  }
}


async function renderSubmittedRequests() {
  const div = document.getElementById('submitted-requests')
  if (!div) return
  div.innerHTML = loadingHtml()
  try {
    const items = await api('/admin/submitted_requests', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
    if (!items || items.length === 0) {
      div.innerHTML = '<p style="color:#64748b">' + t('No submitted requests yet.') + '</p>'
      return
    }
    div.innerHTML = ''
    const list = document.createElement('div')
    list.className = 'list-card'
    items.forEach((it, idx) => {
      const isLoan = it.item_type === 'loan'
      const row = document.createElement('div')
      row.className = 'list-item'
      row.style.flexWrap = 'wrap'
      row.id = 'req-row-' + idx
      const typeBadge = isLoan
        ? '<span class="badge" style="background:rgba(139,92,246,0.15);color:#c4b5fd">' + t('Loan Request') + '</span>'
        : '<span class="badge" style="background:rgba(59,130,246,0.15);color:#93c5fd">' + t('Payment') + '</span>'
      let subHtml
      if (isLoan) {
        subHtml = `${t('Loan')} ${formatCurrency(it.loan_amount || 0)} ${t('for')} ${it.loan_term_months || 0} ${t('mo')}`
      } else {
        const sa = Number(it.share_amount || 0)
        const la = Number(it.loan_principal || 0)
        const li = Number(it.loan_interest || 0)
        const fn = Number(it.fine || 0)
        const total = sa + la + li + fn
        const isCombined = sa > 0 && (la > 0 || li > 0 || fn > 0)
        let details = ''
        if (isCombined) {
          if (sa > 0) details += `<span style="color:#67e8f9">Share: ${formatCurrency(sa)}</span> `
          if (la > 0) details += `<span style="color:#86efac">${t('Loan Principal')}: ${formatCurrency(la)}</span> `
          if (li > 0) details += `<span style="color:#f59e0b">${t('Loan Interest')}: ${formatCurrency(li)}</span> `
          if (fn > 0) details += `<span style="color:#f97316">${t('Fine')}: ${formatCurrency(fn)}</span> `
          details += `<span style="color:#ffffff;font-weight:600">· Total: ${formatCurrency(total)}</span>`
        }
        const typeLabel = t('Payment')
        subHtml = isCombined ? details : `${typeLabel} ${formatCurrency(it.total_amount)}`
      }
      row.innerHTML = `
        <div>
          <strong>${it.member_name}</strong><br>
          <small>${subHtml}${it.note ? ' — ' + it.note : ''}</small><br>
          ${typeBadge}
        </div>
        <div>${!isLoan && it.screenshot ? `<a href="${it.screenshot}" target="_blank" style="color:#7dd3fc">${t('📎 Screenshot')}</a>` : ''}</div>
        <div id="req-actions-${idx}">
          <button class="btn primary approve-btn" style="padding:6px 12px;font-size:0.85rem">${t('Approve')}</button>
          <button class="btn secondary reject-btn" style="padding:6px 12px;font-size:0.85rem">${t('Reject')}</button>
        </div>
        <div id="req-reject-form-${idx}" class="reject-form hidden">
          <textarea id="reject-reason-${idx}" placeholder="${t('Reason for rejection...')}" rows="2"></textarea>
          <div class="reject-form-actions">
            <button class="btn primary" id="reject-confirm-${idx}" style="padding:6px 14px;font-size:0.85rem;background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">${t('Confirm Reject')}</button>
            <button class="btn secondary" id="reject-cancel-${idx}" style="padding:6px 14px;font-size:0.85rem">${t('Cancel')}</button>
          </div>
        </div>`
      const approverId = (state.currentUser && state.currentUser.member_id) || 0
      row.querySelector('.approve-btn').onclick = async () => {
        const confirmMsg = isLoan
          ? `Approve loan of ${formatCurrency(it.loan_amount)} for ${it.member_name}?`
          : `Approve payment of ${formatCurrency(it.total_amount)} from ${it.member_name}?`
        if (!(await showConfirm(t('Approve'), confirmMsg))) return
        const btn = row.querySelector('.approve-btn')
        setLoading(btn, true)
        try {
          const url = isLoan ? `/api/admin/approve_loan/${it.req_id}` : `/api/admin/approve_request/${it.req_id}`
          const res = await fetch(url, {method:'POST', headers: {'Content-Type':'application/json','X-ADMIN-TOKEN': (state.adminToken || '')}, body: JSON.stringify({approver_id: approverId})})
          if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(fundErrMsg(e) || e.error || t('Approve failed')) }
          showToast(isLoan ? t('Loan approved') : t('Payment approved'), 'success')
          await renderSubmittedRequests()
        } catch (e) { showToast(e.message, 'error') } finally { setLoading(btn, false) }
      }
      row.querySelector('.reject-btn').onclick = () => {
        document.getElementById('req-actions-' + idx).classList.add('hidden')
        document.getElementById('req-reject-form-' + idx).classList.remove('hidden')
      }
      row.querySelector('#reject-cancel-' + idx).onclick = () => {
        document.getElementById('req-actions-' + idx).classList.remove('hidden')
        document.getElementById('req-reject-form-' + idx).classList.add('hidden')
      }
      row.querySelector('#reject-confirm-' + idx).onclick = async () => {
        const btn = row.querySelector('#reject-confirm-' + idx)
        const reason = document.getElementById('reject-reason-' + idx).value.trim()
        if (!reason) { showToast(t('Enter a reason'), 'error'); return }
        setLoading(btn, true)
        try {
          const url = isLoan ? `/api/admin/reject_loan/${it.req_id}` : `/api/admin/reject_request/${it.req_id}`
          const res = await fetch(url, {method:'POST', headers: {'Content-Type':'application/json','X-ADMIN-TOKEN': (state.adminToken || '')}, body: JSON.stringify({approver_id: approverId, reason})})
          if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.error || 'Reject failed') }
          showToast(isLoan ? t('Loan rejected') : t('Payment rejected'), 'info')
          await renderSubmittedRequests()
        } catch (e) { showToast(e.message, 'error') } finally { setLoading(btn, false) }
      }
      list.appendChild(row)
    })
    div.appendChild(list)
  } catch (e) {
    div.innerHTML = '<p style="color:#ef4444">' + t('Error loading') + ': ' + (e.error || e) + '</p>'
  }
}

async function renderAllMembers() {
  await loadMembers()
  const cardColors = ['#3b82f6','#8b5cf6','#ec4899','#f59e0b','#10b981','#06b6d4','#f97316','#6366f1','#14b8a6','#e11d48','#84cc16','#d946ef']
  const cards = state.members.map((m, i) => {
    const color = cardColors[i % cardColors.length]
    const avatarHtml = m.photo_url
      ? `<div class="mc-avatar" style="background-image:url('${m.photo_url}')"></div>`
      : `<div class="mc-avatar mc-avatar-placeholder" style="background:${color}">${initials(m.name)}</div>`
    // Everyone can open other members' profiles; your own card is static
    // because your data lives in "My Account".
    const isSelf = state.currentUser && m.member_id === state.currentUser.member_id
    const viewable = state.currentUser && !isSelf
    return `<div class="member-card" ${viewable ? `onclick="renderMemberProfile(${m.member_id})" style="cursor:pointer"` : ''}>
      ${avatarHtml}
      <div class="mc-info">
        <div class="mc-name">${mName(m.name)}${m.is_admin ? ' ⭐' : ''}</div>
        <div class="mc-age">${m.dob ? calculateAge(m.dob) + ' yrs' : ''}</div>
        <div class="mc-phone">${m.phone || ''}</div>
      </div>
    </div>`
  }).join('')
  content.innerHTML = `
    <div class="panel">
      <div class="member-grid">${cards}</div>
    </div>
  `
}

async function renderPassbook() {
  content.innerHTML = '<div class="panel pb-page"><div id="pb-active-filters" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;min-height:0"></div><div id="pb-list" style="overflow-x:auto">' + loadingHtml() + '</div></div>'
  await loadPbData()
}

let pbData = []
let pbRows = []
let pbSortCol = 'ts'
let pbSortDir = -1
let pbFilters = {}

const SPLIT_COMPONENTS = [
  { key: 'share', label: 'Share' },
  { key: 'fine', label: 'Fine' },
  { key: 'loan_interest', label: 'Loan Interest' },
  { key: 'loan_principal', label: 'Loan Principal' },
]

function pbExpandRows(data) {
  const out = []
  data.forEach(r => {
    if (r.split) {
      SPLIT_COMPONENTS.forEach(c => {
        const v = Number(r.split[c.key] || 0)
        if (v > 0) out.push({ ts: r.ts, category: c.label, member_name: r.member_name, amount: v, debit_credit: 'credit', comp: c.key })
      })
    } else {
      out.push(r)
    }
  })
  return out
}

async function loadPbData() {
  try {
    pbData = await api('/admin/passbook')
    pbRows = pbExpandRows(pbData)
    applyPbFilters()
  } catch (e) {
    document.getElementById('pb-list').innerHTML = '<p style="color:#ef4444">Error loading passbook</p>'
  }
}

function pbSortIcon(col) {
  const hasFilter = Object.keys(pbFilters).some(k => k.startsWith(col) || (col === 'ts' && (k === 'from' || k === 'to')) || (col === 'amount' && (k.startsWith('amt'))))
  return (pbSortCol === col ? (pbSortDir === -1 ? ' ▾' : ' ▴') : ' ↕') + (hasFilter ? '●' : '')
}

let pbFilterCol = null

function pbToggleFilter(col) {
  const existing = document.getElementById('pb-filter-panel')
  if (existing) { existing.remove(); document.removeEventListener('click', pbCloseOutside, true); return }
  pbFilterCol = col
  const th = document.querySelector(`#pb-list th[data-col="${col}"]`)
  if (!th) return
  const panel = document.createElement('div')
  panel.id = 'pb-filter-panel'
  panel.dataset.col = col
  panel.addEventListener('click', e => e.stopPropagation())
  th.style.position = 'relative'

  const sortRow = `
    <div style="display:flex;gap:6px;margin-bottom:10px;padding-bottom:10px;border-bottom:1px solid rgba(148,163,184,0.08)">
      <button class="pb-sort-btn" onclick="pbDoSort('${col}',1)">▲ Ascending</button>
      <button class="pb-sort-btn" onclick="pbDoSort('${col}',-1)">▼ Descending</button>
    </div>`

  const clearCol = `<button class="btn secondary" style="padding:5px 14px;font-size:0.78rem" onclick="pbClearColFilter('${col}')">Clear column filter</button>`

  let filterHtml = ''
  if (col === 'category') {
    const cats = [...new Set(pbRows.map(r => r.category || '(No type)'))].sort()
    const selected = pbFilters.category || []
    filterHtml = `<div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:6px">${t('Filter by Type')}</div>` +
      `<div style="max-height:200px;overflow-y:auto;margin-bottom:8px;scrollbar-width:thin">` +
      cats.map(c => `<label class="pb-flabel"><input type="checkbox" class="pb-cat-cb" value="${c}" ${selected.includes(c) ? 'checked' : ''} /> ${t(c) || c}</label>`).join('') +
      `</div>` +
      `<div style="display:flex;gap:6px"><button class="btn primary" style="padding:5px 14px;font-size:0.78rem" onclick="pbFilterCat()">Apply</button>${clearCol}</div>`
  } else if (col === 'member_name') {
    const names = [...new Set(pbRows.map(r => r.member_name || '(No member)'))].sort()
    const selected = pbFilters.member_name || []
    filterHtml = `<div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:6px">Filter by Member</div>` +
      `<div style="max-height:200px;overflow-y:auto;margin-bottom:8px;scrollbar-width:thin">` +
      names.map(n => `<label class="pb-flabel"><input type="checkbox" class="pb-name-cb" value="${n}" ${selected.includes(n) ? 'checked' : ''} /> ${n === 'Group Fund' ? t('Group Fund') : n}</label>`).join('') +
      `</div>` +
      `<div style="display:flex;gap:6px"><button class="btn primary" style="padding:5px 14px;font-size:0.78rem" onclick="pbFilterName()">Apply</button>${clearCol}</div>`
  } else if (col === 'ts') {
    filterHtml = `<div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:6px">Filter by Date Range</div>` +
      `<div style="display:flex;gap:6px;margin-bottom:6px"><input id="pb-from-input" type="text" class="admin-input" value="${pbFilters.from || ''}" placeholder="From" readonly /></div>` +
      `<div style="display:flex;gap:6px;margin-bottom:8px"><input id="pb-to-input" type="text" class="admin-input" value="${pbFilters.to || ''}" placeholder="To" readonly /></div>` +
      `<div style="display:flex;gap:6px"><button class="btn primary" style="padding:5px 14px;font-size:0.78rem" onclick="pbFilterDate()">Apply</button>${clearCol}</div>`
  } else if (col === 'amount') {
    filterHtml = `<div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:8px">Filter by Amount</div>` +
      `<div style="display:flex;gap:8px;margin-bottom:8px">` +
      `<label class="pb-flabel" style="flex:1;justify-content:center;padding:6px 0"><input type="checkbox" class="pb-amt-cb" value="credit" ${pbFilters.amtCredit ? 'checked' : ''} /> Credit</label>` +
      `<label class="pb-flabel" style="flex:1;justify-content:center;padding:6px 0"><input type="checkbox" class="pb-amt-cb" value="debit" ${pbFilters.amtDebit ? 'checked' : ''} /> Debit</label>` +
      `</div>` +
      `<div style="display:flex;gap:6px;margin-bottom:6px"><input id="pb-amt-min" type="text" inputmode="decimal" placeholder="Min amount" style="flex:1;padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);color:#f8fafc;font-size:0.82rem" value="${pbFilters.amtMin || ''}" /></div>` +
      `<div style="display:flex;gap:6px;margin-bottom:6px"><input id="pb-amt-max" type="text" inputmode="decimal" placeholder="Max amount" style="flex:1;padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);color:#f8fafc;font-size:0.82rem" value="${pbFilters.amtMax || ''}" /></div>` +
      `<div style="display:flex;gap:6px;margin-bottom:8px"><input id="pb-amt-exact" type="text" inputmode="decimal" placeholder="Exact amount" style="flex:1;padding:8px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.03);color:#f8fafc;font-size:0.82rem" value="${pbFilters.amtExact || ''}" /></div>` +
      `<div style="display:flex;gap:6px"><button class="btn primary" style="padding:5px 14px;font-size:0.78rem" onclick="pbFilterAmount()">Apply</button>${clearCol}</div>`
  }

  panel.innerHTML = sortRow + filterHtml
  panel.style.cssText = 'z-index:20;width:270px;background:rgba(12,18,34,0.98);border:1px solid rgba(148,163,184,0.12);border-radius:14px;padding:14px;backdrop-filter:blur(12px);box-shadow:0 24px 60px rgba(0,0,0,0.5);overflow-y:auto;scrollbar-width:thin;max-height:' + (window.innerHeight - 16) + 'px'
  document.body.appendChild(panel)
  const r = th.getBoundingClientRect()
  const sx = window.scrollX || window.pageXOffset
  const sy = window.scrollY || window.pageYOffset
  // Anchor in document coordinates so the panel travels with its column
  // header when the passbook scrolls behind it.
  panel.style.position = 'absolute'
  const ph = panel.offsetHeight
  let vpLeft = Math.max(4, Math.min(r.left + r.width/2 - 135, window.innerWidth - 278))
  let vpTop = r.bottom + 4
  if (vpTop + ph > window.innerHeight - 8) {
    const upSpace = r.top - 8
    if (upSpace >= 200) {
      vpTop = Math.max(8, r.top - Math.min(ph, upSpace) - 4)
    } else {
      vpTop = Math.max(8, window.innerHeight - Math.min(ph, window.innerHeight - 16) - 8)
    }
  }
  panel.style.left = (vpLeft + sx) + 'px'
  panel.style.top = (vpTop + sy) + 'px'
  ;['pb-amt-min', 'pb-amt-max', 'pb-amt-exact'].forEach(id => {
    const el = document.getElementById(id)
    if (el) indianizeInput(el)
  })
  ;['pb-from-input', 'pb-to-input'].forEach(id => {
    const el = document.getElementById(id)
    if (el) createDatePicker(el)
  })
  document.addEventListener('click', pbCloseOutside, true)
}

function pbDoSort(col, dir) {
  pbSortCol = col; pbSortDir = dir
  pbCloseFilter()
  applyPbFilters()
}

function pbCloseFilter() {
  const p = document.getElementById('pb-filter-panel')
  if (p) p.remove()
  document.removeEventListener('click', pbCloseOutside, true)
}

function pbCloseOutside(e) {
  // Month/year nav popups live outside the calendar container; treat taps
  // there as "inside" so choosing a month/year doesn't kill the filter panel.
  if (!e.target.closest('#pb-filter-panel') && !e.target.closest('.pb-sortable') && !e.target.closest('.flatpickr-calendar') && !e.target.closest('.flatpickr-nav-pop') && !e.target.closest('.flatpickr-nav-btn')) pbCloseFilter()
}

function pbClearColFilter(col) {
  if (col === 'category') delete pbFilters.category
  else if (col === 'member_name') delete pbFilters.member_name
  else if (col === 'ts') { delete pbFilters.from; delete pbFilters.to }
  else if (col === 'amount') { delete pbFilters.amtCredit; delete pbFilters.amtDebit; delete pbFilters.amtMin; delete pbFilters.amtMax; delete pbFilters.amtExact }
  pbCloseFilter()
  applyPbFilters()
}

function pbClearAllFilters() {
  pbFilters = {}
  pbCloseFilter()
  applyPbFilters()
}

function pbRemoveFilterValue(key, value) {
  if (Array.isArray(pbFilters[key])) {
    pbFilters[key] = pbFilters[key].filter(v => v !== value)
    if (!pbFilters[key].length) delete pbFilters[key]
  } else {
    delete pbFilters[key]
  }
  applyPbFilters()
}

function pbFilterCat() {
  const checked = [...document.querySelectorAll('.pb-cat-cb:checked')].map(cb => cb.value)
  if (checked.length) pbFilters.category = checked
  else delete pbFilters.category
  pbCloseFilter()
  applyPbFilters()
}

function pbFilterName() {
  const checked = [...document.querySelectorAll('.pb-name-cb:checked')].map(cb => cb.value)
  if (checked.length) pbFilters.member_name = checked
  else delete pbFilters.member_name
  pbCloseFilter()
  applyPbFilters()
}

function pbFilterDate() {
  const f = document.getElementById('pb-from-input').value
  const t = document.getElementById('pb-to-input').value
  if (f) pbFilters.from = f; else delete pbFilters.from
  if (t) pbFilters.to = t; else delete pbFilters.to
  pbCloseFilter()
  applyPbFilters()
}

function pbFilterAmount() {
  const checked = [...document.querySelectorAll('.pb-amt-cb:checked')].map(cb => cb.value)
  if (checked.includes('credit')) pbFilters.amtCredit = true; else delete pbFilters.amtCredit
  if (checked.includes('debit')) pbFilters.amtDebit = true; else delete pbFilters.amtDebit
  const min = document.getElementById('pb-amt-min').value.replace(/,/g, '')
  const max = document.getElementById('pb-amt-max').value.replace(/,/g, '')
  const exact = document.getElementById('pb-amt-exact').value.replace(/,/g, '')
  if (min) pbFilters.amtMin = parseFloat(min); else delete pbFilters.amtMin
  if (max) pbFilters.amtMax = parseFloat(max); else delete pbFilters.amtMax
  if (exact) pbFilters.amtExact = parseFloat(exact); else delete pbFilters.amtExact
  pbCloseFilter()
  applyPbFilters()
}

function applyPbFilters() {
  let filtered = pbRows
  Object.entries(pbFilters).forEach(([k, v]) => {
    if (k === 'category' && Array.isArray(v)) filtered = filtered.filter(r => v.includes(r.category || '(No type)'))
    if (k === 'member_name' && Array.isArray(v)) filtered = filtered.filter(r => v.includes(r.member_name || '(No member)'))
    if (k === 'from') filtered = filtered.filter(r => r.ts >= v + 'T00:00:00')
    if (k === 'to') filtered = filtered.filter(r => r.ts <= v + 'T23:59:59')
    if (k === 'amtCredit' || k === 'amtDebit') filtered = filtered.filter(r => (pbFilters.amtCredit && r.debit_credit === 'credit') || (pbFilters.amtDebit && r.debit_credit === 'debit'))
    if (k === 'amtMin') filtered = filtered.filter(r => parseFloat(r.amount) >= v)
    if (k === 'amtMax') filtered = filtered.filter(r => parseFloat(r.amount) <= v)
    if (k === 'amtExact') filtered = filtered.filter(r => parseFloat(r.amount) === v)
  })
  filtered.sort((a, b) => {
    let va = a[pbSortCol] || '', vb = b[pbSortCol] || ''
    if (pbSortCol === 'amount') { va = parseFloat(va); vb = parseFloat(vb) }
    else if (pbSortCol === 'ts') { va = va.replace(/\s/g, '').replace(/T/g, ' '); vb = vb.replace(/\s/g, '').replace(/T/g, ' ') }
    else { va = va.toString().toLowerCase(); vb = vb.toString().toLowerCase() }
    if (va < vb) return -pbSortDir
    if (va > vb) return pbSortDir
    return 0
  })

  const filtersDiv = document.getElementById('pb-active-filters')
  if (filtersDiv) {
    const chips = []
    Object.entries(pbFilters).forEach(([k, v]) => {
      let label = ''
      if (k === 'category' || k === 'member_name') {
        if (Array.isArray(v)) v.forEach(val => chips.push({key:k, val, label:(k==='category'?'Type':'Member')+': '+(val==='Group Fund'?t('Group Fund'):val)}))
      } else if (k === 'from') chips.push({key:k, val:null, label:'From: '+v})
      else if (k === 'to') chips.push({key:k, val:null, label:'To: '+v})
      else if (k === 'amtCredit') chips.push({key:k, val:null, label:'Credit'})
      else if (k === 'amtDebit') chips.push({key:k, val:null, label:'Debit'})
      else if (k === 'amtMin') chips.push({key:k, val:null, label:'Min: '+v})
      else if (k === 'amtMax') chips.push({key:k, val:null, label:'Max: '+v})
      else if (k === 'amtExact') chips.push({key:k, val:null, label:'Exact: ₹'+v})
    })
    filtersDiv.innerHTML = chips.map(c =>
      '<span class="pb-chip" onclick="pbRemoveFilterValue(\'' + c.key + '\',\'' + (c.val || '').replace(/'/g, "\\'") + '\')">' + c.label + ' ✕</span>'
    ).join('') + (chips.length ? '<span class="pb-chip pb-chip-clear" onclick="pbClearAllFilters()">✕ Clear all filters</span>' : '')
    filtersDiv.style.minHeight = chips.length ? '28px' : '0'
  }

  const listDiv = document.getElementById('pb-list')
  if (!filtered.length) { listDiv.innerHTML = '<p style="color:#64748b;text-align:center;padding:30px 0">' + t('No entries match filters.') + '</p>'; return }
  const sumByCat = {}
  filtered.forEach(r => { const c = r.category || '(No type)'; sumByCat[c] = (sumByCat[c] || 0) + parseFloat(r.amount || 0) })
  const compTotals = Object.keys(sumByCat).sort().map(c => `${t(c) || c} ${formatCurrency(sumByCat[c])}`).join(' · ')
  const totalsHtml = compTotals ? `<div style="font-size:0.8rem;color:#e2e8f0;font-weight:600;padding:10px 4px 0;border-top:1px solid rgba(148,163,184,0.12);margin-top:4px">${t('Totals')}: ${compTotals}</div>` : ''
  listDiv.innerHTML = '<p style="font-size:0.78rem;color:#64748b;margin:0 0 6px">' + filtered.length + ' ' + t('entries') + '</p>' +
    '<table class="table"><thead><tr>' +
    '<th class="pb-sortable" data-col="ts" onclick="pbToggleFilter(\'ts\')">' + t('Date & Time') + ' <span class="pb-sort-arr">' + pbSortIcon('ts') + '</span></th>' +
    '<th class="pb-sortable" data-col="category" onclick="pbToggleFilter(\'category\')">' + t('Type') + ' <span class="pb-sort-arr">' + pbSortIcon('category') + '</span></th>' +
    '<th class="pb-sortable" data-col="member_name" onclick="pbToggleFilter(\'member_name\')">' + t('Member') + ' <span class="pb-sort-arr">' + pbSortIcon('member_name') + '</span></th>' +
    '<th class="pb-sortable" style="text-align:right" data-col="amount" onclick="pbToggleFilter(\'amount\')">' + t('Amount') + ' <span class="pb-sort-arr">' + pbSortIcon('amount') + '</span></th>' +
    '</tr></thead><tbody>' +
    filtered.slice(0, 500).map(r => {
      const cls = r.debit_credit === 'credit' ? '#34d399' : '#fca5a5'
      const sign = r.debit_credit === 'credit' ? '+' : '−'
      const dp = formatDateParts(r.ts)
      const catText = t(r.category) || r.category
      const cw = String(catText).split(' ')
      const catHtml = cw.length > 1 ? `<span class="pb-tw-a">${escHtml(cw[0])}</span> <span class="pb-tw-b">${escHtml(cw.slice(1).join(' '))}</span>` : escHtml(catText)
      const typeHtml = `<span class="pb-badge ${r.category.toLowerCase().replace(/\s+/g,'-')}">${catHtml}</span>`
      const rawName = r.member_name === 'Group Fund' ? t('Group Fund') : (r.member_name || '-')
      const nw = rawName.split(' ')
      const nmHtml = nw.length > 1 ? `<span class="pb-nm-a">${escHtml(nw[0])}</span><span class="pb-nm-b">${escHtml(nw.slice(1).join(' '))}</span>` : escHtml(rawName)
      return `<tr>
        <td class="pb-date-cell" style="white-space:nowrap;font-size:0.8rem">${dp.date}<span class="pb-time"> ${dp.time}</span></td>
        <td>${typeHtml}</td>
        <td class="pb-name-cell" style="color:#94a3b8">${nmHtml}</td>
        <td style="text-align:right;font-weight:700;color:${cls}">${sign} ${formatCurrency(r.amount)}</td>
      </tr>`
    }).join('') + '</tbody></table>' + totalsHtml
}

async function renderAllHistory() {
  const m = await api(`/members/${state.currentUser.member_id}`)
  // Unified request history from m.requests
  const normDate = (s) => s && !String(s).includes('T') ? String(s) + 'T00:00:00' : String(s)
  const requestRows = []
  ;(m.requests || []).forEach(r => {
    const isLoan = r.item_type === 'loan'
    const typeLabel = isLoan ? t('Loan Application') : t('Payment')
    const amount = isLoan ? (r.loan_amount || 0) : (r.total_amount || 0)
    let statusColor, statusText, statusDate, statusTime, comment
    if (r.status === 'approved') {
      statusColor = '#34d399'; statusText = t('Approved')
      const sp = r.approved_date ? formatDateParts(r.approved_date) : {date:'',time:''}
      statusDate = sp.date; statusTime = sp.time
      comment = ''
    } else if (r.status === 'rejected') {
      statusColor = '#f87171'; statusText = t('Rejected')
      const sp = r.rejected_date ? formatDateParts(r.rejected_date) : {date:'',time:''}
      statusDate = sp.date; statusTime = sp.time
      comment = r.reject_reason || ''
    } else {
      statusColor = '#94a3b8'; statusText = t('Submitted')
      statusDate = ''; statusTime = ''; comment = ''
    }
    requestRows.push({ sortKey: normDate(r.date_submitted), date: r.date_submitted, type: typeLabel, amount, statusColor, statusText, statusDate, statusTime, comment })
  })
  requestRows.sort((a, b) => b.sortKey.localeCompare(a.sortKey))
  const rowsHtml = requestRows.length ? requestRows.map(r => {
    const dp = formatDateParts(r.date ? (r.date.includes('T') ? r.date : r.date + 'T00:00:00') : '')
    return `<tr>
      <td class="act-date-cell" style="white-space:nowrap;font-size:0.8rem">${dp.date}<span class="act-time"> ${dp.time}</span></td>
      <td class="act-type-cell">${r.type}</td>
      <td style="white-space:nowrap">${formatCurrency(r.amount)}</td>
      <td class="act-status-cell"><span style="color:${r.statusColor};font-weight:600">${r.statusText}</span><br/><span class="act-status-dt"><span class="act-status-date">${r.statusDate}</span> <span class="act-status-time">${r.statusTime}</span></span></td>
      <td class="act-comment-cell" style="font-size:0.82rem;color:#94a3b8">${r.comment}</td>
    </tr>`
  }).join('') : `<tr><td colspan="5" style="text-align:center;color:#94a3b8;">${t('No history yet')}</td></tr>`
  content.innerHTML = `
    <div class="panel">
      <div class="table-scroll activity-scroll">
        <table class="table"><thead><tr><th>${t('Date')}</th><th>${t('Type')}</th><th>${t('Amount')}</th><th>${t('Status')}</th><th>${t('Comments')}</th></tr></thead><tbody>${rowsHtml}</tbody></table>
      </div>
    </div>
  `
}

function passwordFormFields() {
  return `
    <p style="font-size:0.85rem;color:#94a3b8;margin-bottom:10px">${t('Change your password')}</p>
    <div style="margin-bottom:8px"><input id="pw-current" type="password" placeholder="${t('Current password')}" style="width:100%;padding:10px;border-radius:8px;border:1px solid rgba(148,163,184,0.15);background:rgba(15,23,42,0.9);color:#f8fafc" /></div>
    <div style="margin-bottom:8px"><input id="pw-new" type="password" placeholder="${t('New password')}" style="width:100%;padding:10px;border-radius:8px;border:1px solid rgba(148,163,184,0.15);background:rgba(15,23,42,0.9);color:#f8fafc" /></div>
    <div style="margin-bottom:12px"><input id="pw-confirm" type="password" placeholder="${t('Confirm new password')}" style="width:100%;padding:10px;border-radius:8px;border:1px solid rgba(148,163,184,0.15);background:rgba(15,23,42,0.9);color:#f8fafc" /></div>
    <div style="display:flex;gap:8px"><button class="btn primary" id="pw-save-btn">${t('Save')}</button><button class="btn" id="pw-cancel-btn">${t('Cancel')}</button></div>
  `
}

function wirePasswordForm(memberId, onDone) {
  document.getElementById('pw-save-btn').onclick = async () => {
    const cur = document.getElementById('pw-current').value
    const nw = document.getElementById('pw-new').value
    const conf = document.getElementById('pw-confirm').value
    if (!cur || !nw) { showToast(t('Fill all fields'), 'error'); return }
    if (nw !== conf) { showToast(t('Passwords do not match'), 'error'); return }
    setLoading(document.getElementById('pw-save-btn'), true)
    try {
      await api(`/members/${memberId}/self`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({current_password: cur, password: nw}),
      })
      showToast(t('Password changed'), 'success')
      onDone()
    } catch (err) {
      showToast(err.error || 'Failed to change password', 'error')
    } finally {
      setLoading(document.getElementById('pw-save-btn'), false)
    }
  }
  document.getElementById('pw-cancel-btn').onclick = () => onDone()
}

function openPasswordForm(memberId, mode) {
  if (document.getElementById('pw-change-form')) return
  const copy = document.querySelector('.profile-copy')
  if (!copy) return
  const div = document.createElement('div')
  div.id = 'pw-change-form'
  div.style.marginTop = '12px'
  div.style.padding = '12px'
  div.style.borderRadius = '10px'
  div.style.background = 'rgba(255,255,255,0.03)'
  div.innerHTML = passwordFormFields()
  copy.appendChild(div)
  wirePasswordForm(memberId, () => renderMemberProfile(memberId, mode))
}

async function renderChangePassword() {
  content.innerHTML = loadingHtml()
  await api(`/members/${state.currentUser.member_id}`)
  content.innerHTML = `
    <div class="profile-wrapper">
      <div class="profile-card">
        <div class="profile-copy" style="width:100%">
          <h2 style="margin-bottom:16px;">🔒 ${t('Change Password')}</h2>
          <div class="pc-details">
            <div class="pc-left" style="width:100%">
              ${passwordFormFields()}
            </div>
          </div>
        </div>
      </div>
    </div>
  `
  wirePasswordForm(state.currentUser.member_id, () => setView('my-profile'))
}

// ===== Custom themed dropdowns: replace every native <select> popup with a
// picker matching the app theme (the OS-drawn native list can't be styled) =====
// Business "today" in India, independent of the device's own timezone/clock —
// toISOString() would return UTC, which lags IST by 5h30m before sunrise.
function istTodayStr() {
  try {
    return new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(new Date())
  } catch (e) { return new Date().toISOString().slice(0, 10) }
}
let selPopsWired = false
function closeSelPops() {
  document.querySelectorAll('.sel-pop.open').forEach(p => p.classList.remove('open'))
}
function enhanceAllSelects(root) {
  ;(root || document).querySelectorAll('select').forEach(sel => {
    if (sel.dataset.enhanced || sel.closest('.flatpickr-calendar')) return
    sel.dataset.enhanced = '1'
    const wrap = document.createElement('div')
    wrap.style.position = 'relative'
    sel.parentNode.insertBefore(wrap, sel)
    wrap.appendChild(sel)
    sel.style.display = 'none'
    const btn = document.createElement('button')
    btn.type = 'button'
    btn.className = 'sel-btn'
    const caret = document.createElement('span')
    caret.className = 'sel-caret'
    caret.textContent = '▾'
    wrap.appendChild(btn)
    wrap.appendChild(caret)
    const pop = document.createElement('div')
    pop.className = 'sel-pop'
    document.body.appendChild(pop)
    const syncBtn = () => {
      const o = sel.options[sel.selectedIndex]
      btn.textContent = o ? o.textContent : ''
      pop.querySelectorAll('.sel-opt').forEach(p =>
        p.classList.toggle('selected', p.dataset.v === String(sel.value)))
    }
    Array.from(sel.options).forEach(o => {
      const ob = document.createElement('button')
      ob.type = 'button'
      ob.className = 'sel-opt'
      ob.dataset.v = o.value
      ob.textContent = o.textContent
      ob.addEventListener('click', e => {
        e.stopPropagation()
        sel.value = o.value
        syncBtn()
        closeSelPops()
        sel.dispatchEvent(new Event('change', { bubbles: true }))
      })
      pop.appendChild(ob)
    })
    const open = () => {
      closeSelPops()
      const r = btn.getBoundingClientRect()
      const sx = window.scrollX || window.pageXOffset
      const sy = window.scrollY || window.pageYOffset
      pop.classList.add('open')
      pop.style.minWidth = Math.max(r.width, 160) + 'px'
      const h = pop.offsetHeight
      let top = r.bottom + sy + 4
      if (top + h > sy + window.innerHeight - 8) top = Math.max(sy + 8, r.top + sy - h - 4)
      pop.style.left = (r.left + sx) + 'px'
      pop.style.top = top + 'px'
      pop.scrollTop = 0
    }
    // Taps inside the popup must not reach outside-click closers (flatpickr etc.)
    ;['mousedown', 'mouseup', 'click', 'touchstart', 'focusin'].forEach(ev =>
      pop.addEventListener(ev, e => e.stopPropagation()))
    // Swallow wheel/touch that the list can't use instead of scrolling the page
    pop.addEventListener('wheel', e => {
      const room = pop.scrollHeight - pop.clientHeight
      if (room <= 0 || (e.deltaY > 0 ? pop.scrollTop >= room - 1 : pop.scrollTop <= 1)) e.preventDefault()
    }, { passive: false })
    let ty = 0
    pop.addEventListener('touchstart', e => { ty = e.touches[0].clientY }, { passive: true })
    pop.addEventListener('touchmove', e => {
      const room = pop.scrollHeight - pop.clientHeight
      const up = ty - e.touches[0].clientY > 0
      if (room <= 0 || (up ? pop.scrollTop >= room - 1 : pop.scrollTop <= 1)) e.preventDefault()
    }, { passive: false })
    btn.addEventListener('click', e => {
      e.preventDefault()
      e.stopPropagation()
      if (pop.classList.contains('open')) closeSelPops()
      else open()
    })
    syncBtn()
  })
  if (!selPopsWired) {
    document.addEventListener('click', e => {
      if (!e.target.closest('.sel-wrap') && !e.target.closest('.sel-pop')) closeSelPops()
    }, true)
    selPopsWired = true
  }
}

// ===== Custom themed dropdowns end =====

async function renderMemberProfile(memberId, mode) {
  if (!mode) {
    mode = state.activeView === 'my-accounts' ? 'accounts' : (state.activeView === 'my-profile' ? 'details' : undefined)
  }
  state.selectedMember = memberId
  content.innerHTML = loadingHtml()
  const m = await api(`/members/${memberId}`)
  const own = state.currentUser.member_id === m.member_id
  const canManage = own || state.currentUser.is_admin
  // Calculate repaid and interest per loan
  const repaidByLoan = {}
  const interestByLoan = {}
  ;(m.payments || []).forEach(p => {
    if (p.loan_id) {
      repaidByLoan[p.loan_id] = (repaidByLoan[p.loan_id] || 0) + (p.loan_principal || p.total_amount || 0)
      interestByLoan[p.loan_id] = (interestByLoan[p.loan_id] || 0) + (p.loan_interest || 0)
    }
  })
  let loansCardsHtml
  try {
    loansCardsHtml = m.loans && m.loans.filter(l => l.status === 'active').length ? m.loans.filter(l => l.status === 'active').map(l => {
    const statusBadge = '<span class="badge success">Active</span>'
    const takenDate = l.disbursed_date || l.last_accrual_date || ''
    const repaid = repaidByLoan[l.loan_id] || 0
    const interestPaid = interestByLoan[l.loan_id] || 0
    const loanPayments = (m.payments || []).filter(p => p.loan_id === l.loan_id)
    const paidMonths = new Set(loanPayments.map(p => (p.pay_date || '').slice(0, 7))).size
    let closeDate = '-'
    if (l.disbursed_date && l.term_months) {
      const d = new Date(l.disbursed_date)
      d.setMonth(d.getMonth() + l.term_months)
      closeDate = formatDate(d.toISOString().slice(0, 10))
    }
    const pct = l.loan_principal > 0 ? Math.round((repaid / l.loan_principal) * 100) : 0
    const displayPct = Math.min(pct, 100)
    const progressClass = displayPct >= 80 ? '' : (displayPct >= 40 ? 'warn' : '')
    const interestRate = l.rate_monthly ? (l.rate_monthly * 100) + '%' : '1%'
    return `
      <div class="loan-card">
        <div class="lc-top">
          <div class="lc-top-left">
            <span class="loan-id">💰 Loan #${l.loan_id}</span>
            ${statusBadge}
            <span style="font-size:0.75rem;color:#64748b;margin-left:4px;">${interestRate}/mo</span>
          </div>
        </div>
        <div class="lc-grid">
          <div class="lc-cell lc-amount"><span class="lc-label">${t('Loan Principal')}</span><span class="lc-value lc-value-lg">${formatCurrency(l.loan_principal)}</span></div>
          <div class="lc-cell lc-repaid"><span class="lc-label">Total Paid</span><span class="lc-value lc-value-lg">${formatCurrency(repaid)}</span></div>
          <div class="lc-cell lc-taken"><span class="lc-label">Taken Date</span><span class="lc-value">${takenDate ? formatDate(takenDate) : '-'}</span></div>
          <div class="lc-cell lc-close"><span class="lc-label">Close Date</span><span class="lc-value">${closeDate}</span></div>
          <div class="lc-cell lc-outstanding"><span class="lc-label">Outstanding</span><span class="lc-value">${formatCurrency(l.outstanding)}</span></div>
          <div class="lc-cell lc-interest"><span class="lc-label">${t('Loan Interest')} Paid</span><span class="lc-value">${interestPaid > 0 ? formatCurrency(interestPaid) : '-'}</span></div>
          <div class="lc-cell lc-term lc-full"><span class="lc-label">Term</span><span class="lc-value">${paidMonths} / ${l.term_months || '?'} months</span></div>
        </div>
        <div class="lc-progress-row">
          <span class="lc-progress-pct">${displayPct}% repaid</span>
          <div class="progress-bar"><div class="progress-fill ${progressClass}" style="width:${displayPct}%"></div></div>
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
      <div id="profile-avatar" class="profile-avatar ${avatarUrl ? 'has-photo' : ''} ${own ? 'clickable' : ''}" style="${avatarUrl ? `background-image: url('${avatarUrl}')` : ''}"><span class="avatar-init">${initials(m.name)}</span></div>
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
        <div class="pc-details">
          <div class="pc-left">
            <p><strong>Phone:</strong> <span class="input-readonly" id="ro-phone">${m.phone || '-'}</span></p>
            <p><strong>DOB:</strong> <span class="input-readonly" id="ro-dob">${m.dob ? formatDate(m.dob) : '-'}</span></p>
            <p><strong>Age:</strong> <span class="input-readonly">${calculateAge(m.dob)}</span></p>
            <p><strong>Address:</strong> <span class="input-readonly" id="ro-address">${m.address || '-'}</span></p>
            ${own ? `<div style="margin-top:6px;display:flex;gap:8px;flex-wrap:wrap"><button class="btn" id="self-edit-btn">Edit Profile</button>${mode !== 'details' ? `<button class="btn secondary" id="change-pw-btn">Change Password</button>` : ''}</div>` : ''}
          </div>
        </div>
      </div>
    </div>
  `
  // Build unified payment history from the single payments table (share + loan + interest + fine)
  const historyByDate = {}
  ;(m.payments || []).forEach(p => {
    const key = (p.pay_date || '').slice(0, 10)
    if (!historyByDate[key]) historyByDate[key] = { date: key, share: 0, loanPrincipal: 0, loanInterest: 0, fine: 0 }
    historyByDate[key].share += (p.share_amount || 0)
    historyByDate[key].loanPrincipal += (p.loan_principal || 0)
    historyByDate[key].loanInterest += (p.loan_interest || 0)
    historyByDate[key].fine += (p.fine || 0)
  })
  const allHistory = Object.values(historyByDate).sort((a, b) => b.date.localeCompare(a.date))
  const paymentHistory = allHistory.filter(r => r.share > 0 || r.loanPrincipal > 0 || r.loanInterest > 0 || r.fine > 0)
  const totalShare = allHistory.reduce((s, r) => s + r.share, 0)
  const totalLoanPaid = allHistory.reduce((s, r) => s + r.loanPrincipal, 0)
  const totalInterest = allHistory.reduce((s, r) => s + r.loanInterest, 0)
  const totalFine = allHistory.reduce((s, r) => s + r.fine, 0)
  let historyHeader = `<div class="history-totals"><span class="ht-chip ht-label">${t('Total')}</span><span class="ht-chip">${t('Share')} <strong>${formatCurrency(totalShare)}</strong></span><span class="ht-chip">${t('Loan Principal')} <strong>${formatCurrency(totalLoanPaid)}</strong></span>`
  if (totalInterest > 0) historyHeader += `<span class="ht-chip">${t('Loan Interest')} <strong>${formatCurrency(totalInterest)}</strong></span>`
  if (totalFine > 0) historyHeader += `<span class="ht-chip">${t('Fine')} <strong>${formatCurrency(totalFine)}</strong></span>`
  historyHeader += '</div>'
  const paymentTableHtml = `<table class="table"><thead><tr><th>Date</th><th>Share</th><th>${t('Loan Principal')}</th><th>${t('Loan Interest')}</th><th>Fine</th><th>Total</th></tr></thead><tbody>${paymentHistory.map(r => `<tr><td>${window.innerWidth <= 640 ? formatDateCompact(r.date) : formatDate(r.date)}</td><td>${r.share ? `<span style="color:#67e8f9">${formatCurrency(r.share)}</span>` : '-'}</td><td>${r.loanPrincipal ? `<span style="color:#86efac">${formatCurrency(r.loanPrincipal)}</span>` : '-'}</td><td>${r.loanInterest ? `<span style="color:#f59e0b">${formatCurrency(r.loanInterest)}</span>` : '-'}</td><td>${r.fine ? `<span style="color:#f97316">${formatCurrency(r.fine)}</span>` : '-'}</td><td style="color:#e2e8f0;font-weight:600">${formatCurrency(r.share + r.loanPrincipal + r.loanInterest + r.fine)}</td></tr>`).join('')}</tbody></table>`

  const compactHeader = !own && window.innerWidth <= 640
  const compactHeaderHtml = `
    <div class="profile-card compact-header">
      <div id="mini-avatar" class="profile-avatar ${avatarUrl ? 'has-photo' : ''}" style="${avatarUrl ? `background-image: url('${avatarUrl}')` : ''}"><span class="avatar-init">${initials(m.name)}</span></div>
      <div class="profile-copy">
        <h2>${m.name}</h2>
        <span class="compact-toggle" id="compact-toggle">${t('View details')} ▾</span>
        <div class="pc-details" id="compact-details" style="display:none">
          <div class="pc-left">
            <p><strong>Phone:</strong> ${m.phone || '-'}</p>
            <p><strong>DOB:</strong> ${m.dob ? formatDate(m.dob) : '-'}</p>
            <p><strong>Age:</strong> ${calculateAge(m.dob)}</p>
            <p><strong>Address:</strong> ${m.address || '-'}</p>
          </div>
        </div>
      </div>
    </div>
  `

  if (mode === 'details') {
    content.innerHTML = `
      <div class="profile-wrapper">
        ${profileFields}
      </div>
    `
  } else if (mode === 'accounts') {
    content.innerHTML = `
      <div class="profile-grid">
        <div class="panel payments-panel" style="margin-bottom:12px;">
          <h3 style="margin:0 0 10px;">📊 Payment History</h3>
          ${historyHeader}
          <div class="table-scroll">
            ${paymentTableHtml}
          </div>
        </div>
        <div class="panel compact-panel" id="loans-panel">
          <h3 style="margin-bottom:10px;">🏦 Loans</h3>
          ${loansCardsHtml}
        </div>
      </div>
    `
  } else {
    content.innerHTML = `
      <div class="profile-wrapper">
        ${compactHeader ? compactHeaderHtml : profileFields}
      </div>

      <div class="profile-grid">
        <div class="panel payments-panel" style="margin-bottom:12px;">
          <h3 style="margin:0 0 10px;">📊 Payment History</h3>
          ${historyHeader}
          <div class="table-scroll">
            ${paymentTableHtml}
          </div>
        </div>
        <div class="panel compact-panel" id="loans-panel">
          <h3 style="margin-bottom:10px;">🏦 Loans</h3>
          ${loansCardsHtml}
        </div>
      </div>
    `
  }
    // Compact header: tap the small photo / card to expand or collapse details
    const compactToggle = document.getElementById('compact-toggle')
    if (compactToggle) {
      const compactDetails = document.getElementById('compact-details')
      const miniAvatar = document.getElementById('mini-avatar')
      const toggleCompact = () => {
        const isOpen = compactDetails.style.display !== 'none'
        compactDetails.style.display = isOpen ? 'none' : 'block'
        compactToggle.textContent = isOpen ? (t('View details') + ' ▾') : (t('Hide details') + ' ▴')
        const header = compactToggle.closest('.compact-header')
        if (header) header.classList.toggle('expanded', !isOpen)
      }
      compactToggle.addEventListener('click', (e) => { e.stopPropagation(); toggleCompact() })
      if (miniAvatar) miniAvatar.addEventListener('click', (e) => { e.stopPropagation(); toggleCompact() })
      const header = compactToggle.closest('.compact-header')
      if (header) header.addEventListener('click', toggleCompact)
    }

    // Attach handlers for inline profile photo and edit/save flow
    const avatar = document.getElementById('profile-avatar')
    const photoInput = document.getElementById('profile-photo-input')
    const confirmBtn = document.getElementById('confirm-photo-btn')
    const cancelBtn = document.getElementById('cancel-photo-btn')
    const removeBtn = document.getElementById('remove-photo-btn')
    const editBtn = document.getElementById('self-edit-btn')
    let stagedBlob = null

    // avatar click opens a small visible menu (owner/admin) with clear actions
    const avatarMenu = document.getElementById('avatar-menu')
    const avatarAddBtn = document.getElementById('avatar-add-btn')
    const avatarRemoveBtn = document.getElementById('avatar-remove-btn')
    if (avatar && photoInput && own) {
      avatar.addEventListener('click', (ev) => {
        ev.stopPropagation()
        if (avatarMenu) avatarMenu.classList.toggle('hidden')
      })
      // Add new photo opens file picker
      if (avatarAddBtn) avatarAddBtn.addEventListener('click', () => { photoInput.click(); if (avatarMenu) avatarMenu.classList.add('hidden') })
      // Remove via avatar menu delegates to same remove flow
      if (avatarRemoveBtn) avatarRemoveBtn.addEventListener('click', async () => {
        if (!(await showConfirm('Remove Photo', 'Are you sure you want to remove your profile photo?'))) return
        await api(`/members/${m.member_id}/self`, {method:'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({photo_url: ''})})
        showToast('Photo removed', 'info')
        renderMemberProfile(m.member_id)
      })
      // clicking outside hides the menu
      // (delegated listener added once at init)
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
          avatar.classList.add('has-photo')
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
        setLoading(confirmBtn, true)
        const fd = new FormData()
        fd.append('photo', stagedBlob, 'photo.jpg')
        const res = await fetch(`/api/members/${m.member_id}/upload_photo`, {method: 'POST', body: fd})
        setLoading(confirmBtn, false)
        if (res.ok) { showToast(t('Photo uploaded'), 'success'); renderMemberProfile(m.member_id) } else { const e = await res.json().catch(()=>({})); showToast(e.error||t('Upload failed'),'error') }
      }
    }

    if (cancelBtn) {
      cancelBtn.onclick = () => {
        const inp = document.getElementById('profile-photo-input')
        if (inp) inp.value = ''
        stagedBlob = null
        if (m.photo_url) avatar.style.backgroundImage = `url('${m.photo_url}')`
        else { avatar.style.backgroundImage = ''; avatar.classList.remove('has-photo') }
        if (confirmBtn) confirmBtn.style.display = 'none'
        if (cancelBtn) cancelBtn.style.display = 'none'
      }
    }

    if (removeBtn) {
      // hidden until edit mode (legacy inline button)
      removeBtn.style.display = 'none'
      removeBtn.onclick = async () => {
        if (!confirm('Remove photo?')) return
        await api(`/members/${m.member_id}/self`, {method:'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({photo_url: ''})})
        showToast('Photo removed', 'info')
        renderMemberProfile(m.member_id)
      }
    }

    // Change password flow
    const pwBtn = document.getElementById('change-pw-btn')
    if (pwBtn) pwBtn.onclick = () => openPasswordForm(m.member_id, mode)

    // Edit flow: transform readonly fields into inputs when user clicks Edit
    if (editBtn) {
      editBtn.onclick = () => {
        const copy = document.querySelector('.profile-copy')
        const phoneSpan = copy.querySelector('#ro-phone')
        const dobSpan = copy.querySelector('#ro-dob')
        const addrSpan = copy.querySelector('#ro-address')
        if (!phoneSpan || !dobSpan || !addrSpan) return
        phoneSpan.outerHTML = `<input id="self-phone" class="input-edit" inputmode="tel" value="${m.phone||''}" />`
        addrSpan.outerHTML = `<input id="self-address" class="input-edit" value="${m.address||''}" />`
        editBtn.style.display = 'none'
        const dobWrap = document.createElement('span')
        dobWrap.style.cssText = 'position:relative;display:inline-block'
        const dobInput = document.createElement('input')
        dobInput.id = 'self-dob'
        dobInput.className = 'input-edit'
        dobInput.type = 'text'
        dobInput.value = m.dob || ''
        dobInput.readOnly = true
        dobWrap.appendChild(dobInput)
        dobSpan.parentNode.replaceChild(dobWrap, dobSpan)
        createDatePicker(dobInput)
        const btnWrap = document.createElement('div')
        btnWrap.style.marginTop = '8px'
        btnWrap.innerHTML = `<button class="btn primary" id="self-save-btn">Save</button> <button class="btn" id="self-cancel-btn">Cancel</button>`
        copy.appendChild(btnWrap)
        if (removeBtn) removeBtn.style.display = m.photo_url ? 'inline-block' : 'none'
        // bind save/cancel
        document.getElementById('self-save-btn').onclick = async () => {
          await handleUpdateDetails(m.member_id)
        }
        document.getElementById('self-cancel-btn').onclick = () => renderMemberProfile(m.member_id)
      }
    }

}

async function renderSubmitView() {
  content.innerHTML = loadingHtml()
  const m = await api(`/members/${state.currentUser.member_id}`)
  const today = istTodayStr()
  content.innerHTML = `
    <div class="grid-2" style="gap:20px;">
      <div class="panel compact-panel submit-panel">
        <h3>📤 ${t('Submit Proof of Payment')}</h3>
          <div class="input-row" style="display:flex;gap:12px;">
            <div style="flex:1">
              <label>${t('Share')} *</label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="share-amount-input" type="text" inputmode="decimal" value="500" /></div>
            </div>
            <div style="flex:1">
              <label>${t('Fine')} <span class="fine-hint">(${t('₹50/day after 10th')})</span></label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="fine-amount" type="text" inputmode="decimal" value="0" /></div>
            </div>
          </div>
          <div class="input-row" style="display:flex;gap:12px;">
            <div style="flex:1">
              <label>${t('Loan Principal')}</label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="loan-principal-input" type="text" inputmode="decimal" placeholder="0" /></div>
            </div>
            <div style="flex:1">
              <label>${t('Loan Interest')}</label>
              <div class="input-with-currency"><span class="currency">₹</span><input id="loan-interest-input" type="text" inputmode="decimal" placeholder="0" /></div>
            </div>
          </div>
          <div class="input-row" style="margin-top:4px;">
            <div style="flex:1;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.25);border-radius:8px;padding:10px 12px;display:flex;justify-content:space-between;align-items:center;">
              <span style="font-weight:600">${t('Total Amount')}</span>
              <strong id="submit-total-amount" style="font-size:1.1rem;color:#34d399">₹0</strong>
            </div>
          </div>
          <div class="input-row small-row">
            <label style="flex-basis:100%">${t('Payment Date')}</label>
            <input id="pay-txn-date" type="text" value="${today}" data-max="${today}" readonly />
          </div>
          <div class="input-row small-row"><input id="pay-note" placeholder="${t('Note (optional)')}" /></div>
          <div class="upload-area" id="upload-area">
            <input id="screenshot-input" type="file" accept="image/*" hidden />
            <div class="upload-placeholder">
              <span class="upload-icon">📎</span>
              <span class="upload-text">${t('Tap to upload receipt / proof')}</span>
              <span class="upload-hint">${t('Image only')}</span>
            </div>
            <div class="upload-preview hidden">
              <img id="upload-preview-img" />
              <span id="upload-filename"></span>
              <button class="upload-remove" id="upload-remove-btn" type="button">✕</button>
            </div>
          </div>
          <button class="btn primary" id="submit-payment-btn-top">${t('Submit Payment for Approval')}</button>
        </div>
        <div class="panel compact-panel">
          <h3>💰 ${t('Request Loan')}</h3>
          <div class="input-row"><label style="flex-basis:100%">${t('Loan Amount')}</label><div class="input-with-currency"><span class="currency">₹</span><input id="request-loan-amount" type="text" inputmode="decimal" placeholder="0" /></div></div>
          <div class="input-row" style="display:flex;gap:12px;">
            <div style="flex:1">
              <label style="font-size:0.8rem;color:#94a3b8;display:block;text-align:center;margin-bottom:2px;">${t('Years')}</label>
              <div class="stepper">
                <button class="stepper-btn" id="loan-years-down">−</button>
                <span class="stepper-value" id="loan-years-display">1</span>
                <button class="stepper-btn" id="loan-years-up">+</button>
              </div>
            </div>
            <div style="flex:1">
              <label style="font-size:0.8rem;color:#94a3b8;display:block;text-align:center;margin-bottom:2px;">${t('Months')}</label>
              <div class="stepper">
                <button class="stepper-btn" id="loan-months-down">−</button>
                <span class="stepper-value" id="loan-months-display">0</span>
                <button class="stepper-btn" id="loan-months-up">+</button>
              </div>
            </div>
          </div>
          <div id="loan-period-display" style="text-align:center;font-size:0.85rem;color:#94a3b8;margin-bottom:10px;">1 year 0 months</div>
          <button class="btn primary" id="request-loan-btn">Request Loan</button>
        </div>
      </div>
  `
  // Apply Indian number formatting to amount inputs
  ;['share-amount-input', 'loan-principal-input', 'loan-interest-input', 'request-loan-amount', 'fine-amount'].forEach(id => {
    const el = document.getElementById(id)
    if (el) indianizeInput(el)
  })
  const submitTotalEl = document.getElementById('submit-total-amount')
  const updateSubmitTotal = () => {
    const sum = ['share-amount-input', 'fine-amount', 'loan-principal-input', 'loan-interest-input'].reduce((acc, id) => {
      const el = document.getElementById(id)
      return acc + (Number((el ? el.value : '').replace(/,/g, '')) || 0)
    }, 0)
    if (submitTotalEl) submitTotalEl.textContent = formatCurrency(sum)
  }
  ;['share-amount-input', 'fine-amount', 'loan-principal-input', 'loan-interest-input'].forEach(id => {
    const el = document.getElementById(id)
    if (el) el.addEventListener('input', updateSubmitTotal)
  })
  updateSubmitTotal()
  const payDate = document.getElementById('pay-txn-date')
  if (payDate) createDatePicker(payDate)

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

  const submitPaymentBtn = document.getElementById('submit-payment-btn-top')
  if (submitPaymentBtn) {
    submitPaymentBtn.onclick = () => handleSubmitPayment(m.member_id)
  }
  // auto-calculate fine on date change
  const payDateInput = document.getElementById('pay-txn-date')
  const fineInput = document.getElementById('fine-amount')
  if (payDateInput && fineInput) {
    const calcFine = () => {
      const day = new Date(payDateInput.value).getDate()
      fineInput.value = toIndianNumber(String(day > 10 ? (day - 10) * 50 : 0))
    }
    payDateInput.addEventListener('change', calcFine)
    calcFine()
  }
  // loan request button handler
  const requestLoanBtn = document.getElementById('request-loan-btn')
  if (requestLoanBtn) {
    let loanYears = 1, loanMonths = 0
    const yearsDisplay = document.getElementById('loan-years-display')
    const monthsDisplay = document.getElementById('loan-months-display')
    const periodDisplay = document.getElementById('loan-period-display')
    function updatePeriodDisplay() {
      if (yearsDisplay) yearsDisplay.textContent = loanYears
      if (monthsDisplay) monthsDisplay.textContent = loanMonths
      if (periodDisplay) {
        const y = loanYears + ' ' + t(loanYears !== 1 ? 'years' : 'year')
        const m = loanMonths + ' ' + t(loanMonths !== 1 ? 'months' : 'month')
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
      if (!amt || amt <= 0) { showToast(t('Enter loan amount'), 'error'); return }
      const totalMonths = loanYears * 12 + loanMonths
      if (totalMonths < 1) { showToast(t('Select at least 1 month term'), 'error'); return }
      const period = `${loanYears} ${t(loanYears !== 1 ? 'years' : 'year')}, ${loanMonths} ${t(loanMonths !== 1 ? 'months' : 'month')}`
      if (!(await showConfirm(t('Request Loan'), `${formatCurrency(amt)} — ${period}?`))) return
      setLoading(requestLoanBtn, true)
      try {
        await api(`/members/${m.member_id}/apply_loan`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({amount: amt, term_months: totalMonths}),
        })
        showToast(t('Loan request submitted'), 'success')
        renderSubmitView()
      } finally {
        setLoading(requestLoanBtn, false)
      }
    }
  }
}

async function handleAddMember() {
  const btn = document.getElementById('add-member-btn')
  const name = document.getElementById('new-member-name').value.trim()
  const phone = document.getElementById('new-member-phone').value.trim()
  const depositRaw = document.getElementById('new-member-deposit').value.replace(/,/g, '')
  const depositAmount = Number(depositRaw) || 0
  const depositDate = document.getElementById('new-member-date').value
  const password = document.getElementById('new-member-password').value
  if (!name) { showToast(t('Enter a name'), 'error'); return }
  if (!(await showConfirm('Add Member', `Add new member "${name}"${phone ? ' ('+phone+')' : ''}?`))) return
  setLoading(btn, true)
  try {
    await api('/members', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, phone, entry_deposit_amount: depositAmount, entry_deposit_date: depositDate, password}),
    })
    await loadMembers()
    renderView()
  } finally {
    setLoading(btn, false)
  }
}

async function handleDirectEntry() {
  const btn = document.getElementById('de-submit-btn')
  const memberId = Number(document.getElementById('de-member').value)
  const shareRaw = document.getElementById('de-share').value.replace(/,/g, '')
  const fineRaw = document.getElementById('de-fine').value.replace(/,/g, '')
  const loanPrincipalRaw = document.getElementById('de-loan-principal').value.replace(/,/g, '')
  const loanInterestRaw = document.getElementById('de-loan-interest').value.replace(/,/g, '')
  const shareAmount = Number(shareRaw) || 0
  const loanPrincipal = Number(loanPrincipalRaw) || 0
  const loanInterest = Number(loanInterestRaw) || 0
  const fine = Number(fineRaw) || 0
  const entryDate = document.getElementById('de-date').value
  const note = document.getElementById('de-note').value
  if (!memberId) { showToast(t('Select a member'), 'error'); return }
  if (!shareAmount && !loanPrincipal && !loanInterest) { showToast(t('Enter at least share or loan amount'), 'error'); return }
  let msg = ''
  if (shareAmount > 0) msg += `Share: ${formatCurrency(shareAmount)} `
  if (fine > 0) msg += `${t('Fine')}: ${formatCurrency(fine)} `
  if (loanPrincipal > 0) msg += `${t('Loan Principal')}: ${formatCurrency(loanPrincipal)} `
  if (loanInterest > 0) msg += `${t('Loan Interest')}: ${formatCurrency(loanInterest)} `
  if (!(await showConfirm('Direct Entry', msg.trim()))) return
  setLoading(btn, true)
  try {
    const res = await fetch('/api/admin/direct_entry', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify({
        member_id: memberId,
        share_amount: shareAmount,
        fine: fine,
        loan_principal: loanPrincipal,
        loan_interest: loanInterest,
        entry_date: entryDate || undefined,
        note: note || '',
      }),
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({error: 'failed'}))
      showToast(e.error || 'Direct entry failed', 'error')
      return
    }
    showToast(t('Entry recorded successfully'), 'success')
    document.getElementById('de-share').value = '500'
    document.getElementById('de-fine').value = '0'
    document.getElementById('de-loan-principal').value = ''
    document.getElementById('de-loan-interest').value = ''
    document.getElementById('de-note').value = ''
    await renderView()
  } catch (err) {
    showToast((err && err.message) || 'Direct entry failed', 'error')
  } finally {
    setLoading(btn, false)
  }
}

function toggleAdminSection(btnId, bodyId) {
  const btn = document.getElementById(btnId)
  const body = document.getElementById(bodyId)
  if (!btn || !body) return
  const on = body.style.display === 'none'
  body.style.display = on ? 'block' : 'none'
  btn.classList.toggle('active', on)
}

function fdSchemeNo(id) { return 'FD' + String(id || 0).padStart(4, '0') }

async function renderFdEntries() {
  const keepingDiv = document.getElementById('fd-keeping')
  const recordDiv = document.getElementById('fd-record')
  if (!keepingDiv) return
  try {
    const entries = await api('/admin/fd/list', {headers: {'X-ADMIN-TOKEN': (state.adminToken || '')}})
    state.fdEntries = entries
    if (!entries || !entries.length) {
      keepingDiv.innerHTML = '<div class="fd-empty">' + t('No entries yet.') + '</div>'
      return
    }
    const oneTimeActive = entries.filter(e => e.status === 'active' && e.investment_type !== 'monthly' && e.investment_type !== 'installment')
    const schemes = entries.filter(e => e.status === 'active' && e.investment_type === 'monthly')
    const installments = entries.filter(e => e.investment_type === 'installment')
    const closedOneTime = entries.filter(e => e.status !== 'active' && e.investment_type !== 'monthly' && e.investment_type !== 'installment')
    const closedSchemes = entries.filter(e => e.status !== 'active' && e.investment_type === 'monthly')

    let activeHtml = ''
    if (oneTimeActive.length) {
      activeHtml += '<div class="fd-table-wrap" style="margin-bottom:12px">' + activeFdTable(oneTimeActive) + '</div>'
    }
    for (const scheme of schemes) {
      const schemeInsts = installments.filter(i => i.parent_id === scheme.id)
      const totalInvested = schemeInsts.reduce((s, i) => s + (i.amount || 0), 0)
      activeHtml += schemeCard(scheme, schemeInsts, totalInvested)
    }
    if (!activeHtml) activeHtml = '<div class="fd-empty">' + t('No active entries.') + '</div>'
    keepingDiv.innerHTML = activeHtml

    let closedHtml = ''
    if (closedOneTime.length) {
      closedHtml += '<div class="fd-table-wrap" style="margin-bottom:12px">' + closedFdTable(closedOneTime) + '</div>'
    }
    for (const scheme of closedSchemes) {
      const schemeInsts = installments.filter(i => i.parent_id === scheme.id)
      const totalInvested = schemeInsts.reduce((s, i) => s + (i.amount || 0), 0)
      closedHtml += closedSchemeCard(scheme, schemeInsts, totalInvested)
    }
    if (!closedHtml) closedHtml = '<div class="fd-empty muted">' + t('No closed entries.') + '</div>'
    recordDiv.innerHTML = closedHtml
  } catch (e) {
    keepingDiv.innerHTML = '<div class="fd-empty error">' + t('Error loading entries') + '</div>'
  }
}

function activeFdTable(fds) {
  return '<table class="fd-table"><thead><tr><th>' + t('FD No.') + '</th><th>' + t('Amount') + '</th><th>' + t('Start') + '</th><th>' + t('Maturity') + '</th><th>' + t('Rate') + '</th><th>' + t('Provider') + '</th><th></th></tr></thead><tbody>' +
    fds.map(fd => `<tr>
      <td class="td-bank"><strong>${fdSchemeNo(fd.fd_id)}</strong></td>
      <td class="td-amount">${formatCurrency(fd.amount)}</td>
      <td>${formatDate(fd.start_date)}</td>
      <td>${fd.maturity_date ? formatDate(fd.maturity_date) : '-'}</td>
      <td>${fd.interest_rate ? fd.interest_rate + '%' : '-'}</td>
      <td class="td-bank">${fd.notes || '-'}</td>
      <td><button class="fd-btn-withdraw" onclick="closeFd(${fd.fd_id})">${t('Close')}</button></td>
    </tr>`).join('') + '</tbody></table>'
}

function schemeCard(scheme, installments, totalInvested) {
  const instRows = installments.map((inst, i) => `
    <div style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(148,163,184,0.08);font-size:0.85rem">
      <span style="color:#94a3b8">${fdSchemeNo(scheme.fd_id)} · #${i + 1} ${inst.installment_date ? formatDate(inst.installment_date) : ''}</span>
      <span style="font-weight:500">${formatCurrency(inst.amount)}</span>
    </div>`).join('')
  return `<div style="background:rgba(199,210,254,0.04);border:1px solid rgba(199,210,254,0.12);border-radius:10px;padding:14px;margin-bottom:10px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <div>
        <strong style="font-size:0.75rem;color:#fbbf24">${fdSchemeNo(scheme.fd_id)}</strong>
        <span style="font-weight:600;font-size:0.9rem"> ${escHtml(scheme.notes || 'Unnamed')}</span>
        <span style="display:inline-block;margin-left:8px;font-size:0.7rem;background:rgba(251,191,36,0.15);color:#fbbf24;padding:2px 8px;border-radius:4px">${t('Monthly Scheme')}</span>
      </div>
      <button class="fd-btn-withdraw" onclick="closeFd(${scheme.fd_id})" style="background:rgba(239,68,68,0.15);color:#fca5a5;border:1px solid rgba(239,68,68,0.2)">${t('Close Scheme')}</button>
    </div>
    <div style="display:flex;gap:12px;font-size:0.8rem;color:#94a3b8;align-items:center;flex-wrap:wrap">
      <span>${formatDate(scheme.start_date)} → ${scheme.maturity_date ? formatDate(scheme.maturity_date) : '-'}</span>
      <span>${t('Total')}: <strong style="color:#e2e8f0">${formatCurrency(totalInvested)}</strong></span>
      <span>${installments.length} ${t('installments')}</span>
      <button class="fd-scheme-toggle" id="scheme-toggle-${scheme.fd_id}" onclick="toggleScheme(${scheme.fd_id})">${t('Show installments')} <span class="fd-chevron">▾</span></button>
    </div>
    <div id="scheme-body-${scheme.fd_id}" style="margin-top:8px;display:none">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <span style="font-size:0.8rem;color:#94a3b8">${t('Installments')}</span>
        <button class="fd-btn-withdraw" onclick="showInstallmentForm(${scheme.fd_id})" style="background:rgba(52,211,153,0.12);color:#34d399;border:1px solid rgba(52,211,153,0.2);padding:2px 10px;font-size:0.75rem">+ ${t('Add')}</button>
      </div>
      <div id="inst-form-${scheme.fd_id}"></div>
      ${instRows || '<div style="color:#64748b;font-size:0.8rem">' + t('No installments yet') + '</div>'}
    </div>
  </div>`
}

function toggleScheme(schemeId) {
  const body = document.getElementById('scheme-body-' + schemeId)
  const btn = document.getElementById('scheme-toggle-' + schemeId)
  const open = body.style.display !== 'none'
  body.style.display = open ? 'none' : 'block'
  btn.classList.toggle('open', !open)
  btn.innerHTML = (open ? t('Show installments') : t('Hide installments')) + ' <span class="fd-chevron">' + (open ? '▸' : '▾') + '</span>'
}

function closedSchemeCard(scheme, installments, totalInvested) {
  const instRows = installments.map((inst, i) => `
    <div style="display:flex;justify-content:space-between;padding:3px 0;font-size:0.8rem;color:#94a3b8">
      <span>${fdSchemeNo(scheme.fd_id)} · #${i + 1} ${inst.installment_date ? formatDate(inst.installment_date) : ''}</span>
      <span>${formatCurrency(inst.amount)}</span>
    </div>`).join('')
  return `<div style="background:rgba(148,163,184,0.03);border:1px solid rgba(148,163,184,0.1);border-radius:10px;padding:14px;margin-bottom:10px">
    <div style="display:flex;justify-content:space-between;margin-bottom:6px">
      <span><strong style="font-size:0.75rem;color:#94a3b8">${fdSchemeNo(scheme.fd_id)}</strong> <span style="font-weight:600;font-size:0.9rem">${escHtml(scheme.notes || 'Unnamed')}</span></span>
      <span style="font-size:0.7rem;background:rgba(148,163,184,0.15);color:#94a3b8;padding:2px 8px;border-radius:4px">${t('Closed Scheme')}</span>
    </div>
    <div style="display:flex;gap:12px;font-size:0.8rem;color:#94a3b8;align-items:center;flex-wrap:wrap">
      <span>${formatDate(scheme.start_date)} → ${scheme.maturity_date ? formatDate(scheme.maturity_date) : '-'}</span>
      <span>${t('Invested')}: ${formatCurrency(totalInvested)}</span>
      <span>${t('Return')}: ${scheme.interest_earned ? formatCurrency(scheme.interest_earned) : '-'}</span>
      <button class="fd-scheme-toggle" id="scheme-toggle-${scheme.fd_id}" onclick="toggleScheme(${scheme.fd_id})">${t('Show installments')} <span class="fd-chevron">▸</span></button>
    </div>
    <div id="scheme-body-${scheme.fd_id}" style="margin-top:6px;padding-top:6px;border-top:1px solid rgba(148,163,184,0.08);display:none">
      <div style="font-size:0.75rem;color:#64748b;margin-bottom:4px">${installments.length} ${t('installments')}</div>
      ${instRows}
    </div>
  </div>`
}

function closedFdTable(fds) {
  return '<table class="fd-table"><thead><tr><th>' + t('FD No.') + '</th><th>' + t('Amount') + '</th><th>' + t('Start') + '</th><th>' + t('Maturity') + '</th><th>' + t('Rate') + '</th><th>' + t('Return') + '</th><th>' + t('Provider') + '</th></tr></thead><tbody>' +
    fds.map(fd => `<tr>
      <td class="td-bank"><strong>${fdSchemeNo(fd.fd_id)}</strong></td>
      <td class="td-amount">${formatCurrency(fd.amount)}</td>
      <td>${formatDate(fd.start_date)}</td>
      <td>${fd.maturity_date ? formatDate(fd.maturity_date) : '-'}</td>
      <td>${fd.interest_rate ? fd.interest_rate + '%' : '-'}</td>
      <td class="td-interest">${fd.interest_earned ? formatCurrency(fd.interest_earned) : '-'}</td>
      <td class="td-bank">${fd.notes || '-'}</td>
    </tr>`).join('') + '</tbody></table>'
}

async function handleAddFd() {
  const btn = document.getElementById('fd-add-btn')
  const isMonthly = document.querySelector('input[name="inv-type"]:checked')?.value === 'monthly'
  const amount = Number(document.getElementById('fd-amount').value.replace(/,/g,''))
  const start_date = toISODate(document.getElementById('fd-start').value)
  const end_date = toISODate(document.getElementById('fd-end').value)
  const interest_rate = parseFloat(document.getElementById('fd-rate').value) || 0
  const notes = document.getElementById('fd-bank').value.trim()
  if (!start_date) { showToast(t('Enter valid start date'), 'error'); return }
  if (!end_date) { showToast(t('Enter valid maturity date'), 'error'); return }
  if (!isMonthly) {
    if (!amount || amount <= 0) { showToast(t('Enter valid amount'), 'error'); return }
  }
  const sd = new Date(start_date + 'T00:00:00')
  const ed = new Date(end_date + 'T00:00:00')
  if (ed < sd) { showToast(t('Maturity must not be before start date'), 'error'); return }
  const term_months = Math.max(0, (ed.getFullYear() - sd.getFullYear()) * 12 + (ed.getMonth() - sd.getMonth()))
  const confirmMsg = isMonthly
    ? `Create monthly scheme "${notes || 'Unnamed'}" from ${formatDate(start_date)} to ${formatDate(end_date)}?`
    : `Add ${formatCurrency(amount)} at ${interest_rate || 0}% for ${term_months} mo?`
  if (!(await showConfirm(isMonthly ? 'Create Scheme' : 'Add Investment', confirmMsg))) return
  setLoading(btn, true)
  try {
    await api('/admin/fd/add', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify({
        amount: isMonthly ? 0 : amount,
        start_date, term_months,
        interest_rate: isMonthly ? 0 : interest_rate,
        notes,
        investment_type: isMonthly ? 'monthly' : 'one_time',
      }),
    })
    showToast(isMonthly ? t('Scheme created') : t('Investment added'), 'success')
    await renderFdEntries()
    document.getElementById('fd-amount').value = ''
    document.getElementById('fd-bank').value = ''
  } catch (e) {
    showToast(fundErrMsg(e) || e.error || t('Add failed'), 'error')
  } finally {
    setLoading(btn, false)
  }
}

window.showInstallmentForm = function(schemeId) {
  const container = document.getElementById('inst-form-' + schemeId)
  if (!container) return
  if (container.dataset.open === '1') {
    container.innerHTML = ''
    delete container.dataset.open
    return
  }
  container.dataset.open = '1'
  container.innerHTML = `
    <div style="display:flex;gap:8px;align-items:end;margin-bottom:8px;padding:8px;background:rgba(255,255,255,0.03);border-radius:6px">
      <div style="flex:1">
        <label style="font-size:0.7rem;color:#94a3b8;display:block;margin-bottom:2px">${t('Amount')}</label>
        <div class="input-with-currency" style="margin:0"><span class="currency" style="padding:4px 6px">₹</span><input id="inst-amt-${schemeId}" type="text" inputmode="decimal" style="padding:6px 8px;font-size:0.85rem" /></div>
      </div>
      <div style="flex:1">
        <label style="font-size:0.7rem;color:#94a3b8;display:block;margin-bottom:2px">${t('Date')}</label>
        <div class="input-group" style="margin:0"><input id="inst-date-${schemeId}" type="text" class="dual-date" style="padding:6px 8px;font-size:0.85rem" value="${new Date().toLocaleDateString('en-IN', {day:'2-digit',month:'2-digit',year:'numeric'})}" /></div>
      </div>
      <button class="btn primary" onclick="handleAddInstallment(${schemeId})" style="padding:6px 14px;font-size:0.8rem;white-space:nowrap">${t('Save')}</button>
      <button class="btn secondary" onclick="showInstallmentForm(${schemeId})" style="padding:6px 10px;font-size:0.8rem">✕</button>
    </div>`
  const dateInput = document.getElementById('inst-date-' + schemeId)
  if (dateInput) dualDateInput(dateInput)
  const amtInput = document.getElementById('inst-amt-' + schemeId)
  if (amtInput) indianizeInput(amtInput)
}

window.handleAddInstallment = async function(schemeId) {
  const amtInput = document.getElementById('inst-amt-' + schemeId)
  const dateInput = document.getElementById('inst-date-' + schemeId)
  const amount = Number(amtInput?.value.replace(/,/g, '')) || 0
  const installment_date = dateInput ? toISODate(dateInput.value) : ''
  if (!amount || amount <= 0) { showToast(t('Enter valid amount'), 'error'); return }
  if (!installment_date) { showToast(t('Select a date'), 'error'); return }
  try {
    const res = await fetch('/api/admin/fd/installment', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
      body: JSON.stringify({parent_id: schemeId, amount, installment_date, notes: ''}),
    })
    if (!res.ok) {
      const e = await res.json().catch(() => ({error: 'failed'}))
      showToast(fundErrMsg(e) || e.error || t('Add failed'), 'error')
      return
    }
    showToast(t('Installment added'), 'success')
    await renderFdEntries()
  } catch (err) {
    showToast((err && err.message) || 'Failed', 'error')
  }
}

window.closeFd = async function(fdId) {
  const existing = document.getElementById('fd-close-overlay')
  if (existing) existing.remove()
  const fdRow = state.fdEntries ? state.fdEntries.find(e => e.fd_id === fdId) : null
  if (!fdRow) { showToast(t('Entry not found'), 'error'); return }
  const isScheme = fdRow.investment_type === 'monthly'
  const installments = isScheme ? state.fdEntries.filter(e => e.parent_id === fdId && e.status === 'active') : []
  const totalInvested = installments.reduce((s, i) => s + (i.amount || 0), 0)
  const amount = isScheme ? totalInvested : fdRow.amount
  const termMonths = fdRow.term_months
  const rate = fdRow.interest_rate
  const bank = fdRow.notes || '-'
  const expectedReturn = amount * (rate / 100) * (termMonths / 12) || Math.round(amount * 0.05)

  const overlay = document.createElement('div')
  overlay.id = 'fd-close-overlay'
  overlay.className = 'modal-overlay'
  overlay.innerHTML = `
    <div class="modal-box" style="max-width:420px">
      <p style="margin:0 0 12px;font-weight:600">${isScheme ? t('Close Scheme') : t('Close')}</p>
      <div style="background:rgba(255,255,255,0.03);border-radius:10px;padding:14px;margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span style="color:#94a3b8">${t('Provider')}</span><span>${bank || '-'}</span></div>
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span style="color:#94a3b8">${isScheme ? t('Total Invested') : t('Amount')}</span><span style="font-weight:600">${formatCurrency(amount)}</span></div>
        ${isScheme ? `<div style="display:flex;justify-content:space-between;padding:3px 0"><span style="color:#94a3b8">${t('Installments')}</span><span>${installments.length}</span></div>` : ''}
        <div style="display:flex;justify-content:space-between;padding:3px 0"><span style="color:#94a3b8">${t('Period')}</span><span>${formatDate(fdRow.start_date)} → ${fdRow.maturity_date ? formatDate(fdRow.maturity_date) : '-'}</span></div>
      </div>
      <div style="margin-bottom:14px">
        <label style="font-size:0.8rem;color:#94a3b8;display:block;margin-bottom:4px">${t('Return Amount')}</label>
        <div class="input-with-currency"><span class="currency">₹</span><input id="fd-return-amount" type="text" inputmode="decimal" value="${Math.round(expectedReturn)}" /></div>
      </div>
      <div class="reject-form-actions">
        <button class="btn primary" id="fd-close-confirm" style="background:rgba(239,68,68,0.2);color:#fca5a5;border:1px solid rgba(239,68,68,0.25)">${t('Confirm Close')}</button>
        <button class="btn secondary" id="fd-close-cancel">${t('Cancel')}</button>
      </div>
    </div>
  `
  document.body.appendChild(overlay)
  const returnInput = document.getElementById('fd-return-amount')
  if (returnInput) indianizeInput(returnInput)

  document.getElementById('fd-close-confirm').onclick = async () => {
    const btn = document.getElementById('fd-close-confirm')
    const interestEarned = Number(document.getElementById('fd-return-amount').value.replace(/,/g,''))
    if (isNaN(interestEarned) || interestEarned < 0) { showToast(t('Enter valid return amount'), 'error'); return }
    setLoading(btn, true)
    try {
      await api(`/admin/fd/close/${fdId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'X-ADMIN-TOKEN': (state.adminToken || '')},
        body: JSON.stringify({end_date: fdRow.maturity_date || istTodayStr(), interest_earned: interestEarned}),
      })
      overlay.remove()
      showToast(isScheme ? t('Scheme closed. Return added.') : t('Closed. Return added.'), 'success')
      renderView()
    } finally {
      setLoading(btn, false)
    }
  }
  document.getElementById('fd-close-cancel').onclick = () => overlay.remove()
}

async function handleUpdateDetails(memberId) {
  const btn = document.getElementById('self-save-btn')
  const phone = document.getElementById('self-phone').value.trim()
  const dob = document.getElementById('self-dob').value
  const address = document.getElementById('self-address').value.trim()
  const url = `/members/${memberId}/self`
  setLoading(btn, true)
  try {
    await api(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({phone, dob, address}),
    })
    renderMemberProfile(memberId)
  } catch (e) {
    showToast(e?.error || 'Save failed', 'error')
    console.error('Profile save error:', e)
  } finally {
    setLoading(btn, false)
  }
}

window.handleUpdateDetails = handleUpdateDetails
window.renderMemberProfile = renderMemberProfile
window.setView = setView

async function handleSubmitPayment(memberId) {
  const btn = document.getElementById('submit-payment-btn-top')
  const shareRaw = document.getElementById('share-amount-input').value.replace(/,/g, '')
  const loanPrincipalRaw = document.getElementById('loan-principal-input').value.replace(/,/g, '')
  const loanInterestRaw = document.getElementById('loan-interest-input').value.replace(/,/g, '')
  const shareAmount = Number(shareRaw) || 0
  const loanPrincipal = Number(loanPrincipalRaw) || 0
  const loanInterest = Number(loanInterestRaw) || 0
  const txnDate = document.getElementById('pay-txn-date').value
  const note = document.getElementById('pay-note').value
  const fineRaw = document.getElementById('fine-amount').value.replace(/,/g, '')
  const fine = Number(fineRaw) || 0
  if (!txnDate) { showToast(t('Select a payment date'), 'error'); return }
  if (new Date(txnDate) > new Date()) { showToast(t('Date cannot be in the future'), 'error'); return }
  if (!shareAmount || shareAmount <= 0) { showToast(t('Share is required'), 'error'); return }
  let msg = `${t('Share')}: ${formatCurrency(shareAmount)}`
  if (loanPrincipal > 0) msg += `<br>${t('Loan Principal')}: ${formatCurrency(loanPrincipal)}`
  if (loanInterest > 0) msg += `<br>${t('Loan Interest')}: ${formatCurrency(loanInterest)}`
  if (fine > 0) msg += `<br>${t('Fine')}: ${formatCurrency(fine)}`
  if (!(await showConfirm(t('Submit Payment'), msg))) return
  setLoading(btn, true)
  const screenshotInput = document.getElementById('screenshot-input')
  const screenshotFile = screenshotInput?.files?.[0]
  const total = shareAmount + loanPrincipal + loanInterest + fine
  try {
    const fd = new FormData()
    fd.append('amount', total)
    fd.append('share_amount', shareAmount)
    fd.append('loan_principal', loanPrincipal)
    fd.append('loan_interest', loanInterest)
    fd.append('fine', fine)
    fd.append('note', note)
    fd.append('txn_date', txnDate)
    if (screenshotFile) fd.append('screenshot', screenshotFile)
    const res = await fetch(`/api/members/${memberId}/submit_payment_request`, {method:'POST', body: fd})
    if (!res.ok) {
      const e = await res.json().catch(()=>({error:'failed'}))
      showToast(e.error || 'Submit failed', 'error')
      return
    }
    showToast(t('Submitted for approval'), 'success')
    renderSubmitView()
  } catch (err) {
    showToast((err && err.message) || 'Submit failed', 'error')
  } finally {
    setLoading(btn, false)
  }
}

document.addEventListener('DOMContentLoaded', () => {
  try {
    topbar = document.getElementById('topbar')
    mainScreen = document.getElementById('main-screen')
    menuLinks = document.getElementById('menu-links')
    content = document.getElementById('content')
    if (content) {
      // Every view swap re-themes any <select> the new view injected
      new MutationObserver(() => enhanceAllSelects(content))
        .observe(content, { childList: true, subtree: true })
    }
    enhanceAllSelects(document)
    memberSelect = document.getElementById('member-select')
    adminPin = document.getElementById('admin-pin')
    loginButton = document.getElementById('login-button')
    loginError = document.getElementById('login-error')
    if (loginButton) {
      try { loginButton.type='button' } catch(_){}
      loginButton.onclick = handleLogin
    }
    const pinToggle = document.getElementById('pin-toggle')
    if (pinToggle && adminPin) {
      pinToggle.onclick = () => {
        const t = adminPin
        t.type = t.type === 'password' ? 'text' : 'password'
        pinToggle.textContent = t.type === 'password' ? '👁' : '🙈'
      }
    }
    // Enter key handling for convenience
    if (adminPin) adminPin.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin() })
    if (memberSelect) memberSelect.addEventListener('keydown', (e) => { if (e.key === 'Enter') handleLogin() })
    translatePage()
    // Click outside avatar menu to close (delegated, added once)
    document.addEventListener('click', (e) => {
      const menu = document.getElementById('avatar-menu')
      if (menu && !menu.contains(e.target) && !e.target.closest('#profile-avatar')) {
        menu.classList.add('hidden')
      }
    })
    init()
  } catch (e) {
    try { fetch('/api/client_error', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({message: 'binding_error', stack: (e && e.stack)||String(e), ua: navigator.userAgent})}) } catch(_){}
  }
})



// PWA: register service worker (fullscreen "Add to Home Screen" support)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {})
  })
}

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
