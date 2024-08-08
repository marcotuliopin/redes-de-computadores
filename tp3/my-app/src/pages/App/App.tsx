import "./App.css";
import { StatsList } from "../../ui/StatsList";
import {
  getEscapedRankGameIds,
  getGameDetails,
  getSunkRankGameIds,
} from "./AppUtils";
import { useState } from "react";
import { GameStats } from "../../shared/entities/GameStats";
import { Options } from "../../shared/enums/Options";
import { ReactSVG } from "react-svg";

const gamesPerApiCall = 50;

export const App = () => {
  const [games, setGames] = useState<Array<GameStats>>([]);
  const [gamesGathered, setGamesGathered] = useState<number>(0);
  const [gamesStart, setGamesStart] = useState<number>(0);

  const handleClick = async (option: Options) => {
    let ids = null;
    if (option === Options.Sunk) ids = await getSunkRankGameIds(1, 50);
    else ids = await getEscapedRankGameIds(1, 50);

    if (!ids) return null;

    const infosPromises = ids?.map((id) => getGameDetails(id));
    let infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );
    infos = infos.sort((a, b) => a!.id - b!.id);

    setGames(infos as GameStats[]);
    setGamesGathered(gamesGathered + gamesPerApiCall);

    return infos;
  };

  const handleChevronClick = (option: Options, order: boolean) => {
    let sortedGames = [...games];
    if (option === Options.Sunk) {
      if (order) sortedGames = sortedGames.sort((a, b) => b.sunk - a.sunk);
      else sortedGames = sortedGames.sort((a, b) => a.sunk - b.sunk);
    } else {
      if (order)
        sortedGames = sortedGames.sort((a, b) => b.escaped - a.escaped);
      else sortedGames = sortedGames.sort((a, b) => a.escaped - b.escaped);
    }
    console.log(sortedGames);
    setGames(sortedGames);
  };

  return (
    <div className="App">
      <div className="header">Bridge Defense Analytics</div>
      <div className="queries">
        <button className="sunk-btn" onClick={() => handleClick(Options.Sunk)}>
          Sunk Rank
        </button>
        <button
          className="escaped-btn"
          onClick={() => handleClick(Options.Escaped)}
        >
          Escaped Rank
        </button>
      </div>
      <div className="table">
        <div className="table-menu">
          <ReactSVG
            className="chevron"
            style={{
              transform: "rotate(90deg)"
            }}
            src="/down-chevron.svg"
          />
          <div>{gamesStart}</div> / <div>{gamesStart + 50}</div>
          <ReactSVG
            className="chevron"
            style={{
              transform: "rotate(-90deg)"
            }}
            src="/down-chevron.svg"
          />
        </div>
        <StatsList gameList={games} handleChevronClick={handleChevronClick} />
      </div>
    </div>
  );
};
