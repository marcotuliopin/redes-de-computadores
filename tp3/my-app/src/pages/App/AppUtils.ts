import { GameStats } from "../../shared/entities/GameStats";

export const getSunkRankGameIds = async (
  request: string
)  : Promise<{ games: Array<number>; prev: string | null; next: string | null } | null> => {
  try {
    const response = await fetch(
      `http://localhost:3000/` + request
    );
    const data = await response.json();
    return {
      games: data.games,
      prev: data.prev,
      next: data.next
    };
  } catch (error) {
    console.log(error);
    return null;
  }
};

export const getEscapedRankGameIds = async (
  request: string
)  : Promise<{ games: Array<number>; prev: string | null; next: string | null } | null> => {
    try {
      const response = await fetch(
        `http://localhost:3000/`+ request
      );
      const data = await response.json();
      return {
        games: data.games,
        prev: data.prev,
        next: data.next
      };
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
