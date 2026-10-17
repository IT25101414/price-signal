#!/usr/bin/env python3
"""Dependency-free accessibility regression check for the six static pages."""
from html.parser import HTMLParser
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
PAGES = ("welcome.html", "index.html", "explore.html", "report.html", "method.html", "help.html")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Node:
    def __init__(self, tag="root", attrs=None, parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs or []), parent
        self.children, self.data = [], []

    def text(self):
        return " ".join(" ".join(self.data).split()) + (" " if self.data else "") + " ".join(c.text() for c in self.children)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.stack.pop()

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if data.strip():
            self.stack[-1].data.append(data.strip())


def nodes(root):
    out = []
    todo = [root]
    while todo:
        node = todo.pop()
        out.append(node)
        todo.extend(reversed(node.children))
    return out


def labelled(node, ids, labels):
    if node.attrs.get("aria-label", "").strip():
        return True
    refs = node.attrs.get("aria-labelledby", "").split()
    if refs and all(ref in ids and ids[ref].text().strip() for ref in refs):
        return True
    if node.attrs.get("id") in labels:
        return True
    ancestor = node.parent
    while ancestor:
        if ancestor.tag == "label" and ancestor.text().strip():
            return True
        ancestor = ancestor.parent
    return bool(node.text().strip()) if node.tag == "button" else False


def parse_hex(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(value):
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in parse_hex(value)]
    return .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2]


def contrast(a, b):
    x, y = luminance(a), luminance(b)
    return (max(x, y) + .05) / (min(x, y) + .05)


def page_failures(path):
    parser = Tree()
    parser.feed(path.read_text(encoding="utf-8"))
    all_nodes = nodes(parser.root)
    ids = {n.attrs["id"]: n for n in all_nodes if n.attrs.get("id")}
    id_list = [n.attrs["id"] for n in all_nodes if n.attrs.get("id")]
    labels = {n.attrs.get("for") for n in all_nodes if n.tag == "label" and n.attrs.get("for")}
    failures = []
    html = next((n for n in all_nodes if n.tag == "html"), None)
    if not html or html.attrs.get("lang") != "en":
        failures.append("html lang must be en")
    if sum(n.tag == "main" for n in all_nodes) != 1:
        failures.append("page must have exactly one main landmark")
    if sum(n.tag == "h1" for n in all_nodes) != 1:
        failures.append("page must have exactly one h1")
    if len(id_list) != len(set(id_list)):
        failures.append("duplicate id")
    skips = [n for n in all_nodes if n.tag == "a" and "skip" in n.attrs.get("class", "").split()]
    if not skips or not skips[0].attrs.get("href", "").startswith("#") or skips[0].attrs["href"][1:] not in ids:
        failures.append("skip link must target an existing id")
    for node in all_nodes:
        for attr in ("aria-labelledby", "aria-describedby", "aria-controls"):
            for ref in node.attrs.get(attr, "").split():
                if ref not in ids:
                    failures.append(f"{attr} points to missing #{ref}")
        if node.tag == "img" and "alt" not in node.attrs:
            failures.append("image is missing alt text")
        if node.tag in {"input", "select", "textarea", "button"} and node.attrs.get("type") != "hidden":
            if not labelled(node, ids, labels):
                failures.append(f"unnamed {node.tag}#{node.attrs.get('id', '')}")
        if node.tag == "a" and node.attrs.get("href") and not (node.text().strip() or node.attrs.get("aria-label", "").strip()):
            failures.append("link has no accessible name")
        if int(node.attrs.get("tabindex", "0") or 0) > 0:
            failures.append("positive tabindex changes the natural keyboard order")
    headings = [int(n.tag[1]) for n in all_nodes if re.fullmatch(r"h[1-6]", n.tag)]
    if any(b - a > 1 for a, b in zip(headings, headings[1:])):
        failures.append("heading level is skipped")
    return failures


def css_failures():
    css = (STATIC / "app.css").read_text(encoding="utf-8")
    failures = []
    required = (":focus-visible", "prefers-reduced-motion", "color-scheme: light", "color-scheme: dark")
    for phrase in required:
        if phrase not in css:
            failures.append(f"CSS is missing {phrase}")
    def variables(selector):
        match = re.search(selector + r"\s*\{([^}]+)\}", css)
        if not match:
            return {}
        return dict(re.findall(r"--([\w-]+)\s*:\s*(#[0-9a-fA-F]{6})", match.group(1)))

    light = variables(r":root")
    dark = variables(r':root\[data-theme="dark"\]')
    wanted = ("bg", "surface", "ink", "ink-2", "ink-3", "accent")
    if any(name not in light for name in wanted) or any(name not in dark for name in wanted):
        failures.append("could not read all principal light and dark colour variables")
    pairs = {
        "light primary text": (light.get("ink", "#000000"), light.get("bg", "#000000")),
        "light secondary text": (light.get("ink-2", "#000000"), light.get("bg", "#000000")),
        "light muted text": (light.get("ink-3", "#000000"), light.get("bg", "#000000")),
        "light button": (light.get("surface", "#000000"), light.get("accent", "#000000")),
        "dark primary text": (dark.get("ink", "#000000"), dark.get("bg", "#000000")),
        "dark secondary text": (dark.get("ink-2", "#000000"), dark.get("bg", "#000000")),
        "dark muted text": (dark.get("ink-3", "#000000"), dark.get("bg", "#000000")),
        "dark button": (dark.get("surface", "#000000"), dark.get("accent", "#000000")),
    }
    for label, (foreground, background) in pairs.items():
        ratio = contrast(foreground, background)
        if ratio < 4.5:
            failures.append(f"{label} contrast is {ratio:.2f}:1, below 4.5:1")
    return failures, pairs


def run():
    results = {name: page_failures(STATIC / name) for name in PAGES}
    css, pairs = css_failures()
    results["app.css"] = css
    return results, pairs


def main():
    results, pairs = run()
    failures = 0
    for name, issues in results.items():
        if issues:
            for issue in issues:
                print(f"FAIL {name}: {issue}")
                failures += 1
        else:
            print(f"PASS {name}")
    for label, colors in pairs.items():
        print(f"PASS contrast {label}: {contrast(*colors):.2f}:1")
    print(f"{len(PAGES)} pages checked; {failures} accessibility regression failures")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
