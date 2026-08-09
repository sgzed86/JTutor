import { useEffect, useState } from "react";
import { api } from "../api";

type Props = {
  onChanged?: (bookId: string) => void;
  compact?: boolean;
};

export function BookSwitcher({ onChanged, compact }: Props) {
  const [books, setBooks] = useState<any[]>([]);
  const [active, setActive] = useState("starter");
  const [busy, setBusy] = useState(false);

  const reload = async () => {
    const data = await api.books();
    setBooks(data.books || []);
    setActive(data.active || "starter");
  };

  useEffect(() => {
    void reload().catch(() => undefined);
  }, []);

  const change = async (bookId: string) => {
    if (bookId === active || busy) return;
    setBusy(true);
    try {
      await api.setBook(bookId);
      setActive(bookId);
      onChanged?.(bookId);
    } finally {
      setBusy(false);
    }
  };

  if (!books.length) return null;

  return (
    <label className="book-switcher" style={{ display: "grid", gap: compact ? 2 : 6 }}>
      {!compact && <span className="muted" style={{ fontSize: "0.8rem" }}>Book</span>}
      <select
        value={active}
        disabled={busy}
        onChange={(e) => void change(e.target.value)}
        style={{
          background: "var(--bg2)",
          color: "var(--ink)",
          border: "1px solid var(--line)",
          borderRadius: 10,
          padding: compact ? "0.35rem 0.5rem" : "0.45rem 0.7rem",
          maxWidth: "100%",
        }}
      >
        {books.map((b) => (
          <option key={b.id} value={b.id} disabled={!b.available}>
            {b.title}
            {!b.available ? " (not built)" : ""}
          </option>
        ))}
      </select>
    </label>
  );
}
