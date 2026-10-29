"use client";

import { useEffect, useRef, useState } from "react";
import { api, type JournalDetail } from "@/lib/api";

const INPUT =
  "rounded border border-border bg-surface-2 px-2 py-1.5 text-sm text-fg placeholder:text-muted focus:border-accent focus:outline-none";

const dt = (s: string) => new Date(s).toLocaleString();

export default function JournalView() {
  const [entries, setEntries] = useState<JournalDetail[] | null>(null);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [tags, setTags] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    void load();
  }, []);

  async function load() {
    try {
      const page = await api.listJournal();
      // List has no images; fetch each entry's detail for its screenshots.
      // ponytail: N+1, fine for a personal journal; add images to the list if it grows.
      const details = await Promise.all(page.items.map((e) => api.getJournalEntry(e.id)));
      setEntries(details);
    } catch (e) {
      setError(String(e));
    }
  }

  async function save() {
    if (!title.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const entry = await api.createJournalEntry({
        title: title.trim(),
        notes,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      if (file) {
        const form = new FormData();
        form.append("file", file);
        await api.uploadJournalImage(entry.id, form);
      }
      setTitle("");
      setNotes("");
      setTags("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: string) {
    setBusy(true);
    setError(null);
    try {
      await api.deleteJournalEntry(id);
      setConfirmId(null);
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      {error && (
        <p className="rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>
      )}

      {/* New entry */}
      <section className="rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-4 text-sm font-semibold">Nueva entrada</h2>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Título (p. ej. BTC rompió resistencia)"
          className={`${INPUT} w-full`}
        />
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notas: tesis, entrada/salida, qué aprendiste…"
          rows={4}
          className={`${INPUT} mt-3 w-full resize-y`}
        />
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <input
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="etiquetas, separadas, por coma"
            className={`${INPUT} flex-1`}
          />
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm text-muted file:mr-2 file:rounded file:border file:border-border file:bg-surface-2 file:px-2 file:py-1 file:text-sm file:text-fg"
          />
        </div>
        <button
          onClick={save}
          disabled={busy || !title.trim()}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-50"
        >
          {busy && (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          )}
          Guardar entrada
        </button>
      </section>

      {/* Entries */}
      {entries === null ? (
        <p className="text-sm text-muted">Cargando…</p>
      ) : entries.length === 0 ? (
        <p className="rounded-lg border border-border bg-surface p-6 text-sm text-muted">
          Tu diario está vacío. Registra tu primera idea u operación arriba.
        </p>
      ) : (
        entries.map((e) => (
          <article key={e.id} className="rounded-xl border border-border bg-surface p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="font-medium">{e.title}</h3>
                <div className="text-xs text-muted">{dt(e.created_at)}</div>
              </div>
              {confirmId === e.id ? (
                <span className="flex items-center gap-2 text-xs">
                  <span className="text-muted">¿Eliminar?</span>
                  <button onClick={() => remove(e.id)} className="text-neg hover:underline">
                    sí
                  </button>
                  <button onClick={() => setConfirmId(null)} className="text-muted hover:underline">
                    no
                  </button>
                </span>
              ) : (
                <button
                  onClick={() => setConfirmId(e.id)}
                  className="text-xs text-muted hover:text-neg"
                >
                  eliminar
                </button>
              )}
            </div>

            {e.notes && <p className="mt-2 whitespace-pre-wrap text-sm text-fg/90">{e.notes}</p>}

            {e.tags.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {e.tags.map((t) => (
                  <span
                    key={t}
                    className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs text-muted"
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}

            {e.images.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {e.images.map((img) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    key={img.id}
                    src={api.journalImageUrl(e.id, img.id)}
                    alt={img.filename}
                    className="h-28 rounded border border-border object-cover"
                  />
                ))}
              </div>
            )}
          </article>
        ))
      )}
    </div>
  );
}
