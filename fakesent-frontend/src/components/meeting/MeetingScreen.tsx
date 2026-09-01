import { useEffect, useRef, useState } from "react";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { useSessionAnalysis } from "../../hooks/useSessionAnalysis";
import type { ParticipantStatus } from "../../types/backend";
import type { ParticipantViewModel } from "../../types/viewModels";
import { APP_CONFIG } from "../../constants/appConfig";
import { USE_MOCK_PARTICIPANTS } from "../../constants/env";
import { theme } from "../../constants/theme";

const STATUS_LABELS: Record<ParticipantStatus, string> = {
  analyzing: "ANALİZ EDİLİYOR",
  authentic: "GERÇEK",
  suspicious: "RİSKLİ",
  disconnected: "BAĞLANTI KESİLDİ",
};

function getStatusColor(status: ParticipantStatus): string {
  switch (status) {
    case "authentic":
      return theme.colors.authentic;
    case "suspicious":
      return theme.colors.suspicious;
    case "analyzing":
      return theme.colors.analyzing;
    case "disconnected":
      return theme.colors.disconnected;
  }
}

function getScorePercentage(viewModel: ParticipantViewModel): number | null {
  return viewModel.latestAnalysis
    ? Math.round(viewModel.latestAnalysis.realityScore * 100)
    : null;
}

