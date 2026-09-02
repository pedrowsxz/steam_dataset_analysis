// src/components/KpiCard.jsx
import styles from './KpiCard.module.css';

export default function KpiCard({ value, label, note }) {
  return (
    <div className={styles.card}>
      <div className={styles.value}>{value}</div>
      <div className={styles.label}>{label}</div>
      {note && <div className={styles.note}>{note}</div>}
    </div>
  );
}
