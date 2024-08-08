import "./StatsList.style.css";
import { FC, useState } from "react";
import { GameStats } from "../../shared/entities/GameStats";
import { ReactSVG } from "react-svg";
import { Options } from "../../shared/enums/Options";

interface StatsListProps {
  gameList: Array<GameStats>;
  handleChevronClick: (option: Options) => void;
}

export const StatsList: FC<StatsListProps> = ({
  gameList,
  handleChevronClick,
}) => {
  const [selectedRow, setSelectedRow] = useState<number>(-1);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);
  const [sortBy, setSortBy] = useState<Options | null>(null);

  const handleRowClick = (index: number) => {
    setSelectedRow(index === selectedRow ? -1 : index);
  };

  const onSort = (option: Options) => {
    handleChevronClick(option);
    setIsFlipped(!isFlipped);
    setSortBy(option);
  };

  return (
    <div className="wrapper">
      <table>
        <thead>
          <tr>
            <th>Gas</th>
            <th>
              <div className="orderable-col">
                <span>Escaped</span>
                <ReactSVG
                  style={{
                    transform:
                      isFlipped && sortBy === Options.Escaped
                        ? "rotate(180deg) translateY(40%)"
                        : "translateY(-50%)",
                    transition: "transform 0.3s",
                  }}
                  onClick={() => onSort(Options.Escaped)}
                  className="chevron"
                  src="/down-chevron.svg"
                />
              </div>
            </th>
            <th>
              <div className="orderable-col">
                <span>Sunk</span>
                <ReactSVG
                  style={{
                    transform:
                      isFlipped && sortBy === Options.Sunk
                        ? "rotate(180deg) translateY(40%)"
                        : "translateY(-50%)",
                    transition: "transform 0.3s",
                  }}
                  onClick={() => onSort(Options.Sunk)}
                  className="chevron"
                  src="/down-chevron.svg"
                />
              </div>
            </th>
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
