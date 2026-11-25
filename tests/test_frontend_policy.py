from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (FRONTEND / "index.html", FRONTEND / "styles.css", FRONTEND / "app.js")
    )


def test_frontend_uses_local_runtime_assets_and_no_inline_handlers():
    text = sources()
    assert not re.search(r'(?:src|href)=["\']https?://', text, re.IGNORECASE)
    assert not re.search(r'url\(["\']?https?://', text, re.IGNORECASE)
    assert not re.search(r'\son[a-z]+\s*=', text, re.IGNORECASE)
    assert '/vendor/katex/katex.min.css' in text
    assert '/vendor/katex/katex.min.js' in text
    assert '/vendor/marked/marked.umd.js' in text
    assert '/vendor/dompurify/purify.min.js' in text


def test_frontend_has_one_app_state_and_all_six_views():
    text = sources()
    assert text.count('const AppState') == 1
    for view in ('sprint', 'radar', 'chat', 'vault', 'mock', 'checker'):
        assert f'data-view="{view}"' in text
    assert 'addEventListener' in text
    assert 'DOMPurify.sanitize' in text


def test_styles_obey_precision_shell_and_banned_style_policy():
    text = sources().lower()
    for banned in (
        'linear-gradient', 'radial-gradient', 'conic-gradient',
        'backdrop-filter', 'box-shadow', '#6366f1', '#8b5cf6',
        '#a855f7', '#06b6d4', '#0f172a', '#1e293b',
        'border-radius: 9999px',
    ):
        assert banned not in text
    for required in ('100dvh', '--bg-app: #0d0e11', 'height: 44px', 'height: 26px', ':focus-visible'):
        assert required in text
