import { useCallback, useEffect, useState } from "react";
import { api, type Clip, type Status } from "../api";
import Library from "../components/Library";
import Chat from "../components/Chat";
import Plan from "../components/Plan";

// Schermata di lavoro: libreria | chat | piano
export default function Workspace({ status, goToSettings }: { status: Status; goToSettings: () => void }) {
  const [clips, setClips] = useState<Clip[]>([]);
  const [libraryError, setLibraryError] = useState("");
  const [loadingClips, setLoadingClips] = useState(true);
  const [draft, setDraft] = useState("");
  const [planVersion, setPlanVersion] = useState(0);

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

  useEffect(() => {
    loadClips();
  }, [loadClips]);

  return (
    <main className="workspace">
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
          if (actions.some((a) => a.includes("proposta"))) setPlanVersion((v) => v + 1);
          if (actions.some((a) => a.includes("trascritto"))) loadClips();
        }}
      />
      <Plan version={planVersion} dryRun={status.dry_run} />
    </main>
  );
}
