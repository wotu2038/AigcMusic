import { createContext, useContext, useState } from 'react';

const PlayerContext = createContext();

export function usePlayer() {
    return useContext(PlayerContext);
}

export function PlayerProvider({ children }) {
    const [currentSong, setCurrentSong] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);

    const playSong = (song) => {
        setCurrentSong(song);
        setIsPlaying(true);
    };

    const pauseSong = () => {
        setIsPlaying(false);
    };

    const stopSong = () => {
        setCurrentSong(null);
        setIsPlaying(false);
    };

    return (
        <PlayerContext.Provider value={{
            currentSong,
            isPlaying,
            playSong,
            pauseSong,
            stopSong,
            setCurrentSong,
            setIsPlaying
        }}>
            {children}
        </PlayerContext.Provider>
    );
}

