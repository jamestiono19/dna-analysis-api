const form = document.getElementById("analysis-form");
const fileInput = document.getElementById("file");
const fileName = document.getElementById("file-name");
const fileDrop = fileInput.closest(".file-drop");
const frameStep = document.getElementById("frame-step");
const runButton = form.querySelector(".run");
const errorBox = document.getElementById("error");
const errorMessage = document.getElementById("error-message");
const result = document.getElementById("result");

const ROW_WIDTH = 60;

const ACTION_LABELS = {
  align: "Alignment result",
  translate: "Translation result",
  analyze: "Full analysis",
};

// How strongly each effect changes the protein, used only for colour.
const EFFECT_TONES = {
  synonymous: "neutral",
  missense: "caution",
  "in-frame insertion": "caution",
  "in-frame deletion": "caution",
  nonsense: "severe",
  frameshift: "severe",
  undetermined: "unknown",
};

const TYPE_LABELS = { SNV: "SNV", insertion: "Insertion", deletion: "Deletion" };

// Short notes shown in the boxed "How to read this" panel beside each result.
const VARIANT_NOTES = [
  "Position is the reference base number, counted from 1.",
  "An insertion sits after the base named. Position 0 means before base 1.",
  "Neighbouring inserted or deleted bases are reported as one event.",
];
const EFFECT_NOTE = "Effects compare codons in reference frame 1.";
const ALIGNMENT_NOTES = [
  "Both sequences are shown in full, 60 columns per row.",
  "The numbers at each end are the first and last base on that row.",
];
const PROTEIN_NOTES = [
  "Codons that contain N are shown as X.",
  "Translation stops before the first stop codon, which is not shown.",
];

// Build elements with textContent only, so nothing from the file is read as HTML.
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function formatNumber(value, digits = 0) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/* ---------- Form behaviour ---------- */

function selectedAction() {
  return form.elements.action.value;
}

function syncFrameStep() {
  frameStep.disabled = selectedAction() !== "translate";
}

form.addEventListener("change", (event) => {
  if (event.target.name === "action") syncFrameStep();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "Choose a FASTA file";
  fileDrop.classList.toggle("has-file", Boolean(file));
});

syncFrameStep();

/* ---------- Result building blocks ---------- */

function metricStrip(items) {
  const list = el("dl", null, "metrics");
  for (const [term, value, unit] of items) {
    const row = el("div");
    // Numbers use the data face; words such as "Reached" stay in the body face.
    const dd = el("dd", value, /\d/.test(value) ? null : "word");
    if (unit) dd.append(el("small", unit));
    row.append(el("dt", term), dd);
    list.append(row);
  }
  return list;
}

// A result section: title and a boxed "how to read this" note beside the data.
function section(title, notes, ...content) {
  const wrapper = el("section", null, "result-section");
  const side = el("div", null, "section-side");
  side.append(el("h3", title));
  if (notes.length) {
    const note = el("aside", null, "note-panel");
    note.append(el("p", "How to read this", "note-label"));
    const list = el("ul", null, "note-list");
    for (const text of notes) list.append(el("li", text));
    note.append(list);
    side.append(note);
  }
  const body = el("div", null, "section-body");
  body.append(...content);
  wrapper.append(side, body);
  return wrapper;
}

// Classify one alignment column for highlighting.
function columnClass(refBase, queryBase) {
  if (refBase === "-" || queryBase === "-") return "gap";
  if (refBase !== queryBase && "ACGT".includes(refBase) && "ACGT".includes(queryBase)) return "mismatch";
  return "";
}

// Append text to a line, grouping neighbouring characters with the same class.
function appendRuns(line, text, classes) {
  let start = 0;
  for (let i = 1; i <= text.length; i++) {
    if (i === text.length || classes[i] !== classes[start]) {
      const chunk = text.slice(start, i);
      const cls = classes[start];
      if (cls === "mismatch") line.append(el("mark", chunk));
      else if (cls === "gap") line.append(el("span", chunk, "gap"));
      else line.append(document.createTextNode(chunk));
      start = i;
    }
  }
}

