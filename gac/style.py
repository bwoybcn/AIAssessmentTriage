"""Styling Streamlit's theme settings can't express. See DESIGN.md.

Colours here work in both light and dark mode: text inherits the theme
colour, borders use a translucent grey, and rating badges are solid with
white text (all at least 5.9:1).
"""

SANS = 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif'

CSS = f"""
<style>
:root {{
  --gac-brand: #15693b;
  --gac-red: #b3261e;
  --gac-amber: #8a5a00;
  --gac-green: #15693b;
  --gac-line: rgba(128, 128, 128, 0.35);
  --gac-soft: rgba(128, 128, 128, 0.08);
  --gac-sans: {SANS};
}}

/* ---- Streamlit chrome ---- */
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stDecoration"] {{ display: none; }}
.block-container {{ padding-top: 2.5rem; padding-bottom: 4rem; max-width: 760px; }}

/* ---- Typography (DESIGN.md) ---- */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{ font-size: 20px; line-height: 1.6; }}
h1, h2, h3, h4 {{ letter-spacing: -0.02em; }}
[data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
button, button *, [data-baseweb="select"] *, input, textarea,
[role="listbox"] *, [role="radiogroup"] label *, [role="tab"] *,
.gac-sans, .gac-sans * {{ font-family: var(--gac-sans) !important; }}
/* Streamlit's icons are a font: never override it */
[data-testid="stIconMaterial"], .material-symbols-rounded {{
  font-family: "Material Symbols Rounded" !important;
}}
[data-testid="stWidgetLabel"] p, button p,
[role="radiogroup"] label p, [role="tab"] p {{ font-size: 16px; line-height: 1.4; }}
[data-testid="stWidgetLabel"] p {{ font-weight: 600; }}

/* ---- Buttons ---- */
button p, button div {{ font-size: 16px !important; }}
button[kind^="primary"] p {{ font-weight: 600; }}

/* ---- Brand bar ---- */
.gac-brand {{
  display: flex; align-items: center; gap: 12px;
  padding-bottom: 18px; margin-bottom: 8px; border-bottom: 1px solid var(--gac-line);
}}
.gac-brand img {{ flex: none; display: block; }}
.gac-brand-name {{ font-family: var(--gac-sans); font-weight: 700; font-size: 18px; letter-spacing: -0.01em; }}
.gac-badge {{
  font-family: var(--gac-sans); font-size: 12px; font-weight: 600; letter-spacing: 0.04em;
  text-transform: uppercase; border: 1px solid var(--gac-line); border-radius: 9999px;
  padding: 2px 10px; margin-left: auto;
}}

/* ---- Hero ---- */
.gac-eyebrow {{
  font-family: var(--gac-sans); font-size: 13px; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; opacity: 0.75; margin: 28px 0 4px;
}}

/* ---- Stepper ---- */
.gac-steps {{
  list-style: none; display: flex; gap: 6px; padding: 0 !important; margin: 8px 0 28px !important;
  font-family: var(--gac-sans);
}}
.gac-steps li {{ flex: 1; min-width: 0; margin: 0 !important; padding: 0 !important; }}
.gac-steps .bar {{ display: block; height: 4px; border-radius: 9999px; background: var(--gac-line); }}
.gac-steps .done .bar, .gac-steps .current .bar {{ background: var(--gac-brand); }}
.gac-steps .name {{
  display: block; font-size: 13px; margin-top: 8px; opacity: 0.7;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.gac-steps .current .name {{ opacity: 1; font-weight: 700; }}
@media (max-width: 640px) {{ .gac-steps .name {{ display: none; }} }}
.gac-step-count {{ font-family: var(--gac-sans); font-size: 14px; opacity: 0.75; margin-bottom: 2px; }}

/* ---- Rating badges ---- */
.gac-pill {{
  display: inline-flex; align-items: center; gap: 6px; border-radius: 9999px;
  padding: 3px 12px; color: #fff; font-family: var(--gac-sans);
  font-size: 14px; font-weight: 700; line-height: 1.5; white-space: nowrap;
}}
.gac-pill.red {{ background: var(--gac-red); }}
.gac-pill.amber {{ background: var(--gac-amber); }}
.gac-pill.green {{ background: var(--gac-green); }}
.gac-pill.lg {{ font-size: 16px; padding: 5px 16px; }}

/* ---- Results summary ---- */
.gac-overall {{
  border: 1px solid var(--gac-line); border-radius: 4px; padding: 24px;
  margin: 8px 0 16px; background: var(--gac-soft);
}}
.gac-overall h2 {{ margin: 12px 0 6px; padding: 0; font-size: 30px; line-height: 1.25; }}
.gac-overall p {{ margin: 0; font-size: 18px; line-height: 1.6; }}
.gac-meta {{ font-family: var(--gac-sans); font-size: 14px; opacity: 0.8; margin-top: 14px; }}
.gac-grid {{
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 24px;
}}
.gac-grid > [role="listitem"] {{ display: flex; }}
.gac-grid .gac-card {{ flex: 1; }}
@media (max-width: 640px) {{ .gac-grid {{ grid-template-columns: 1fr; }} }}
.gac-card {{
  border: 1px solid var(--gac-line); border-left-width: 5px; border-radius: 4px; padding: 14px 16px;
}}
.gac-card.red {{ border-left-color: var(--gac-red); }}
.gac-card.amber {{ border-left-color: var(--gac-amber); }}
.gac-card.green {{ border-left-color: var(--gac-green); }}
.gac-card .label {{
  font-family: var(--gac-sans); font-size: 13px; font-weight: 600; letter-spacing: 0.06em;
  text-transform: uppercase; opacity: 0.8; margin-bottom: 8px;
}}
.gac-card .desc {{ font-family: var(--gac-sans); font-size: 14px; opacity: 0.8; margin-top: 8px; line-height: 1.45; }}

/* ---- Findings & recommendations ---- */
.gac-item {{ border-top: 1px solid var(--gac-line); padding: 18px 0 6px; }}
.gac-item:first-child {{ border-top: none; padding-top: 6px; }}
.gac-item h4 {{ margin: 10px 0 6px; padding: 0; font-size: 20px; }}
.gac-item p {{ margin: 0 0 8px; font-size: 18px; line-height: 1.6; }}
.gac-ref {{ font-family: var(--gac-sans); font-size: 14px; opacity: 0.8; line-height: 1.5; }}
.gac-tag {{
  font-family: var(--gac-sans); font-size: 12px; font-weight: 600; border: 1px solid var(--gac-line);
  border-radius: 9999px; padding: 1px 9px; margin-left: 6px; vertical-align: middle;
}}

/* ---- Review table ---- */
.gac-review {{ width: 100%; border-collapse: collapse; font-family: var(--gac-sans); font-size: 15px; }}
.gac-review th, .gac-review td {{
  text-align: left; vertical-align: top; padding: 9px 0; border-bottom: 1px solid var(--gac-line);
}}
.gac-review th {{ width: 42%; font-weight: 600; padding-right: 16px; }}

/* ---- Footer ---- */
.gac-footer {{
  font-family: var(--gac-sans); font-size: 13px; opacity: 0.75; line-height: 1.6;
  border-top: 1px solid var(--gac-line); margin-top: 48px; padding-top: 16px;
}}

/* ---- Sign-in ---- */
.gac-signin {{ text-align: center; margin: 56px 0 24px; }}
.gac-signin h1 {{ font-size: 40px; margin: 18px 0 8px; padding: 0; }}
.gac-signin p {{ font-size: 18px; opacity: 0.85; margin: 0; }}

/* Selected tab: keep label in the text colour (brand green on black is 3.1:1); the underline stays green */
[role="tab"][aria-selected="true"] p {{ color: inherit !important; font-weight: 700; }}

/* ---- Small screens ---- */
@media (max-width: 640px) {{
  h1 {{ font-size: 2rem !important; line-height: 1.2 !important; }}
  .gac-brand-name {{ font-size: 16px; }}
  .gac-badge {{ font-size: 11px; padding: 1px 8px; }}
  .gac-overall {{ padding: 18px; }}
  .gac-overall h2 {{ font-size: 24px; }}
  [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ font-size: 18px; }}
}}

/* Visible keyboard focus everywhere */
:focus-visible {{ outline: 3px solid var(--gac-brand) !important; outline-offset: 2px; }}
</style>
"""

def logo(size: int = 28) -> str:
    """Logo <img>, served from static/ (server.enableStaticServing).

    Decorative (empty alt), because the app name always sits next to it.
    """
    return f'<img src="app/static/logo.png" width="{size}" height="{size}" alt="">'
