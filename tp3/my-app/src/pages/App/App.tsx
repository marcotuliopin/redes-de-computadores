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
  const [prevUrl, setPrevUrl] = useState<string | null>(null);
  const [nextUrl, setNextUrl] = useState<string | null>(null);


  const handleClick = async (option: Options) => {
    let results = null;
    if (option === Options.Sunk) {
      results = await getSunkRankGameIds("api/rank/sunk?limit=50&start=1");
    } else {
      results = await getEscapedRankGameIds("api/rank/escaped?limit=50&start=1");
    }

    if (!results) return null;

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

  const handleNext = async (option: Options) => {
    let results = null;
    if (option === Options.Sunk) {
      results = await getSunkRankGameIds(nextUrl);
    } else {
      results = await getEscapedRankGameIds(nextUrl);
    }
    if (!results) return null;

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

  const handlePrev = async (option: Options) => {
    let results = null;
    if (option === Options.Sunk) {
      results = await getSunkRankGameIds(prevUrl);
    } else {
      results = await getEscapedRankGameIds(prevUrl);
    }
    if (!results) return null;

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
