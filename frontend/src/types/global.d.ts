export {};

declare global {
    interface Window {
        webkitAudioContext?: typeof AudioContext;
        EssentiaWASM: any;
        Essentia: any;
        EssentiaModel: any;
    }
}
