(() => {
  const menu = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.primary-nav');
  if (menu && nav) {
    const close = () => { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Open navigation'); };
    menu.addEventListener('click', () => {
      const open = !nav.classList.contains('is-open');
      nav.classList.toggle('is-open', open);
      menu.setAttribute('aria-expanded', String(open));
      menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click', close));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    window.addEventListener('resize', () => { if (window.innerWidth > 900) close(); });
  }
  document.querySelectorAll('[data-confirm]').forEach(btn => btn.addEventListener('click', event => {
    if (!window.confirm(btn.dataset.confirm)) event.preventDefault();
  }));
  const amount = document.getElementById('donation_amount');
  if (amount) amount.addEventListener('input', () => amount.setCustomValidity(''));
  const donationForm = document.querySelector('form[action$="submit-donation"]');
  if (donationForm) donationForm.addEventListener('submit', event => {
    const value = Number(amount.value);
    if (!Number.isFinite(value) || value < 1 || value > 1000000) {
      event.preventDefault(); amount.setCustomValidity('Please enter an amount between $1 and $1,000,000.'); amount.reportValidity();
    }
  });
  const volunteer = document.querySelector('form[action$="submit-volunteer"]');
  if (volunteer) volunteer.addEventListener('submit', event => {
    const phone = document.getElementById('v_phone');
    if (phone.value.replace(/\D/g, '').length < 10) {
      event.preventDefault(); phone.setCustomValidity('Enter a contact number with at least 10 digits.'); phone.reportValidity();
    }
  });
  const phone = document.getElementById('v_phone');
  if (phone) phone.addEventListener('input', () => phone.setCustomValidity(''));
})();
