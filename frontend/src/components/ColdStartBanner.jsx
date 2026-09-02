// src/components/ColdStartBanner.jsx
import styles from './ColdStartBanner.module.css';

export default function ColdStartBanner({ status }) {
  if (status === 'ok' || status === 'checking') return null;

  return (
    <div className={styles.banner} role="status">
      {status === 'slow'
        ? 'Waking up the server — the free-tier API sleeps when idle, so the first load can take up to a minute.'
        : "The API isn't responding yet. Charts below will fill in once it's back — this page keeps retrying automatically."}
    </div>
  );
}
