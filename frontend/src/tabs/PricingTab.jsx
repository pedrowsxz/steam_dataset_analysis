import { useApiData } from '../hooks/useApiData';
import ChartCard from '../components/ChartCard';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
} from 'recharts';
import styles from './PricingTab.module.css';

// Index-matched to the [Free, Paid] order donutData is built in below.
const DONUT_COLORS = ['var(--color-text-muted)', 'var(--color-accent)'];

export default function PricingTab() {
  const tiers = useApiData('/api/pricing/tiers');
  const freeVsPaid = useApiData('/api/pricing/free-vs-paid');
  const scatter = useApiData('/api/pricing/scatter?limit=1500');

  const donutData = freeVsPaid.data
    ? [
        { name: 'Free', value: freeVsPaid.data.free.game_count, pct: freeVsPaid.data.free.pct },
        { name: 'Paid', value: freeVsPaid.data.paid.game_count, pct: freeVsPaid.data.paid.pct },
      ]
    : [];

  const scatterNote = scatter.data
    ? `Pearson r = ${scatter.data.correlation.pearson_r}. ${scatter.data.correlation.note} Showing ${scatter.data.sampling.sample_size.toLocaleString()} of ${scatter.data.sampling.eligible_rows.toLocaleString()} priced, reviewed games (stratified sample).`
    : undefined;

  return (
    <div className={styles.tab}>
      <ChartCard title="Games by price tier" loading={tiers.loading} error={tiers.error} onRetry={tiers.retry}>
        {tiers.data && (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={tiers.data.tiers} layout="vertical" margin={{ left: 24, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `${v}%`} stroke="var(--color-text-muted)" fontSize={12} />
              <YAxis dataKey="tier" type="category" width={170} stroke="var(--color-text-muted)" fontSize={12} />
              <Tooltip
                formatter={(_value, _name, item) => [`${item.payload.game_count.toLocaleString()} games`, item.payload.tier]}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Bar dataKey="pct_of_games" fill="var(--color-accent)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Free vs. paid" loading={freeVsPaid.loading} error={freeVsPaid.error} onRetry={freeVsPaid.retry}>
        {freeVsPaid.data && (
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={donutData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={100} paddingAngle={2}>
                {donutData.map((entry, index) => (
                  <Cell key={entry.name} fill={DONUT_COLORS[index]} stroke="var(--color-bg)" />
                ))}
              </Pie>
              <Legend
                formatter={(value) => {
                  const entry = donutData.find((d) => d.name === value);
                  return `${value} — ${entry ? entry.pct.toFixed(1) : ''}%`;
                }}
              />
              <Tooltip
                formatter={(value, name) => [`${value.toLocaleString()} games`, name]}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard
        title="Price vs. review score"
        note={scatterNote}
        loading={scatter.loading}
        error={scatter.error}
        onRetry={scatter.retry}
      >
        {scatter.data && (
          <ResponsiveContainer width="100%" height={360}>
            <ScatterChart margin={{ left: 12, right: 24, bottom: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                dataKey="price"
                type="number"
                name="Price"
                tickFormatter={(v) => `$${v}`}
                stroke="var(--color-text-muted)"
                fontSize={12}
              />
              <YAxis
                dataKey="positive_review_rate"
                type="number"
                name="Positive review rate"
                domain={[0, 1]}
                tickFormatter={(v) => `${Math.round(v * 100)}%`}
                stroke="var(--color-text-muted)"
                fontSize={12}
              />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                formatter={(value, name) =>
                  // `name` here is the axis `name` prop above ("Price" / "Positive review rate"),
                  // not the raw dataKey — match against those, not the snake_case field names.
                  name === 'Positive review rate' ? [`${Math.round(value * 100)}%`, name] : [`$${Number(value).toFixed(2)}`, name]
                }
                labelFormatter={() => ''}
                contentStyle={{ background: 'var(--color-surface-raised)', border: '1px solid var(--color-border)' }}
              />
              <Scatter data={scatter.data.points} fill="var(--color-accent)" fillOpacity={0.45} />
            </ScatterChart>
          </ResponsiveContainer>
        )}
      </ChartCard>
    </div>
  );
}
