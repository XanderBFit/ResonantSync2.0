export interface AnalyzedData {
    title: string;
    artist: string;
    album: string;
    bpm: number;
    key: string;
    mood: string;
    genre: string;
    energy: string | number;
    valence: number;
    danceability: number;
    instruments: string[];
    vocalPresence: string;
    scale: string;
    lufs?: number;      // Server-measured integrated loudness (ITU-R BS.1770)
    fileId?: string;
    audioBuffer?: AudioBuffer;
}

export interface TrackMetadata {
    title?: string;
    artist?: string;
    album?: string;
    bpm?: string | number;
    key?: string;
    mood?: string;
    genre?: string;
    instruments?: string;
    vocalPresence?: string;
    isrc?: string;
    publisher?: string;
    composer?: string;
    contactName?: string;
    contactEmail?: string;
    oneStop?: boolean;
    scale?: string;
    energy?: string | number;
    valence?: number;
    danceability?: number;
    lufs?: number;
    comments?: string;
    contactPhone?: string;
    grouping?: string;
}
