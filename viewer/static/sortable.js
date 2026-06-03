/* Generic client-side column sort for any <table data-sortable>.
 *
 * - Every <th> in such a table becomes sortable unless it carries
 *   `data-nosort` (e.g. a leading index / icon column).
 * - Click cycles: ascending → descending → (click another col resets).
 * - Sort key per cell: explicit `data-sort` attr if present, else text.
 * - Type-aware: ISO dates and numbers compare numerically; everything
 *   else uses locale string compare with numeric awareness ("P2" > "P1").
 * - Empty values ("", "—", "-") always sink to the bottom, both directions.
 * - Group/band header rows (a single cell with colspan, e.g. the Design
 *   page's status bands) are removed on first sort, since any global sort
 *   flattens the banding. Reload restores the default banded order.
 */
(function () {
  "use strict";

  var EMPTY = { "": 1, "—": 1, "-": 1, "–": 1 };

  function cellKey(row, idx) {
    var td = row.children[idx];
    if (!td) return "";
    if (td.dataset && td.dataset.sort !== undefined) return td.dataset.sort.trim();
    return (td.textContent || "").trim();
  }

  function isEmpty(v) { return EMPTY[v] === 1; }

  function compare(a, b) {
    var ea = isEmpty(a), eb = isEmpty(b);
    if (ea || eb) return ea === eb ? 0 : (ea ? 1 : -1); // empties last, both dirs
    var na = parseFloat(a.replace(/[^0-9.\-]/g, ""));
    var nb = parseFloat(b.replace(/[^0-9.\-]/g, ""));
    var pureNum = /^-?[\d.,%\s]+$/;
    if (pureNum.test(a) && pureNum.test(b) && !isNaN(na) && !isNaN(nb)) {
      return na - nb;
    }
    return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
  }

  function isGroupRow(row) {
    // A band/empty-state row: exactly one cell, spanning columns.
    if (row.children.length !== 1) return false;
    var c = row.children[0];
    return c.hasAttribute("colspan");
  }

  function sortTable(table, colIdx, dir) {
    var tbody = table.tBodies[0];
    if (!tbody) return;
    var all = Array.prototype.slice.call(tbody.rows);
    var dataRows = all.filter(function (r) { return !isGroupRow(r); });
    if (dataRows.length < 2) return;

    // Drop band/group header rows — they only make sense in default order.
    all.forEach(function (r) { if (isGroupRow(r)) r.parentNode.removeChild(r); });

    dataRows.sort(function (ra, rb) {
      return dir * compare(cellKey(ra, colIdx), cellKey(rb, colIdx));
    });
    dataRows.forEach(function (r) { tbody.appendChild(r); });
  }

  function initTable(table) {
    var thead = table.tHead;
    if (!thead || !thead.rows.length) return;
    var headRow = thead.rows[thead.rows.length - 1];
    var ths = Array.prototype.slice.call(headRow.cells);

    ths.forEach(function (th, idx) {
      if (th.hasAttribute("data-nosort")) return;
      th.classList.add("sortable");
      if (!th.querySelector(".sort-ind")) {
        var ind = document.createElement("span");
        ind.className = "sort-ind";
        ind.textContent = "↕";
        th.appendChild(ind);
      }
      th.addEventListener("click", function () {
        var asc = !th.classList.contains("sort-asc");
        ths.forEach(function (o) {
          o.classList.remove("sort-asc", "sort-desc");
          var i = o.querySelector(".sort-ind");
          if (i) i.textContent = "↕";
        });
        th.classList.add(asc ? "sort-asc" : "sort-desc");
        var ind = th.querySelector(".sort-ind");
        if (ind) ind.textContent = asc ? "▲" : "▼";
        sortTable(table, idx, asc ? 1 : -1);
      });
    });
  }

  function init() {
    document.querySelectorAll("table[data-sortable]").forEach(initTable);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
