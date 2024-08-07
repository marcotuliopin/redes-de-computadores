import "./StatsList.style.css";
import { FC, useState } from "react";
import { GameStats } from "../../shared/entities/GameStats";

interface StatsListProps {
  gameList: Array<GameStats>;
}

export const StatsList: FC<StatsListProps> = ({ gameList }) => {
  const [selectedRow, setSelectedRow] = useState<number>(-1);

  const handleRowClick = (index: number) => {
    setSelectedRow(index === selectedRow ? -1 : index);
  };

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
            <tr
              key={`game-${game.id}`}
              id={`game-${i}`}
              onClick={() => handleRowClick(i)}
              className={selectedRow === i ? "selected" : ""}
            >
              <td className="expandable">{game.gas}</td>
              <td>{game.escaped}</td>
              <td>{game.sunk}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