export function MeetingScreen() {
  useSessionAnalysis();
  const [isRemovedSectionOpen, setIsRemovedSectionOpen] = useState(false);
  const [isDisconnectedSectionOpen, setIsDisconnectedSectionOpen] =
    useState(false);
  const [removingParticipantId, setRemovingParticipantId] = useState<
    string | null
  >(null);
  const removalTimeoutRef = useRef<number | null>(null);

  const {
    session,
    participants,
    removedParticipants,
    isLoading,
    connectionState,
    error,
    removeParticipantForDemo,
  } = useAnalysisStore();

  const disconnectedParticipants = participants.filter(
    ({ participant }) => participant.status === "disconnected",
  );
  const gridParticipants = participants.filter(
    ({ participant }) => participant.status !== "disconnected",
  );

  const participantGroups: Array<{
    status: ParticipantStatus;
    title: string;
  }> = [
    { status: "suspicious", title: "RİSKLİ KATILIMCILAR" },
    { status: "analyzing", title: "ANALİZ EDİLEN KATILIMCILAR" },
    { status: "authentic", title: "GERÇEK KATILIMCILAR" },
  ];

  useEffect(
    () => () => {
      if (removalTimeoutRef.current !== null) {
        window.clearTimeout(removalTimeoutRef.current);
      }
    },
    [],
  );

  const handleRemoveParticipant = (participantId: string) => {
    if (!USE_MOCK_PARTICIPANTS || removingParticipantId !== null) return;

    setRemovingParticipantId(participantId);
    removalTimeoutRef.current = window.setTimeout(() => {
      removeParticipantForDemo(participantId);
      setRemovingParticipantId(null);
      removalTimeoutRef.current = null;
    }, 300);
  };

  return (
    <div
      style={{
        width: "100vw",
        height: "100vh",
        background: theme.colors.appBackground,
        display: "flex",
        flexDirection: "column",
        fontFamily: theme.font.heading,
      }}
    >
      <header
        style={{
          minHeight: "60px",
          background: theme.colors.headerBackground,
          borderBottom: `1px solid ${theme.colors.cyan}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 20px",
          color: theme.colors.textLight,
          gap: "20px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center" }}>
          <img
            src="/personalive_logo.png"
            alt="PersonaLive"
            style={{
              height: "38px",
              width: "auto",
              objectFit: "contain",
              marginRight: "12px",
            }}
          />
          <span style={{ fontWeight: "bold", fontSize: "1.1rem" }}>
            {APP_CONFIG.name} — Çoklu Konferans Güvenliği
          </span>
        </div>
        {session && (
          <span
            style={{
              color: theme.colors.textSecondaryLight,
              fontSize: "0.85rem",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {session.title}
          </span>
        )}
      </header>

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <main
          style={{
            flex: 1,
            padding: "20px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gridAutoRows: "minmax(180px, 1fr)",
            alignContent: "start",
            gap: "15px",
            position: "relative",
            overflowY: "auto",
          }}
        >
          {error && (
            <div
              role="alert"
              style={{
                gridColumn: "1 / -1",
                background: theme.colors.suspicious,
                color: theme.colors.textLight,
                padding: "12px 20px",
                borderRadius: "8px",
              }}
            >
              {error}
            </div>
          )}

          {connectionState === "reconnecting" && (
            <div
              role="status"
              style={{
                gridColumn: "1 / -1",
                background: theme.colors.warning,
                color: theme.colors.textDark,
                padding: "12px 20px",
                borderRadius: "8px",
                fontWeight: "bold",
              }}
            >
              Bağlantı kaybedildi. Yeniden bağlanılıyor…
            </div>
          )}

          {connectionState === "disconnected" && (
            <div
              role="status"
              style={{
                gridColumn: "1 / -1",
                background: theme.colors.cameraBackgroundAlt,
                color: theme.colors.textSecondaryLight,
                padding: "12px 20px",
                borderRadius: "8px",
              }}
            >
              Oturum bağlantısı kesildi.
            </div>
          )}

          {isLoading ? (
            <div
              role="status"
              style={{
                gridColumn: "1 / -1",
                color: theme.colors.textSecondaryDark,
                textAlign: "center",
                padding: "60px 20px",
              }}
            >
              Katılımcılar yükleniyor…
            </div>
          ) : gridParticipants.length === 0 ? (
            <div
              style={{
                gridColumn: "1 / -1",
                color: theme.colors.textSecondaryDark,
                textAlign: "center",
                padding: "60px 20px",
              }}
            >
              Kamera alanında gösterilecek bağlı katılımcı bulunmuyor.
            </div>
          ) : (
            gridParticipants.map((viewModel) => {
              const { participant } = viewModel;
              const percentage = getScorePercentage(viewModel);
              const statusColor = getStatusColor(participant.status);
              const isRemoving =
                removingParticipantId === participant.participantId;

              return (
                <article
                  key={participant.participantId}
                  style={{
                    minHeight: "180px",
                    background: theme.colors.cameraBackground,
                    borderRadius: "12px",
                    border: `2px solid ${statusColor}`,
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                    opacity: isRemoving ? 0 : 1,
                    transform: isRemoving
                      ? "translateY(6px) scale(0.96)"
                      : "translateY(0) scale(1)",
                    pointerEvents: isRemoving ? "none" : "auto",
                    transition:
                      "opacity 300ms ease, transform 300ms ease, border-color 0.3s ease",
                  }}
                >
                  <span style={{ color: theme.colors.textSecondaryLight }}>
                    {`Kamera Akışı (${participant.displayName})`}
                  </span>

                  <div
                    style={{
                      position: "absolute",
                      top: "10px",
                      right: "10px",
                      color: statusColor,
                      background: "rgba(0,0,0,0.7)",
                      padding: "4px 8px",
                      borderRadius: "4px",
                      fontSize: "0.7rem",
                      fontWeight: "bold",
                    }}
                  >
                    {STATUS_LABELS[participant.status]}
                  </div>

                  <div
                    style={{
                      position: "absolute",
                      bottom: "10px",
                      left: "10px",
                      right: "10px",
                      background: "rgba(0,0,0,0.7)",
                      padding: "6px 8px",
                      borderRadius: "4px",
                      color: theme.colors.textLight,
                      fontSize: "0.8rem",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    <span
                      style={{
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {participant.displayName}
                    </span>
                    <span style={{ color: statusColor, fontWeight: "bold" }}>
                      {percentage === null ? "Analiz bekleniyor" : `${percentage}%`}
                    </span>
                  </div>
                </article>
              );
            })
          )}
        </main>

        <aside
          style={{
            width: "360px",
            background: theme.colors.sidebarBackground,
            borderLeft: `1px solid ${theme.colors.cyan}`,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              padding: "20px 20px 5px",
              flex: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "25px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h3
                style={{
                  margin: 0,
                  color: theme.colors.textDark,
                  fontSize: "1rem",
                }}
              >
                Katılımcı Durumları
              </h3>
              <span
                style={{
                  fontSize: "0.75rem",
                  background: theme.colors.sidebarCardBackground,
                  padding: "4px 8px",
                  borderRadius: "12px",
                  color: theme.colors.primary,
                }}
              >
                Toplam: {participants.length}
              </span>
            </div>

            {!isLoading && participants.length === 0 && (
              <p
                style={{
                  color: theme.colors.textSecondaryDark,
                  fontSize: "0.85rem",
                  lineHeight: "1.5",
                }}
              >
                Katılımcı verisi henüz mevcut değil.
              </p>
            )}

            {participantGroups.map(({ status, title }) => {
              const group = participants.filter(
                ({ participant }) => participant.status === status,
              );
              if (group.length === 0) return null;

              const statusColor = getStatusColor(status);

              return (
                <section key={status}>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      color: statusColor,
                      fontWeight: "bold",
                      marginBottom: "10px",
                      borderBottom: `1px solid ${statusColor}`,
                      paddingBottom: "4px",
                    }}
                  >
                    {title} ({group.length})
                  </div>

                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    {group.map((viewModel) => {
                      const { participant } = viewModel;
                      const percentage = getScorePercentage(viewModel);
                      const isRemovalDisabled =
                        !USE_MOCK_PARTICIPANTS ||
                        removingParticipantId !== null;

                      return (
                        <div
                          key={participant.participantId}
                          style={{
                            padding: "12px",
                            borderRadius: "6px",
                            background: theme.colors.sidebarCardBackground,
                            border: `1px solid ${statusColor}`,
                            display: "flex",
                            flexDirection: "column",
                            gap: "8px",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              justifyContent: "space-between",
                              alignItems: "center",
                              gap: "10px",
                            }}
                          >
                            <span
                              style={{
                                color: theme.colors.textDark,
                                fontSize: "0.9rem",
                              }}
                            >
                              {participant.displayName}
                            </span>
                            <span
                              style={{ color: statusColor, fontWeight: "bold" }}
                            >
                              {percentage === null ? "—" : `${percentage}%`}
                            </span>
                          </div>

                          {percentage === null ? (
                            <span
                              style={{
                                color: theme.colors.disconnected,
                                fontSize: "0.75rem",
                              }}
                            >
                              Analiz sonucu bekleniyor
                            </span>
                          ) : (
                            <div
                              style={{
                                width: "100%",
                                height: "6px",
                                background: theme.colors.progressTrackLight,
                                borderRadius: "3px",
                                overflow: "hidden",
                              }}
                            >
                              <div
                                style={{
                                  width: `${percentage}%`,
                                  height: "100%",
                                  background: statusColor,
                                  transition: "width 0.5s ease",
                                }}
                              />
                            </div>
                          )}

                          {status === "suspicious" && (
                            <>
                              <button
                                type="button"
                                disabled={isRemovalDisabled}
                                onClick={() =>
                                  handleRemoveParticipant(
                                    participant.participantId,
                                  )
                                }
                                title={
                                  !USE_MOCK_PARTICIPANTS
                                    ? "Backend katılımcı bağlantısını kesme desteği henüz mevcut değil"
                                    : removingParticipantId !== null
                                      ? "Katılımcı toplantıdan çıkarılıyor"
                                      : "Katılımcıyı demo toplantısından çıkar"
                                }
                                style={{
                                  padding: "8px",
                                  background: !isRemovalDisabled
                                    ? theme.colors.suspicious
                                    : theme.colors.progressTrackLight,
                                  color: !isRemovalDisabled
                                    ? theme.colors.textLight
                                    : theme.colors.disconnected,
                                  border: "none",
                                  borderRadius: "4px",
                                  fontSize: "0.75rem",
                                  fontWeight: "bold",
                                  cursor: !isRemovalDisabled
                                    ? "pointer"
                                    : "not-allowed",
                                  opacity: !isRemovalDisabled ? 1 : 0.7,
                                }}
                              >
                                Toplantıdan Çıkar
                              </button>
                              {!USE_MOCK_PARTICIPANTS && (
                                <span
                                  style={{
                                    color: theme.colors.disconnected,
                                    fontSize: "0.7rem",
                                  }}
                                >
                                  Backend bağlantı kesme desteği henüz mevcut
                                  değil.
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
            <div style={{ marginTop: "auto", paddingTop: "4px" }}>
            {disconnectedParticipants.length > 0 && (
              <section
                style={{
                  marginBottom:
                    removedParticipants.length > 0 ? "6px" : "0",
                }}
              >
                <button
                  type="button"
                  onClick={() =>
                    setIsDisconnectedSectionOpen((isOpen) => !isOpen)
                  }
                  aria-expanded={isDisconnectedSectionOpen}
                  style={{
                    width: "100%",
                    padding: "8px 0",
                    background: "transparent",
                    border: "none",
                    boxShadow: "none",
                    color: theme.colors.disconnected,
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "0.75rem",
                    fontWeight: "bold",
                    textAlign: "left",
                    cursor: "pointer",
                  }}
                >
                  <span aria-hidden="true">
                    {isDisconnectedSectionOpen ? "▾" : "▸"}
                  </span>
                  <span>
                    BAĞLANTISI KESİLENLER ({disconnectedParticipants.length})
                  </span>
                </button>

                {isDisconnectedSectionOpen && (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                      marginTop: "6px",
                    }}
                  >
                    {disconnectedParticipants.map((viewModel) => {
                      const percentage = getScorePercentage(viewModel);

                      return (
                        <div
                          key={viewModel.participant.participantId}
                          style={{
                            padding: "8px 10px",
                            borderRadius: "6px",
                            background: theme.colors.sidebarCardBackground,
                            border: `1px solid ${theme.colors.borderLight}`,
                            color: theme.colors.textSecondaryDark,
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "10px",
                          }}
                        >
                          <span>{viewModel.participant.displayName}</span>
                          {percentage !== null && <span>{percentage}%</span>}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            )}

            {removedParticipants.length > 0 && (
              <section style={{ marginBottom: "0" }}>
                <button
                  type="button"
                  onClick={() =>
                    setIsRemovedSectionOpen((isOpen) => !isOpen)
                  }
                  aria-expanded={isRemovedSectionOpen}
                  style={{
                    width: "100%",
                    padding: "8px 0",
                    background: "transparent",
                    border: "none",
                    boxShadow: "none",
                    color: theme.colors.disconnected,
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "0.75rem",
                    fontWeight: "bold",
                    textAlign: "left",
                    cursor: "pointer",
                  }}
                >
                  <span aria-hidden="true">
                    {isRemovedSectionOpen ? "▾" : "▸"}
                  </span>
                  <span>
                    TOPLANTIDAN ÇIKARILANLAR ({removedParticipants.length})
                  </span>
                </button>

                {isRemovedSectionOpen && (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "6px",
                      marginTop: "6px",
                    }}
                  >
                    {removedParticipants.map((viewModel) => {
                      const percentage = getScorePercentage(viewModel);

                      return (
                        <div
                          key={viewModel.participant.participantId}
                          style={{
                            padding: "8px 10px",
                            borderRadius: "6px",
                            background: theme.colors.sidebarCardBackground,
                            color: theme.colors.textSecondaryDark,
                            display: "flex",
                            justifyContent: "space-between",
                            gap: "10px",
                          }}
                        >
                          <span>{viewModel.participant.displayName}</span>
                          {percentage !== null && <span>{percentage}%</span>}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            )}
            </div>
          </div>

          <div
            style={{
              padding: "14px 20px",
              background: theme.colors.sidebarFooterBackground,
              borderTop: `1px solid ${theme.colors.borderLight}`,
              color: theme.colors.textSecondaryDark,
              fontSize: "0.8rem",
            }}
          >
            <div>
              {session
                ? `Oturum durumu: ${session.status}`
                : "Oturum verisi bekleniyor"}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
