import type { TutorPayload } from "../../api/types";
import { BookPage } from "../stage/BookPage";

/** Compact book preview kept for the context drawer when the stage isn't showing it. */
export function BookTab({ payload }: { payload: TutorPayload | null }) {
  if (!payload) {
    return <p className="ask__empty">Open a lesson to see the book page.</p>;
  }
  return <BookPage payload={payload} variant="panel" />;
}
