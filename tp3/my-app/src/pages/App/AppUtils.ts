import { GameStats } from "../../shared/entities/GameStats";

const LIMIT = 50;
const START = 1;

export const getSunkRankGameIds = async (): Promise<Array<number> | null> => {
  try {
    const response = await fetch(
      `http://localhost:3000/api/rank/sunk?limit=${LIMIT}&start=${START}`
    );
    const data = await response.json();
    console.log(data);
    return data.games;
  } catch (error) {
    console.log(error);
    return null;
  }
};

export const getEscapedRankGameIds = async (): Promise<Array<number> | null> => {
    try {
      const response = await fetch(
        `http://localhost:3000/api/rank/escaped?limit=${LIMIT}&start=${START}`
      );
      const data = await response.json();
      return data.games;
    } catch (error) {
      console.log(error);
      return null;
    }
  };

export const getGameDetails = async (id: number): Promise<GameStats | null> => {
  try {
    const response = await fetch(`http://localhost:3000/api/game/${id}`);
    const data = await response.json();
    return {
      id: data.game_id,
      gas: data.game_stats.auth,
      escaped: data.game_stats.escaped_ships,
      sunk: data.game_stats.sunk_ships,
    };
  } catch (error) {
    console.log(error);
    return null;
  }
};
