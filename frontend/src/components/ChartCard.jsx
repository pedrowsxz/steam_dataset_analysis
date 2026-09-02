// src/components/ChartCard.jsx
//
// Every chart across all four tabs goes through this wrapper, so loading
// skeletons, error/retry handling, and the caveat-note treatment (used
// heavily — 2019 is partial, genres don't sum to 100%, etc.) look and
// behave identically everywhere.
import styles from './ChartCard.module.css';

export default function ChartCard({ title, note, loading, error, onRetry, children }) {
  return (
    <section className={styles.card}>
      <h2 className={styles.title}>{title}</h2>
      <div className={styles.body}>
        {loading && <div className={styles.skeleton} aria-hidden="true" />}
        {!loading && error && (
          <div className={styles.error}>
            <span>Couldn&rsquo;t load this chart. {error}</span>
            {onRetry && (
              <button type="button" className={styles.retry} onClick={onRetry}>
                Retry
              </button>
            )}
          </div>
        )}
        {!loading && !error && children}
      </div>
      {note && <p className={styles.note}>{note}</p>}
    </section>
  );
}