function alignmentBlock(alignment) {
  const ref = alignment.reference_aligned;
  const query = alignment.query_aligned;
  const pre = el("pre", null, "alignment");
  pre.setAttribute("aria-label", "Alignment of query against reference");

  let refPos = 0;
  let queryPos = 0;
  for (let start = 0; start < ref.length; start += ROW_WIDTH) {
    const refChunk = ref.slice(start, start + ROW_WIDTH);
    const queryChunk = query.slice(start, start + ROW_WIDTH);
    const classes = [...refChunk].map((r, i) => columnClass(r, queryChunk[i]));

    let matchLine = "";
    for (let i = 0; i < refChunk.length; i++) {
      const r = refChunk[i];
      const q = queryChunk[i];
      if (r === "-" || q === "-") matchLine += " ";
      else if (r === q && "ACGT".includes(r)) matchLine += "|";
      else matchLine += ".";
    }

    const refStart = refPos + 1;
    const queryStart = queryPos + 1;
    refPos += refChunk.replaceAll("-", "").length;
    queryPos += queryChunk.replaceAll("-", "").length;

    const refLine = el("span");
    refLine.append(el("span", "REF   ", "lbl"), el("span", String(refStart).padStart(4) + "  ", "pos"));
    appendRuns(refLine, refChunk, classes);
    refLine.append(el("span", "  " + refPos, "pos"));

    const midLine = el("span", " ".repeat(12) + matchLine, "match-line");

    const queryLine = el("span");
    queryLine.append(el("span", "QUERY ", "lbl"), el("span", String(queryStart).padStart(4) + "  ", "pos"));
    appendRuns(queryLine, queryChunk, classes);
    queryLine.append(el("span", "  " + queryPos, "pos"));

    pre.append(refLine, "\n", midLine, "\n", queryLine, "\n\n");
  }
  return pre;
}

// Key for the alignment, drawn with the same marks the alignment uses.
function alignmentLegend() {
  const panel = el("div", null, "key-panel");
  panel.append(el("p", "Key", "note-label"));
  const list = el("ul", null, "key-list");

  const items = [
    [el("span", "|", "key-symbol"), "Same base in both sequences"],
    [el("span", ".", "key-symbol"), "Different base, or an unknown base (N)"],
    [el("mark", "A", "key-symbol"), "Highlighted: a base that differs from the reference"],
    [el("span", "-", "key-symbol gap"), "Gap: a base missing from one sequence"],
  ];
  for (const [symbol, meaning] of items) {
    const item = el("li");
    item.append(symbol, el("span", meaning));
    list.append(item);
  }
  panel.append(list);
  return panel;
}

function variantTable(variants) {
  if (variants.length === 0) {
    return el("p", "No variants. The sequence matches the reference at every defined base.", "empty");
  }
  const withEffects = "effect" in variants[0];

  const table = el("table", null, "variants");
  const head = el("tr");
  const headings = [["Position", "col-pos"], ["Type"], ["Change"]];
  if (withEffects) headings.push(["Effect"], ["Codon"], ["Amino acid"]);
  for (const [label, className] of headings) {
    const th = el("th", label, className);
    th.scope = "col";
    head.append(th);
  }
  const thead = el("thead");
  thead.append(head);

  const tbody = el("tbody");
  for (const variant of variants) {
    const row = el("tr");
    row.append(el("td", formatNumber(variant.position), "col-pos"));
    row.append(el("td", TYPE_LABELS[variant.type] || variant.type));

    const change = el("td", null, "change");
    change.append(variant.ref, el("span", "→", "arrow"), variant.alt);
    row.append(change);

    if (withEffects) {
      const effectCell = el("td");
      const tone = EFFECT_TONES[variant.effect] || "unknown";
      effectCell.append(el("span", variant.effect, `effect effect-${tone}`));
      row.append(effectCell);

      const codon = variant.ref_codon
        ? `${variant.ref_codon} → ${variant.alt_codon || "?"}`
        : "–";
      row.append(el("td", codon, "codon"));

      const aminoAcid = variant.ref_amino_acid
        ? `${variant.ref_amino_acid} → ${variant.alt_amino_acid || "?"}`
        : "–";
      row.append(el("td", aminoAcid, "codon"));
    }
    tbody.append(row);
  }
  table.append(thead, tbody);

  const scroll = el("div", null, "table-scroll");
  scroll.append(table);
  return scroll;
}

