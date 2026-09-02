import { useApiData } from '../hooks/useApiData';
import KpiCard from '../components/KpiCard';
import ChartCard from '../components/ChartCard';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import styles from './OverviewTab.module.css';

const formatUsd = (value) => `$${value.toFixed(2)}`;
const formatPct = (value) => `${value}%`;

export default function OverviewTab() {
  const summary = useApiData('/api/overview/summary');
  const genres = useApiData('/api/overview/genres?limit=15');

  return (
    <div className={styles.tab}>
      <div className={styles.kpiRow}>
        {summary.loading && (
          <>
            <div className={styles.kpiSkeleton} aria-hidden="true" />
            <div className={styles.kpiSkeleton} aria-hidden="true" />
          </>
        )}
        {!summary.loading && summary.error && (
          <div className={styles.kpiError}>
            Couldn&rsquo;t load the summary numbers.{' '}
            <button type="button" onClick={summary.retry} className={styles.kpiRetry}>
              Retry
            </button>
          </div>
        )}
        {!summary.loading && !summary.error && summary.data && (
          <>
            <KpiCard value={summary.data.total_games.toLocaleString()} label="total games" />
            <KpiCard value={formatUsd(summary.data.avg_paid_price_usd)} label="average price, paid titles" />
          </>
        )}
      </div>

      <ChartCard
        title="Top 15 genres"
        note={genres.data?.note}
        loading={genres.loading}
        error={genres.error}
        onRetry={genres.retry}
      >
        {genres.data && (
          <ResponsiveContainer width="100%" height={420}>
            <BarChart data={genres.data.genres} layout="vertical" margin={{ left: 24, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" tickFormatter={formatPct} stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis dataKey="genre" type="category" width={110} stroke="var(--color-text-muted)" fontSize={12} />
              <Tooltip
                formatter={(value) => [`${value.toFixed(2)}%`, 'of all games']}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Bar dataKey="pct_of_games" fill="var(--color-accent)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}
