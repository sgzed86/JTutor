import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { SrsCard } from "../api/types";
import { useSettings } from "../state/useSettings";

const RATINGS = [
  { rating: 1, label: "Again", className: "btn btn--danger" },
  { rating: 2, label: "Hard", className: "btn" },
  { rating: 3, label: "Good", className: "btn btn--success" },
  { rating: 4, label: "Easy", className: "btn btn--primary" },
];

export function SrsPage() {
  const { settings } = useSettings();
  const [cards, setCards] = useState<SrsCard[]>([]);
  const [stats, setStats] = useState({ due: 0, total: 0 });
  const [flipped, setFlipped] = useState(false);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      const [due, s] = await Promise.all([api.srsDue(), api.srsStats()]);
      setCards(due.cards);
      setStats(s);
      setFlipped(false);
    } catch {
      setMessage("Couldn't load your review cards.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const card = cards[0];

  const rate = async (rating: number) => {
    if (!card) return;
    await api.srsReview(card.id, rating).catch(() => undefined);
    setCards((current) => current.slice(1));
    setFlipped(false);
    setStats(await api.srsStats().catch(() => stats));
  };

  return (
    <main className="main">
      <div className="page">
        <div className="page__head">
          <div>
            <h1>Review</h1>
            <p className="muted">
              {stats.due} due · {stats.total} cards
            </p>
          </div>
          {settings.advanced.developer_tools && (
            <button
              type="button"
              className="btn btn--ghost"
              onClick={async () => {
                const r = await api.seedSrs("L01").catch(() => null);
                setMessage(r ? `Seeded ${r.vocab_cards} vocab, ${r.grammar_cards} grammar cards.` : "Seeding failed.");
                void load();
              }}
            >
              Seed L01 cards
            </button>
          )}
        </div>

        {message && <p className="muted">{message}</p>}

        {!card ? (
          <div className="panel empty-state">
            <h2>Nothing to review</h2>
            <p>Words you struggle with during a lesson appear here automatically.</p>
          </div>
        ) : (
          <div className="panel" style={{ display: "flex", flexDirection: "column", gap: "var(--sp-3)" }}>
            <p className="muted">
              {card.card_type} · {card.lesson_id} · {cards.length} left
            </p>
            <button
              type="button"
              className="panel flashcard jp"
              onClick={() => setFlipped((f) => !f)}
              aria-label={flipped ? "Show the front" : "Show the answer"}
            >
              {flipped ? card.back : card.front}
            </button>
            <p className="muted">Click the card to flip it.</p>
            <div style={{ display: "flex", gap: "var(--sp-2)", flexWrap: "wrap" }}>
              {RATINGS.map((r) => (
                <button
                  key={r.rating}
                  type="button"
                  className={r.className}
                  disabled={!flipped}
                  onClick={() => void rate(r.rating)}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
