// src/services/errorMessages.ts
export const ERROR_MESSAGES: Record<string, string> = {
  'HTTP 401': 'Sessione scaduta. Effettua nuovamente il login.',
  'HTTP 403': 'Non hai i permessi per questa azione.',
  'HTTP 404': 'Risorsa non trovata.',
  'HTTP 500': 'Errore del server. Riprova tra qualche minuto.',
  'HTTP 502': "Servizio temporaneamente non raggiungibile.",
  'HTTP 504': 'Timeout. Il server ha impiegato troppo tempo a rispondere.',
  'Failed to fetch': 'Impossibile connettersi al server. Verifica la connessione.',
};

export function getUserMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  for (const [key, friendly] of Object.entries(ERROR_MESSAGES)) {
    if (message.includes(key)) return friendly;
  }
  return message || 'Si è verificato un errore imprevisto.';
}
