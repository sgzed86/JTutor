import { describe, expect, it } from "vitest";
import { highlightKanjiFocus } from "./FocusCard";

describe("highlightKanjiFocus", () => {
  it("underlines lesson kanji in example sentences", () => {
    const nodes = highlightKanjiFocus("父と母です。", ["父", "母", "子ども", "日本"]);
    const text = nodes.map((n) => (typeof n === "string" ? n : (n as { props: { children: string } }).props.children));
    expect(text).toEqual(["父", "と", "母", "です。"]);
  });

  it("prefers longer headwords first", () => {
    const nodes = highlightKanjiFocus("日本に住んでいます。", ["日", "日本"]);
    const first = nodes[0] as { props: { children: string; className: string } };
    expect(first.props.children).toBe("日本");
    expect(first.props.className).toBe("kanji-focus");
  });
});
