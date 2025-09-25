// Dashboard-specific JS moved from dashboard.html

document.addEventListener('DOMContentLoaded', function() {
  var searchInput = document.getElementById('search-admissions');
  if (searchInput) {
    searchInput.addEventListener('input', function() {
      var filter = this.value.toLowerCase();
      var rows = document.querySelectorAll('#admissions-table-body tr');
      rows.forEach(function(row) {
        var text = row.textContent.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
      });
    });
  }
});
