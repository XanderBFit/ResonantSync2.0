export {};

declare global {
    interface Window {
        EssentiaWASM: any;
        Essentia: any;
        EssentiaModel: any;
        webkitAudioContext?: typeof AudioContext;
    }
}
