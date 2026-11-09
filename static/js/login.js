// Login page: show/hide password, submit state, and the animated code editor.
document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".reveal-pw").forEach(function (button) {
    var input = document.getElementById(button.dataset.target);
    button.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      button.setAttribute("aria-pressed", String(show));
      button.setAttribute("aria-label", show ? "Hide password" : "Show password");
      input.focus();
    });
  });

  // Show a loading state on submit so a double click doesn't send the form twice.
  var form = document.querySelector(".card form");
  if (form) {
    form.addEventListener("submit", function () {
      var submit = form.querySelector(".submit");
      submit.classList.add("loading");
      submit.disabled = true;
    });
  }

  var editor = document.querySelector(".editor");
  if (editor) startEditor(editor);
});

// Real excerpts from this project, typed into the editor one after another.
var SNIPPETS = [
  {
    file: "views.py", dir: "findings",
    code: [
      "@login_required",
      "def dashboard(request):",
      "    # Bad ?project= values are ignored, never trusted.",
      "    form, project = _filtered_project(request)",
      "    board = Dashboard(project=project)",
      "    context = {",
      "        \"filter_form\": form,",
      "        \"totals\": board.totals(),",
      "        \"chart_pillar\": board.chart_by_pillar(),",
      "        \"chart_severity\": board.chart_by_severity(),",
      "        \"chart_trend\": board.chart_status_trend(),",
      "    }",
      "    return render(",
      "        request, \"findings/dashboard.html\", context",
      "    )",
    ].join("\n"),
  },
  {
    file: "models.py", dir: "findings",
    code: [
      "class Finding(models.Model):",
      "    \"\"\"A single security risk found in the SDLC.\"\"\"",
      "",
      "    def update_status(self, new_status):",
      "        if new_status not in self.Status.values:",
      "            raise ValueError(f\"Unknown: {new_status}\")",
      "        self.status = new_status",
      "        if new_status == self.Status.RESOLVED:",
      "            self.resolved_at = timezone.now()",
      "        else:",
      "            self.resolved_at = None",
      "        self.save(update_fields=[\"status\", \"resolved_at\"])",
    ].join("\n"),
  },
  {
    file: "dashboard.py", dir: "findings",
    code: [
      "import matplotlib",
      "",
      "matplotlib.use(\"Agg\")  # server-side, no display needed",
      "from matplotlib.figure import Figure",
      "",
      "def _to_base64(fig):",
      "    buffer = io.BytesIO()",
      "    fig.savefig(buffer, format=\"png\", dpi=120)",
      "    return base64.b64encode(buffer.getvalue())",
      "",
      "SEVERITY_COLOURS = {",
      "    \"LOW\": \"#3E7C59\", \"MEDIUM\": \"#C9932B\",",
      "    \"HIGH\": \"#D2642A\", \"CRITICAL\": \"#A8322D\",",
      "}",
    ].join("\n"),
  },
];

var KEYWORDS = /^(def|class|return|if|elif|else|not|in|and|or|import|from|as|raise|for|while|with|try|except|pass|lambda|is)$/;
var BUILTINS = /^(self|None|True|False|int|str|len|ValueError|print)$/;

// Split Python source into [className, text] tokens for highlighting.
function tokenize(src) {
  var re = /(#[^\n]*)|("""[\s\S]*?"""|f?"[^"\n]*"|'[^'\n]*')|(@\w+)|(\b\d+\b)|([A-Za-z_]\w*)|([=+\-*/<>!:,.(){}\[\]]+)|(\s+|.)/g;
  var tokens = [], m, prevWord = "";
  while ((m = re.exec(src))) {
    var t = m[0], cls = "";
    if (m[1]) cls = "c";
    else if (m[2]) cls = "s";
    else if (m[3]) cls = "d";
    else if (m[4]) cls = "n";
    else if (m[5]) {
      if (KEYWORDS.test(t)) cls = "k";
      else if (BUILTINS.test(t)) cls = "b";
      else if (prevWord === "class" || /^[A-Z][a-z]\w*$/.test(t)) cls = "cl";
      else if (prevWord === "def" || src.charAt(re.lastIndex) === "(") cls = "f";
      prevWord = t;
    } else if (m[6]) cls = "o";
    tokens.push([cls, t]);
  }
  return tokens;
}

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// Render the first `count` characters of the token list as highlighted HTML.
function renderUpTo(tokens, count) {
  var html = "", left = count;
  for (var i = 0; i < tokens.length && left > 0; i++) {
    var text = tokens[i][1].slice(0, left);
    left -= text.length;
    var safe = escapeHtml(text);
    html += tokens[i][0] ? '<span class="tk-' + tokens[i][0] + '">' + safe + "</span>" : safe;
  }
  return html;
}

function startEditor(editor) {
  var code = editor.querySelector(".ed-code code");
  var body = editor.querySelector(".ed-body");
  var gutter = editor.querySelector(".ed-gutter");
  var tabs = editor.querySelectorAll(".ed-tab");
  var fileLabel = editor.querySelector(".ed-file");
  var run = editor.querySelector(".st-run");
  var runText = editor.querySelector(".st-text");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var index = 0;

  function setGutter(lines, current) {
    var html = "";
    for (var i = 0; i < lines; i++) html += i === current ? '<li class="cur"></li>' : "<li></li>";
    gutter.innerHTML = html;
  }

  function setStatus(state, text) {
    run.className = "st-run" + (state ? " " + state : "");
    runText.textContent = text;
  }

  function show(snippet, tokens, chars, typing) {
    var shown = snippet.code.slice(0, chars);
    var lineCount = shown.split("\n").length;
    code.innerHTML = renderUpTo(tokens, chars) + '<span class="caret"></span>';
    editor.classList.toggle("typing", typing);
    setGutter(Math.max(lineCount, 1), lineCount - 1);
    body.scrollTop = body.scrollHeight;  // keep the caret in view on small screens
  }

  function play() {
    var snippet = SNIPPETS[index];
    var tokens = tokenize(snippet.code);
    tabs.forEach(function (tab, i) { tab.classList.toggle("active", i === index); });
    fileLabel.textContent = snippet.file;
    setStatus("", "python manage.py runserver");

    if (reduceMotion) {
      show(snippet, tokens, snippet.code.length, false);
      setStatus("passed", "Ran 15 tests · OK");
      return;
    }

    var chars = 0;
    (function typeNext() {
      if (chars >= snippet.code.length) {
        show(snippet, tokens, chars, false);
        setStatus("running", "python manage.py test …");
        setTimeout(function () {
          setStatus("passed", "Ran 15 tests · OK");
          setTimeout(function () {
            index = (index + 1) % SNIPPETS.length;
            play();
          }, 2600);
        }, 1400);
        return;
      }
      // Type whole runs of indentation at once, pause a little longer at line ends.
      var next = snippet.code.charAt(chars);
      chars += 1;
      if (next === "\n") {
        while (snippet.code.charAt(chars) === " ") chars += 1;
      }
      show(snippet, tokens, chars, true);
      var delay = next === "\n" ? 140 : 18 + Math.random() * 40;
      setTimeout(typeNext, delay);
    })();
  }

  play();
}
