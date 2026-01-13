<!DOCTYPE html>
<html>
<head>
  <title>{{ company_name }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    td, th { font-size: 14px; vertical-align: middle; }
    .actions a { margin-right: 4px; white-space: nowrap; }
    input.small { width: 120px; }
    .sample-link { font-size: 13px; margin-left: 6px; }
  </style>
</head>
<body class="bg-light">

<div class="container-fluid mt-3">
<h4 class="text-center">{{ company_name }}</h4>

<!-- UPLOAD SECTION -->
<div class="row mb-3">
  <div class="col-md-6">
    <form method="post" action="/upload/balance" enctype="multipart/form-data">
      <label class="form-label">
        Upload Balance Excel
        <span class="sample-link">
          (
          <a href="/static/samples/tally_outstanding.xlsx" download>
            Download tally_outstanding
          </a>
          )
        </span>
      </label>
      <input type="file" name="file" class="form-control mb-1" required>
      <button class="btn btn-primary btn-sm">Upload Balance</button>
    </form>
  </div>

  <div class="col-md-6">
    <form method="post" action="/upload/contacts" enctype="multipart/form-data">
      <label class="form-label">
        Upload Contact Excel
        <span class="sample-link">
          (
          <a href="/static/samples/party_contacts.xlsx" download>
            Download party_contacts
          </a>
          )
        </span>
      </label>
      <input type="file" name="file" class="form-control mb-1" required>
      <button class="btn btn-secondary btn-sm">Upload Contacts</button>
    </form>
  </div>
</div>

{% for m in get_flashed_messages() %}
<div class="alert alert-warning">{{ m }}</div>
{% endfor %}

<!-- TABLE -->
<table class="table table-bordered bg-white table-sm">
<thead class="table-dark">
<tr>
<th>#</th>
<th>Party</th>
<th>Mobile</th>
<th>Balance</th>
<th>Actions</th>
</tr>
</thead>
<tbody>

{% for d in data %}
{% set msg =
"Dear " ~ d[2] ~
", As per our records, an outstanding balance of ₹" ~ d[5] ~
" is pending from your side. Kindly arrange the payment at the earliest. "
~ "Thank you – " ~ company_name
%}

<tr>
<td>{{ loop.index }}</td>
<td>{{ d[2] }}</td>

<td>
<input class="form-control form-control-sm small"
value="{{ d[3] or '' }}"
onchange="updateNumber('{{ d[0] }}', this.value)">
</td>

<td>₹ {{ d[5] }}</td>

<td class="actions">
{% if d[3] %}
<a class="btn btn-success btn-sm" target="_blank"
href="https://wa.me/91{{ d[3] }}?text={{ msg|urlencode }}">WhatsApp</a>

<a class="btn btn-primary btn-sm" href="tel:{{ d[3] }}">Call</a>

<a class="btn btn-warning btn-sm"
href="sms:{{ d[3] }}?body={{ msg|urlencode }}">SMS</a>
{% else %}
<span class="text-muted">No Number</span>
{% endif %}
</td>
</tr>
{% endfor %}
</tbody>
</table>

<div class="text-center">
<a href="/companies">Change Company</a> |
<a href="/logout">Logout</a>
</div>
</div>

<script>
function updateNumber(id, number) {
  fetch("/update-number", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({id:id, number:number})
  });
}
</script>

</body>
</html>
