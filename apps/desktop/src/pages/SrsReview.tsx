import { useEffect, useState } from "react";
import { api } from "../api";

export default function SrsReview() {
  const [cards, setCards] = useState<any[]>([]);
  const [idx, setIdx] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [stats, setStats] = useState({ due: 0, total: 0 });
  const [msg, setMsg] = useState("");

  async function load() {
    const [due, st] = await Promise.all([api.srsDue(), api.srsStats()]);
    setCards(due.cards || []);
    setIdx(0);
    setFlipped(false);
    setStats(st);
  }

  useEffect(() => {
    load().catch((e) => setMsg(String(e)));
  }, []);

  const card = cards[idx];

  async function rate(rating: number) {
    if (!card) return;
    await api.srsReview(card.id, rating);
    const next = cards.filter((_, i) => i !== idx);
    setCards(next);
    setFlipped(false);
    setIdx(0);
    const st = await api.srsStats();
    setStats(st);
  }

  async function seedCurrent() {
    setMsg("Seeding L01 SRS…");
    const r = await api.seedSrs("L01");
    setMsg(`Added vocab ${r.vocab_cards}, grammar ${r.grammar_cards}`);
    await load();
  }

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <h1>SRS review</h1>
          <p className="muted">{stats.due} due · {stats.total} total</p>
        </div>
        <button className="btn" onClick={seedCurrent}>
          Seed L01 cards
        </button>
      </div>
      {msg && <p className="muted">{msg}</p>}
      {!card ? (
        <div className="panel">
          <h2>All caught up</h2>
          <p className="muted">No cards due. Study a lesson to generate more.</p>
        </div>
      ) : (
        <div className="panel stack">
          <p className="muted">
            {card.card_type} · {card.lesson_id} · {idx + 1}/{cards.length}
          </p>
          <div className="flashcard panel" onClick={() => setFlipped((f) => !f)} style={{ cursor: "pointer" }}>
            {flipped ? card.back : card.front}
          </div>
          <p className="muted">Click card to flip</p>
          <div className="row">
            <button className="btn danger" onClick={() => rate(1)}>Again</button>
            <button className="btn" onClick={() => rate(2)}>Hard</button>
            <button className="btn ok" onClick={() => rate(3)}>Good</button>
            <button className="btn primary" onClick={() => rate(4)}>Easy</button>
          </div>
        </div>
      )}
    </div>
  );
}