function proteinBlock(translation) {
  const meta = el("dl", null, "protein-meta");
  const pairs = [
    ["Frame", String(translation.frame)],
    ["Length", `${formatNumber(translation.length)} aa`],
    ["Stop codon", translation.has_stop_codon ? "reached" : "not reached"],
  ];
  for (const [term, value] of pairs) {
    const row = el("div");
    row.append(el("dt", term), el("dd", value));
    meta.append(row);
  }

  const emptyText = translation.has_stop_codon
    ? "Empty: the first codon in this frame is a stop codon."
    : "Empty: this frame leaves no complete codon to translate.";
  const sequence = translation.protein
    ? el("pre", translation.protein, "protein")
    : el("p", emptyText, "protein protein-empty");
  return [meta, sequence];
}

/* ---------- Rendering ---------- */

function resultHead(action, data, summary) {
  const head = el("header", null, "result-head");
  const title = el("h2");
  title.append(el("span", data.sequence_id, "result-id"));
  head.append(el("p", ACTION_LABELS[action], "eyebrow"), title, el("p", summary));
  return head;
}

function variantSummary(count) {
  if (count === 0) return "no variants";
  return count === 1 ? "1 variant" : `${count} variants`;
}

function render(action, data) {
  result.replaceChildren();

  if (action === "translate") {
    result.append(
      resultHead(action, data, `Translated in reading frame ${data.frame} with the standard genetic code.`),
      metricStrip([
        ["Reading frame", String(data.frame)],
        ["Protein length", formatNumber(data.length), "aa"],
        ["Stop codon", data.has_stop_codon ? "Reached" : "None"],
      ]),
      section("Protein", PROTEIN_NOTES, ...proteinBlock(data)),
    );
  } else {
    const { alignment, variants } = data;
    result.append(
      resultHead(
        action,
        data,
        `Aligned against ${data.reference_id} with global alignment: ${variantSummary(variants.length)}.`,
      ),
      metricStrip([
        ["Score", formatNumber(alignment.score, 1)],
        ["Identity", formatNumber(alignment.identity * 100, 1), "%"],
        ["Alignment length", formatNumber(alignment.reference_aligned.length), "columns"],
        ["Variants", formatNumber(variants.length)],
      ]),
      section(
        "Variants",
        action === "analyze" ? [...VARIANT_NOTES, EFFECT_NOTE] : VARIANT_NOTES,
        variantTable(variants),
      ),
      section("Alignment", ALIGNMENT_NOTES, alignmentBlock(alignment), alignmentLegend()),
    );
    if (action === "analyze") {
      result.append(
        section(
          "Protein, frame 1",
          ["Translated from base 1 of the uploaded sequence.", ...PROTEIN_NOTES],
          ...proteinBlock(data.translation),
        ),
      );
    }
  }

  result.hidden = false;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  result.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
}

function showError(message) {
  errorMessage.textContent = message;
  errorBox.hidden = false;
}

/* ---------- Submit ---------- */

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  result.hidden = true;

  const action = selectedAction();
  const body = new FormData();
  const file = fileInput.files[0];
  if (file) body.append("file", file); // without a file the API's own error is shown
  if (action === "translate") body.append("frame", form.elements.frame.value);

  runButton.disabled = true;
  runButton.textContent = "Running…";
  try {
    const response = await fetch(`/api/${action}`, { method: "POST", body });
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    if (!response.ok) {
      const message = data && data.error ? data.error.message : `The server answered with status ${response.status}.`;
      throw new Error(message);
    }
    render(action, data);
  } catch (error) {
    showError(error.message);
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run analysis";
  }
});
