const form = document.getElementById("analysis-form");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");

// Build elements with textContent only, so nothing from the file is read as HTML.
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function definitionList(pairs) {
  const list = el("dl");
  for (const [term, value] of pairs) list.append(el("dt", term), el("dd", String(value)));
  return list;
}

// '|' identical base, '.' mismatch or N, ' ' gap.
function matchLine(ref, query) {
  let line = "";
  for (let i = 0; i < ref.length; i++) {
    if (ref[i] === "-" || query[i] === "-") line += " ";
    else if (ref[i] === query[i] && "ACGT".includes(ref[i])) line += "|";
    else line += ".";
  }
  return line;
}

function alignmentBlock(alignment) {
  const ref = alignment.reference_aligned;
  const query = alignment.query_aligned;
  const match = matchLine(ref, query);
  const rows = [];
  for (let i = 0; i < ref.length; i += 60) {
    rows.push(`REF    ${ref.slice(i, i + 60)}`, `       ${match.slice(i, i + 60)}`, `QUERY  ${query.slice(i, i + 60)}`, "");
  }
  return el("pre", rows.join("\n"), "alignment");
}

function variantTable(variants) {
  if (variants.length === 0) return el("p", "No variants found.");
  const columns = ["position", "type", "ref", "alt"];
  if ("effect" in variants[0]) columns.push("effect");

  const table = el("table");
  const head = el("tr");
  for (const column of columns) head.append(el("th", column));
  const thead = el("thead");
  thead.append(head);

  const tbody = el("tbody");
  for (const variant of variants) {
    const row = el("tr");
    for (const column of columns) row.append(el("td", String(variant[column])));
    tbody.append(row);
  }
  table.append(thead, tbody);
  return table;
}

function proteinBlock(translation) {
  return [
    definitionList([
      ["Frame", translation.frame],
      ["Length", translation.length],
      ["Stop codon reached", translation.has_stop_codon ? "yes" : "no"],
    ]),
    el("pre", translation.protein || "(empty: no complete codon before a stop)", "protein"),
  ];
}

function render(action, data) {
  result.replaceChildren(el("h2", `Result for ${data.sequence_id}`));

  if (action === "translate") {
    result.append(...proteinBlock(data));
  } else {
    result.append(
      el("h3", "Alignment"),
      definitionList([
        ["Reference", data.reference_id],
        ["Score", data.alignment.score],
        ["Identity", data.alignment.identity.toFixed(4)],
      ]),
      alignmentBlock(data.alignment),
      el("h3", `Variants (${data.variants.length})`),
      variantTable(data.variants),
    );
    if (action === "analyze") {
      result.append(el("h3", "Protein (frame 1)"), ...proteinBlock(data.translation));
    }
  }
  result.hidden = false;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  result.hidden = true;

  const action = form.elements.action.value;
  const body = new FormData();
  const file = form.elements.file.files[0];
  if (file) body.append("file", file); // without a file the API's own error is shown
  if (action === "translate") body.append("frame", form.elements.frame.value);

  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const response = await fetch(`/api/${action}`, { method: "POST", body });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error ? data.error.message : `Request failed with status ${response.status}.`);
    }
    render(action, data);
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  } finally {
    button.disabled = false;
  }
});
