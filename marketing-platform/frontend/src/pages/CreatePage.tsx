import { useCallback, useEffect, useState } from "react";
import { api, type Clip, type Status } from "../api";
import Library from "../components/Library";
import Chat from "../components/Chat";

// Creazione dei contenuti: libreria dell'hard disk + chat con Claude.
export default function CreatePage({
  status,
  draft,
  setDraft,
  goToSettings,
  goToSchedule,
}: {
  status: Status;
  draft: string;
  setDraft: (d: string) => void;
  goToSettings: () => void;
  goToSchedule: () => void;
}) {
  const [clips, setClips] = useState<Clip[]>([]);
  const [libraryError, setLibraryError] = useState("");
  const [loadingClips, setLoadingClips] = useState(true);
  const [pending, setPending] = useState(0);

  const loadClips = useCallback(async () => {
    setLoadingClips(true);
    try {
      setClips(await api.clips());
      setLibraryError("");
    } catch (e) {
      setClips([]);
      setLibraryError((e as Error).message);
    } finally {
      setLoadingClips(false);
    }
  }, []);

  const loadPending = useCallback(() => {
    api
      .plan()
      .then((items) => setPending(items.filter((i) => i.status === "da_confermare").length))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    loadClips();
    loadPending();
  }, [loadClips, loadPending]);

  return (
    <div className="page create">
      <div className="page-head">
        <h1>Creazione contenuti</h1>
        {pending > 0 && (
          <button className="banner" onClick={goToSchedule}>
            {pending === 1 ? "1 proposta da confermare" : `${pending} proposte da confermare`} → Programmazione
          </button>
        )}
      </div>
      <main className="create-grid">
        <Library
          clips={clips}
          loading={loadingClips}
          error={libraryError}
          onRefresh={loadClips}
          onClipsChanged={loadClips}
          onPrepare={(clip) =>
            setDraft(
              `Prepara titolo, descrizioni e hashtag per «${clip.name}» (id ${clip.id}) e proponimi quando pubblicarla su Instagram, TikTok e YouTube.`,
            )
          }
          goToSettings={goToSettings}
        />
        <Chat
          draft={draft}
          onDraftUsed={() => setDraft("")}
          claudeReady={status.claude}
          goToSettings={goToSettings}
          onWork={(actions) => {
            if (actions.some((a) => a.includes("proposta"))) loadPending();
            if (actions.some((a) => a.includes("trascritto"))) loadClips();
          }}
        />
      </main>
    </div>
  );
}
