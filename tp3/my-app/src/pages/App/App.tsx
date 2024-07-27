import "./App.css";
import { StatsList } from "../../ui/StatsList";
import { getEscapedRankGameIds, getGameDetails, getSunkRankGameIds } from "./AppUtils";
import { useState } from "react";
import { GameStats } from "../../shared/entities/GameStats";

const enum Options {
  Sunk = 'sunk',
  Escaped = 'escaped',
};

export const App = () => {
  const [games, setGames] = useState<Array<GameStats>>([]);

  const handleClick = async (option: Options) => {
    let ids = null;
    if (option === Options.Sunk)
      ids = await getSunkRankGameIds();
    else
      ids = await getEscapedRankGameIds();

    if (!ids) return null;

    const infosPromises = ids?.map((id) => getGameDetails(id));
    const infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );
    setGames(infos as GameStats[]);

    return infos;
  };

  return (
    <div className="App">
      <div className="queries">
        <button onClick={() => handleClick(Options.Sunk)}>Sunk Rank</button>
        <button onClick={() => handleClick(Options.Escaped)}>Escaped Rank</button>
      </div>
      <StatsList gameList={games} />
    </div>
  );
};
