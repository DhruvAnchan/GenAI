// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey:           import.meta.env.VITE_FIREBASE_apiKey,
  authDomain:       import.meta.env.VITE_FIREBASE_authDomain,
  projectId:        import.meta.env.VITE_FIREBASE_projectId,
  storageBucket:    import.meta.env.VITE_FIREBASE_storageBucket,
  messagingSenderId:import.meta.env.VITE_FIREBASE_messagingSenderId,
  appId:            import.meta.env.VITE_FIREBASE_appId,
  measurementId:    import.meta.env.VITE_FIREBASE_measurementId
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const provider = new GoogleAuthProvider();

export const signInWithGoogle = () => signInWithPopup(auth, provider);
export const logout = () => signOut(auth);