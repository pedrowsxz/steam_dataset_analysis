// src/components/TabBar.jsx
import styles from './TabBar.module.css';

const TABS = [
  { id: 'overview', label: 'Market Overview' },
  { id: 'pricing', label: 'Pricing & Reviews' },
  { id: 'trends', label: 'Temporal Trends' },
  { id: 'bi', label: 'BI Artifact' },
];

export default function TabBar({ active, onChange }) {
  return (
    <nav className={styles.tabs} aria-label="Dashboard sections">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          className={active === tab.id ? `${styles.tab} ${styles.tabActive}` : styles.tab}
          onClick={() => onChange(tab.id)}
          aria-current={active === tab.id ? 'page' : undefined}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
