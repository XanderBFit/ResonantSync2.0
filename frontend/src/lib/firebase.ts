import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: "AIzaSyAD0mYw09sVfvfmX14nRh1HOVmzgOO9OwM",
    authDomain: "striking-scout-489504-b4.firebaseapp.com",
    projectId: "striking-scout-489504-b4",
    storageBucket: "striking-scout-489504-b4.firebasestorage.app",
    messagingSenderId: "1032872848680",
    appId: "1:1032872848680:web:14340a9edb7638b33d741d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize standard services
export const auth = getAuth(app);
export const db = getFirestore(app);
