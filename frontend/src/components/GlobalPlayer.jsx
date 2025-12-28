import { usePlayer } from '../contexts/PlayerContext';
import Player from './Player';
import './GlobalPlayer.css';

function GlobalPlayer() {
    const { currentSong } = usePlayer();

    if (!currentSong) {
        return null;
    }

    return (
        <div className="global-player-container">
            <Player song={currentSong} />
        </div>
    );
}

export default GlobalPlayer;

