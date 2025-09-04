"""
Tests for the Streamlit landing page.

Framework: pytest
- We mock 'streamlit' and 'utils.get_app_version' to capture UI calls without requiring Streamlit.
- We load the app module by path to validate its side effects (calls to st.*) at import time.
"""
# ruff: noqa: S101, TRY003

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from typing import Any, List, Tuple
import pytest

# The shell script tries to detect the app file and inject a path here at write time.
# If this path doesn't exist at runtime, we fall back to a dynamic search.
INJECTED_APP_PATH = Path(r"""app.py""")

def _discover_app_file() -> Path:
    """
    Find the Streamlit app file by looking for key markers used in the provided snippet.
    Preference order:
      1) Non-test locations
      2) Any python file including tests/
    """
    repo_root = Path(__file__).resolve().parent.parent
    markers = ("st.set_page_config(", "My Streamlit Template", "A minimal multi-page app template.")
    # Pass 1: outside tests/
    candidates: List[Path] = []
    for py in repo_root.rglob("*.py"):
        try:
            rel = py.relative_to(repo_root)
        except ValueError:
            rel = py
        if "node_modules" in rel.parts or ".venv" in rel.parts:
            continue
        if "tests" in rel.parts:
            continue
        try:
            txt = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(m in txt for m in markers):
            candidates.append(py)
    if candidates:
        # Prefer common filenames
        for name in ("app.py", "streamlit_app.py", "Home.py", "main.py"):
            for c in candidates:
                if c.name == name:
                    return c
        return candidates[0]

    # Pass 2: include tests/
    for py in repo_root.rglob("*.py"):
        try:
            rel = py.relative_to(repo_root)
        except ValueError:
            rel = py
        if "node_modules" in rel.parts or ".venv" in rel.parts:
            continue
        try:
            txt = py.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(m in txt for m in markers):
            return py

    raise FileNotFoundError("Could not locate Streamlit app module containing expected markers.")

def app_file() -> Path:
    if INJECTED_APP_PATH.exists():
        return INJECTED_APP_PATH
    return _discover_app_file()

class _SidebarCtx:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class StreamlitRecorder(types.ModuleType):
    """
    Minimal fake 'streamlit' module that records calls made by the app.
    """
    def __init__(self, name="streamlit"):
        super().__init__(name)
        self._calls: List[Tuple[str, Any]] = []
        self.sidebar = _SidebarCtx()
        # Bind methods on the module object
        for fn in ("set_page_config", "header", "caption", "divider", "write", "markdown", "title", "info"):
            setattr(self, fn, getattr(self, f"_{fn}"))

    # Methods append a simple tuple describing the call
    def _set_page_config(self, **kwargs):
        self._calls.append(("set_page_config", kwargs))
    def _header(self, *args, **kwargs):
        self._calls.append(("header", args, kwargs))
    def _caption(self, *args, **kwargs):
        self._calls.append(("caption", args, kwargs))
    def _divider(self, *args, **kwargs):
        self._calls.append(("divider", args, kwargs))
    def _write(self, *args, **kwargs):
        self._calls.append(("write", args, kwargs))
    def _markdown(self, *args, **kwargs):
        self._calls.append(("markdown", args, kwargs))
    def _title(self, *args, **kwargs):
        self._calls.append(("title", args, kwargs))
    def _info(self, *args, **kwargs):
        self._calls.append(("info", args, kwargs))

    # Helpers for assertions
    def calls(self) -> List[Tuple[str, Any]]:
        return list(self._calls)
    def calls_of(self, name: str) -> List[Tuple[str, Any]]:
        return [c for c in self._calls if c[0] == name]
    def first_call(self) -> Tuple[str, Any]:
        return self._calls[0] if self._calls else None

