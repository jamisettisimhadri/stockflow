/**
 * StockFlow — App JavaScript
 * Handles sidebar toggle, auto-dismiss alerts, and UX enhancements.
 */

(function () {
  'use strict';

  // ---- Sidebar Mobile Toggle ------------------------------------------------
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    sidebar && sidebar.classList.add('open');
    sidebarOverlay && sidebarOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar && sidebar.classList.remove('open');
    sidebarOverlay && sidebarOverlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', openSidebar);
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
  }

  // ---- Auto-dismiss Flash Messages -----------------------------------------
  setTimeout(function () {
    document.querySelectorAll('.alert.fade.show').forEach(function (el) {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert && bsAlert.close();
    });
  }, 5000);

  // ---- Confirm Delete button state -----------------------------------------
  var confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
  if (confirmDeleteBtn) {
    confirmDeleteBtn.closest('form') && confirmDeleteBtn.closest('form').addEventListener('submit', function () {
      confirmDeleteBtn.disabled = true;
      confirmDeleteBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Deleting…';
    });
  }

})();
