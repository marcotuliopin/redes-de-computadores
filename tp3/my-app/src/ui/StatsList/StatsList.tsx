import "./StatsList.style.css"
import { FC } from "react";
import { GameStats } from "../../shared/entities/GameStats";

interface StatsListProps {
  gameList: Array<GameStats>;
}

export const StatsList: FC<StatsListProps> = ({ gameList }) => {
  return (
    <div>
      <table>
        <thead>
          <tr>
            <th>Gas</th>
            <th>Ships Escaped</th>
            <th>Ships Sunk</th>
          </tr>
        </thead>
        <tbody>
          {gameList.map((game, i) => (
            <tr key={`game-${game.id}`} id={`game-${i}`}>
              <td>{game.gas}</td>
              <td>{game.escaped}</td>
              <td>{game.sunk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
