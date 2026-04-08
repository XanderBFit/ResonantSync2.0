export interface TrackMetadata {
    title: string;
    artist: string;
    album?: string;
    bpm: string | number;
    key: string;
    scale: string;
    mood: string;
    genre?: string;
    instruments?: string | string[];
    vocalPresence?: string;
    publisher?: string;
    composer?: string;
    contactName?: string;
    contactEmail?: string;
    oneStop?: boolean;
    isrc?: string;
    energy?: string | number;
    valence?: number;
    danceability?: number;
    lufs?: number;
}
