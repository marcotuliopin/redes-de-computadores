import "./App.css";
import { StatsList } from "../../ui/StatsList";
import { getEscapedRankGameIds, getGameDetails, getSunkRankGameIds } from "./AppUtils";
import { useState } from "react";
import { GameStats } from "../../shared/entities/GameStats";
import { Options } from "../../shared/enums/Options";

const gamesPerApiCall = 50;

export const App = () => {
  const [games, setGames] = useState<Array<GameStats>>([]);
  const [gamesGathered, setGamesGathered] = useState<number>(0);
  const [ascending, setAscending] = useState<boolean>(false);

  const handleClick = async (option: Options) => {
    let ids = null;
    if (option === Options.Sunk)
      ids = await getSunkRankGameIds(1, 50);
    else
      ids = await getEscapedRankGameIds(1, 50);

    if (!ids) return null;

    const infosPromises = ids?.map((id) => getGameDetails(id));
    const infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );

    setGames(infos as GameStats[]);
    setGamesGathered(gamesGathered + gamesPerApiCall);

    return infos;
  };

  const handleChevronClick = (option: Options) => {
    let sortedGames = [...games];
    if (option === Options.Sunk) {
      sortedGames = sortedGames.sort((a, b) => b.sunk - a.sunk);
    }
    else {
      sortedGames = sortedGames.sort((a, b) => b.escaped - a.escaped);
    }
    console.log(sortedGames);
    setGames(sortedGames);
  };

  return (
    <div className="App">
      <div className="header">Bridge Defense Analytics</div>
      <div className="queries">
        <button className="sunk-btn" onClick={() => handleClick(Options.Sunk)}>Sunk Rank</button>
        <button className="escaped-btn" onClick={() => handleClick(Options.Escaped)}>Escaped Rank</button>
      </div>
      <StatsList gameList={games} handleChevronClick={handleChevronClick}/>
    </div>
  );
};