def load_app_with_fakes(version: str = "1.2.3", raise_on_version: bool = False):
    """
    Inject fake modules for 'streamlit' and 'utils', then import the app by file path.
    Returns: (module, streamlit_recorder)
    """
    fake_st = StreamlitRecorder()
    fake_utils = types.ModuleType("utils")

    if raise_on_version:
        def get_app_version():
            raise RuntimeError("boom")
    else:
        def get_app_version():
            return version
    fake_utils.get_app_version = get_app_version

    # Backup sys.modules and inject fakes
    modules_backup = sys.modules.copy()
    sys.modules["streamlit"] = fake_st
    sys.modules["utils"] = fake_utils

    try:
        path = app_file()
        spec = importlib.util.spec_from_file_location("app_under_test", str(path))
        mod = importlib.util.module_from_spec(spec)
        if spec is None or spec.loader is None:
            raise AssertionError("Failed to create module spec for app")
        spec.loader.exec_module(mod)  # Executes top-level Streamlit calls
        return mod, fake_st
    finally:
        # Clean up to avoid leaking fakes into other tests
        sys.modules.clear()
        sys.modules.update(modules_backup)

def _extract_single_arg_text(call_entry) -> str:
    # call_entry shape for non-config calls: (name, args, kwargs)
    _, args, kwargs = call_entry
    if args:
        return str(args[0])
    # fallback if only kwargs used
    for v in kwargs.values():
        return str(v)
    return ""

def test_page_config_is_set_correctly():
    _, st = load_app_with_fakes(version="9.9.9")
    # First call should be set_page_config with expected keys
    assert st.first_call()[0] == "set_page_config", "Expected first Streamlit call to configure page"
    cfg = st.first_call()[1]
    assert isinstance(cfg, dict)
    assert cfg.get("page_title") == "My Streamlit Template"
    assert cfg.get("page_icon") == "✨"
    assert cfg.get("layout") == "wide"
    menu = cfg.get("menu_items") or {}
    assert set(menu.keys()) == {"Get Help", "Report a bug", "About"}
    assert "https://docs.streamlit.io/" in menu["Get Help"]
    assert "https://github.com/streamlit/streamlit/issues" in menu["Report a bug"]
    assert menu["About"] == "A minimal multi-page app template."

def test_sidebar_shows_header_version_divider_text_and_quick_links():
    _, st = load_app_with_fakes(version="1.2.3")
    headers = [c for c in st.calls_of("header")]
    assert any("✨ App" in _extract_single_arg_text(c) for c in headers)

    captions = [c for c in st.calls_of("caption")]
    assert any("Version: 1.2.3" in _extract_single_arg_text(c) for c in captions)

    assert len(st.calls_of("divider")) >= 1

    writes = [c for c in st.calls_of("write")]
    assert any("Use the menu at the top-left to switch pages." in _extract_single_arg_text(c) for c in writes)

    markdowns = [c for c in st.calls_of("markdown")]
    md_texts = [_extract_single_arg_text(c) for c in markdowns]
    assert any("Quick links" in t for t in md_texts)
    assert any("🏠 Home" in t for t in md_texts)
    assert any("📊 Data" in t for t in md_texts)
    assert any("⚙️ Settings" in t for t in md_texts)

def test_main_content_title_body_and_info_tip_rendered():
    _, st = load_app_with_fakes()
    titles = [c for c in st.calls_of("title")]
    assert any("✨ My Streamlit Template" in _extract_single_arg_text(c) for c in titles)

    writes = [c for c in st.calls_of("write")]
    assert any("Use the **Pages** menu (top-left) to navigate." in _extract_single_arg_text(c) for c in writes)
    assert any("landing page is optional" in _extract_single_arg_text(c) for c in writes)

    infos = [c for c in st.calls_of("info")]
    assert any("Tip:" in _extract_single_arg_text(c) for c in infos)
    assert any("global announcements" in _extract_single_arg_text(c) for c in infos)

def test_import_bubbles_error_when_version_lookup_fails():
    with pytest.raises(RuntimeError, match="boom"):
        load_app_with_fakes(raise_on_version=True)

def test_set_page_config_called_before_any_rendering_calls():
    _, st = load_app_with_fakes()
    calls = st.calls()
    names = [c[0] for c in calls]
    assert names[0] == "set_page_config"
    # ensure at least one of the rendering calls appears after
    assert "title" in names[1:] or "header" in names[1:]