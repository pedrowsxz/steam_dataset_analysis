import { useApiData } from '../hooks/useApiData';
import ChartCard from '../components/ChartCard';
import {
  ComposedChart,
  Bar,
  Cell,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  BarChart,
} from 'recharts';
import styles from './TrendsTab.module.css';

export default function TrendsTab() {
  const releases = useApiData('/api/trends/releases');
  const platforms = useApiData('/api/trends/platforms');
  const publishers = useApiData('/api/trends/publishers?limit=10');

  const releasesNote = releases.data
    ? `Years before ${releases.data.notes.trimmed_years_before} are trimmed (fewer than 50 releases, too noisy to trend). ${releases.data.notes.partial_year_reason} ${releases.data.notes.partial_year}'s bar is outlined, not filled, and shows no year-over-year figure for that reason.`
    : undefined;

  return (
    <div className={styles.tab}>
      <ChartCard title="Releases per year" note={releasesNote} loading={releases.loading} error={releases.error} onRetry={releases.retry}>
        {releases.data && (
          <ResponsiveContainer width="100%" height={340}>
            <ComposedChart data={releases.data.years} margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="year" stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis yAxisId="releases" stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis yAxisId="yoy" orientation="right" tickFormatter={(v) => `${v}%`} stroke="var(--color-text-muted)" fontSize={12} />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'YoY growth') {
                    return value === null ? ['— (partial year)', name] : [`${value}%`, name];
                  }
                  return [value.toLocaleString(), name];
                }}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Legend />
              <Bar yAxisId="releases" dataKey="releases" name="releases" radius={[4, 4, 0, 0]}>
                {releases.data.years.map((entry) => {
                  const isPartial = entry.year === releases.data.notes.partial_year;
                  return (
                    <Cell
                      key={entry.year}
                      fill={isPartial ? 'transparent' : 'var(--color-accent)'}
                      stroke="var(--color-accent)"
                      strokeDasharray={isPartial ? '4 3' : undefined}
                    />
                  );
                })}
              </Bar>
              <Line
                yAxisId="yoy"
                type="monotone"
                dataKey="yoy_pct"
                name="YoY growth"
                stroke="var(--color-accent-2)"
                strokeWidth={2}
                dot
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard
        title="Platform availability by release year"
        note={platforms.data?.note}
        loading={platforms.loading}
        error={platforms.error}
        onRetry={platforms.retry}
      >
        {platforms.data && (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={platforms.data.years} margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis dataKey="year" stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis tickFormatter={(v) => `${v}%`} domain={[0, 100]} stroke="var(--color-text-muted)" fontSize={12} />
              <Tooltip
                formatter={(value) => `${value}%`}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Legend />
              <Line type="monotone" dataKey="pct_windows" name="Windows" stroke="var(--color-text-muted)" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="pct_mac" name="Mac" stroke="var(--color-accent)" strokeWidth={2.5} dot={false} />
              <Line type="monotone" dataKey="pct_linux" name="Linux" stroke="var(--color-accent-2)" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard
        title="Top 10 publishers by game count"
        note={publishers.data?.note}
        loading={publishers.loading}
        error={publishers.error}
        onRetry={publishers.retry}
      >
        {publishers.data && (
          <ResponsiveContainer width="100%" height={340}>
            <BarChart data={publishers.data.publishers} layout="vertical" margin={{ left: 24, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis dataKey="publisher" type="category" width={140} stroke="var(--color-text-muted)" fontSize={12} />
              <Tooltip
                formatter={(value, _name, item) => [`${value} games (${item.payload.pct_of_games}% of all titles)`, item.payload.publisher]}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Bar dataKey="game_count" fill="var(--color-accent)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}
