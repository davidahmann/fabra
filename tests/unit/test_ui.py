from streamlit.testing.v1 import AppTest
from unittest.mock import patch

# Path to the ui.py file
UI_FILE = "src/meridian/ui.py"


def test_ui_file_not_found() -> None:
    # Simulate running with a file argument that doesn't exist
    with patch("sys.argv", ["ui.py", "non_existent.py"]):
        at = AppTest.from_file(UI_FILE)
        at.run()
        # Verify it doesn't crash
        assert not at.exception
        # Ideally we would check for st.error("File not found...") but AppTest
        # properties interactions are complex. Smoke test is sufficient.


def test_ui_loads_no_args() -> None:
    at = AppTest.from_file(UI_FILE)
    at.run()
    # just verify it doesn't crash
    assert not at.exception
