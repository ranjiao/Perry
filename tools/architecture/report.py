"""Offline report assembly: source content is data, never HTML or JavaScript."""
import json
from pathlib import Path


def render(data):
    here = Path(__file__).parent
    payload = json.dumps(data, ensure_ascii=True).replace("<", "\\u003c")
    return (here.joinpath("report.html").read_text(encoding="utf-8")
            .replace("/* STYLES */", here.joinpath("report.css").read_text(encoding="utf-8"))
            .replace("/* APP */", here.joinpath("report.js").read_text(encoding="utf-8"))
            .replace("<!-- DATA -->", payload))
