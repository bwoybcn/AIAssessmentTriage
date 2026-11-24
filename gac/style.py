"""Styling Streamlit's theme settings can't express. See DESIGN.md."""

CSS = """
<style>
/* Body copy: serif, 20px, generous leading */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
  font-size: 20px;
  line-height: 1.6;
}
/* Headings: tight tracking */
h1, h2, h3, h4 { letter-spacing: -0.02em; }
/* Plumbing (labels, buttons, captions, help): sans-serif */
[data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] *,
button, button *,
[data-baseweb="select"] *, input, textarea,
[role="listbox"] *, [role="radiogroup"] label * {
  font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif !important;
}
[data-testid="stWidgetLabel"] p,
button p, [role="radiogroup"] label p { font-size: 16px; line-height: 1.4; }
</style>
"""
