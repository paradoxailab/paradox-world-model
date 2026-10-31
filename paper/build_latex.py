"""Convert the paper (markdown export of the Claude Doc) into an arXiv-ready LaTeX project.

  python build_latex.py paper.md   ->  arxiv/main.tex (+ refs.bib, fig_architecture.tex), compiled main.pdf
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "arxiv")
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "paper.md")

TITLE = ("PWM-Dyn and ParadoxBench: A Provenance-Audited Physical Dynamics Model, "
         "Benchmarked Against Zero-Shot Foundation Models on US Traffic and Indian Rainfall")
AUTHOR = r"Aditya Kumar \qquad Anupam Singh\\[3pt] \small Paradox AI Lab, India\\ \small \href{https://paradoxailab.com}{\texttt{paradoxailab.com}}"

md = open(SRC).read()
md = md.replace("\r", "")

# ---- split off pieces that become LaTeX structure ---------------------------------------
def section(text, head):
    """Return (before, body, after) for the section starting with exactly `head`."""
    i = text.index(head)
    j = text.find("\n## ", i + len(head))
    j = len(text) if j < 0 else j + 1
    return text[:i], text[i + len(head):j], text[j:]

pre, abstract, rest = section(md, "## Abstract\n")
abstract = abstract.strip().replace("**", "")
md = rest
pre_refs, _refs, post_refs = section(md, "## References\n")
md = pre_refs + "```{=latex}\n\\nocite{*}\n\\bibliography{refs}\n```\n\n" + post_refs
md = md[:md.index("## Appendix B")] if "## Appendix B" in md else md
md = re.sub(r"\n\*Draft status[^\n]*\n", "\n", md)
md = re.sub(r"\n- Venue note:[^\n]*", "", md)

# ---- headings: drop hand numbering, shift levels -----------------------------------------
def head(m):
    hashes, text = m.group(1), m.group(2)
    text = re.sub(r"^\d+(\.\d+)*\.?\s+", "", text)
    level = len(hashes) - 1
    if text.startswith("Acknowledgements"):
        return "#" * level + " " + text + " {-}"
    if text.startswith("Appendix"):
        text = re.sub(r"^Appendix:?\s*", "", text)
        return "```{=latex}\n\\appendix\n```\n\n" + "#" * level + " " + text[0].upper() + text[1:]
    return "#" * level + " " + text
md = re.sub(r"^(#{2,4}) (.+)$", head, md, flags=re.M)

# ---- figure -----------------------------------------------------------------------------
fig = ("```{=latex}\n\\begin{figure*}[t]\n\\centering\n\\resizebox{\\textwidth}{!}{\\input{fig_architecture}}\n"
       "\\caption{PWM-Dyn forward pass. History, time, the fixed physical graph and (v0.4) the training-split "
       "climatology are encoded per location, mixed over the physical and learned graphs by three GraphMix blocks, "
       "and read out as three quantiles per horizon and location.}\n\\label{fig:arch}\n\\end{figure*}\n```")
md = re.sub(r"^&#91;embedded content:[^\n]*$", lambda m: fig, md, flags=re.M)

# ---- maths -------------------------------------------------------------------------------
md = re.sub(r"```latex\n(.*?)\n```", lambda m: "$$" + m.group(1).strip() + "$$", md, flags=re.S)
def setin(m):
    lhs, space, sup = m.group(1), m.group(2), m.group(3)
    space = {"ℝ": r"\mathbb{R}", "R": r"\mathbb{R}", "{0,1}": r"\{0,1\}"}[space]
    return f"${lhs} \\in {space}^{{{sup.replace('×', r' \times ')}}}$"
md = re.sub(r"(\b[A-Za-z](?:, [A-Za-z])?) ∈ (ℝ|R|\{0,1\})\^\{([^}]*)\}", setin, md)
md = md.replace(r"A\_{ij} = exp(−(d\_{ij}/σ)²)", r"$A_{ij} = \exp(-(d_{ij}/\sigma)^2)$")
md = md.replace(r"exp(−(km\_{ij}/30)²)", r"$\exp(-(\mathrm{km}_{ij}/30)^2)$")
md = re.sub(r"\b([A-Za-z]+)\\_\{([A-Za-z0-9]+)\}", r"$\1_{\2}$", md)
md = md.replace(r"\[q10, q90\]", r"$[q_{10}, q_{90}]$").replace("[q10, q90]", r"$[q_{10}, q_{90}]$")

os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "body.md"), "w").write(md)
open(os.path.join(OUT, "abstract.md"), "w").write(abstract)

header = r"""
\usepackage{amssymb}
\usepackage{newunicodechar}
\newunicodechar{→}{\ensuremath{\rightarrow}}
\newunicodechar{−}{\ensuremath{-}}
\newunicodechar{≤}{\ensuremath{\le}}
\newunicodechar{≥}{\ensuremath{\ge}}
\newunicodechar{∈}{\ensuremath{\in}}
\newunicodechar{≈}{\ensuremath{\approx}}
\newunicodechar{ℝ}{\ensuremath{\mathbb{R}}}
\newunicodechar{δ}{\ensuremath{\delta}}
\newunicodechar{σ}{\ensuremath{\sigma}}
\newunicodechar{ᵀ}{\ensuremath{^{\top}}}
\newunicodechar{⋅}{\ensuremath{\cdot}}
\usepackage{tikz}
\usetikzlibrary{positioning,arrows.meta,calc}
\usepackage{etoolbox}
\AtBeginEnvironment{longtable}{\footnotesize}
\renewcommand{\arraystretch}{1.15}
\setlength{\LTpre}{6pt}\setlength{\LTpost}{6pt}
\usepackage{microtype}
"""
open(os.path.join(OUT, "header.tex"), "w").write(header)
abs_tex = subprocess.run(["pandoc", "-f", "markdown", "-t", "latex"], input=abstract, text=True,
                         capture_output=True, check=True).stdout
args = ["pandoc", os.path.join(OUT, "body.md"), "-f", "markdown-implicit_figures-auto_identifiers+raw_attribute",
        "-t", "latex", "-s", "--number-sections", "-o", os.path.join(OUT, "main.tex"),
        "-V", "documentclass=article", "-V", "fontfamily=mathptmx", "-V", "fontsize=10pt", "-V", "geometry:margin=0.9in",
        "-V", "colorlinks=true", "-V", "linkcolor=blue!50!black", "-V", "urlcolor=blue!50!black",
        "-V", "citecolor=blue!50!black", "--natbib",
        "-M", f"title={TITLE}", "-M", "date=October 2026",
        "-H", os.path.join(OUT, "header.tex")]
subprocess.run(args, check=True)
tex = open(os.path.join(OUT, "main.tex")).read()
tex = tex.replace(r"\begin{document}", r"\begin{document}", 1)
tex = re.sub(r"\\author\{[^}]*\}", "", tex)
tex = tex.replace(r"\date{October 2026}", r"\author{" + AUTHOR + "}\n\\date{October 2026}")
tex = tex.replace(r"\maketitle", "\\maketitle\n\\begin{abstract}\n" + abs_tex + "\\end{abstract}\n", 1)
open(os.path.join(OUT, "main.tex"), "w").write(tex)
for f in ("refs.bib", "fig_architecture.tex"):
    shutil.copy(os.path.join(HERE, f), os.path.join(OUT, f))
for f in ("body.md", "abstract.md", "header.tex"):
    os.remove(os.path.join(OUT, f))
r = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                   cwd=OUT, capture_output=True, text=True)
print(r.stdout[-1500:] if r.returncode else "compiled OK")
log = open(os.path.join(OUT, "main.log"), errors="ignore").read()
print("overfull boxes:", log.count("Overfull"), "| undefined refs:", log.count("undefined"))
