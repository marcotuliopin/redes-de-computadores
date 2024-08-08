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
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [currOption, setCurrOption] = useState<Options | null>(null);


  const handleClick = async (option: Options) => {
    let results = null;
    if (option === Options.Sunk) {
      results = await getSunkRankGameIds("/api/rank/sunk?limit=50&start=1");
    } else {
      results = await getEscapedRankGameIds("/api/rank/escaped?limit=50&start=1");
    }
    setCurrOption(option);
    if (!results) return null;

    const { games: ids, prev, next } = results;
    setPrevUrl(prev);
    setNextUrl(next);

    const infosPromises = ids?.map((id) => getGameDetails(id));
    let infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );
    infos = infos.sort((a, b) => a!.id - b!.id);

    setGames(infos as GameStats[]);
    setGamesGathered(gamesGathered + gamesPerApiCall);

    return infos;
  };

  const handleNext = async () => {
    //atualizar gamestart

    let results = null;
    if (currOption === Options.Sunk) {
      console.log(nextUrl)
      results = await getSunkRankGameIds(nextUrl!);
    } else {
      results = await getEscapedRankGameIds(nextUrl!);
    }
    if (!results) return null;

    const { games: ids, prev, next } = results;
    setGamesStart(gamesStart+ids.length)
    setPrevUrl(prev);
    setNextUrl(next);

    const infosPromises = ids?.map((id) => getGameDetails(id));
    const infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );

    setGames(infos as GameStats[]);
    setGamesGathered(gamesGathered + gamesPerApiCall);
    return infos;
  };

  const handlePrev = async () => {
    //atualizar gamestart
    let results = null;
    if (currOption === Options.Sunk) {
      results = await getSunkRankGameIds(prevUrl!);
    } else {
      results = await getEscapedRankGameIds(prevUrl!);
    }
    if (!results) return null;
    setGamesStart(gamesStart-games.length)
    const { games: ids, prev, next } = results;
    setPrevUrl(prev);
    setNextUrl(next);

    const infosPromises = ids?.map((id) => getGameDetails(id));
    const infos = (await Promise.all(infosPromises)).filter(
      (info) => info !== null
    );

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
            onClick={() => handlePrev()}
          />
          <div>{gamesStart}</div> / <div>{gamesStart + 50}</div>
          <ReactSVG
            className="chevron"
            style={{
              transform: "rotate(-90deg)"
            }}
            src="/down-chevron.svg"
            onClick={() => handleNext()}
          />
        </div>
        <StatsList gameList={games} handleChevronClick={handleChevronClick} />
      </div>
    </div>
  );
};
