import React, { createContext, useContext, useEffect, useState } from 'react';
import * as microsoftTeams from "@microsoft/teams-js";

interface TeamsContextType {
  inTeams: boolean;
  context: microsoftTeams.app.Context | null;
}

const TeamsContext = createContext<TeamsContextType>({
  inTeams: false,
  context: null,
});

// eslint-disable-next-line react-refresh/only-export-components
export const useTeams = () => useContext(TeamsContext);

export const TeamsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [inTeams, setInTeams] = useState(false);
  const [context, setContext] = useState<microsoftTeams.app.Context | null>(null);

  useEffect(() => {
    microsoftTeams.app.initialize().then(() => {
      microsoftTeams.app.getContext().then((ctx) => {
        setInTeams(true);
        setContext(ctx);
        console.log("Teams context loaded:", ctx);
      }).catch(() => {
        setInTeams(false);
        console.log("Running outside of Teams");
      });
    }).catch(() => {
      setInTeams(false);
      console.log("Teams SDK failed to initialize - running outside of Teams");
    });
  }, []);

  return (
    <TeamsContext.Provider value={{ inTeams, context }}>
      {children}
    </TeamsContext.Provider>
  );
};
