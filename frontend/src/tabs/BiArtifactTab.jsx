import { useApiData } from '../hooks/useApiData';
import ChartCard from '../components/ChartCard';
import styles from './BiArtifactTab.module.css';

export default function BiArtifactTab() {
  const meta = useApiData('/api/bi-artifact/metadata');

  if (meta.loading) {
    return <div className={styles.skeleton} aria-hidden="true" />;
  }

  if (meta.error) {
    return (
      <div className={styles.error}>
        Couldn&rsquo;t load the BI artifact details.{' '}
        <button type="button" onClick={meta.retry} className={styles.retry}>
          Retry
        </button>
      </div>
    );
  }

  const { dax_measures, data_model_notes, pbix_reference, screenshots, powerbi_embed_url } = meta.data;

  return (
    <div className={styles.tab}>
      <ChartCard title="Power BI screenshots">
        <div className={styles.screenshotGrid}>
          {screenshots.map((filename) => (
            <figure key={filename} className={styles.screenshot}>
              <img
                src={`/screenshots/${filename}`}
                alt={`Power BI dashboard screenshot: ${filename}`}
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling.style.display = 'flex';
                }}
              />
              <figcaption className={styles.screenshotFallback}>
                {filename} — screenshot not found on the server
              </figcaption>
            </figure>
          ))}
        </div>
      </ChartCard>

      <ChartCard title="Data model">
        <p className={styles.notes}>{data_model_notes}</p>
        <div className={styles.pbixRef}>
           <a 
              href="https://github.com/pedrowsxz/steam_dataset_analysis/tree/main/powerbi" 
              target="_blank" 
              rel="noopener noreferrer"
              className={styles.pbixFilename}
            >
              {pbix_reference.filename}
            </a>
          <span className={styles.pbixNote}>{pbix_reference.note}</span>
        </div>
      </ChartCard>

      <ChartCard title="DAX measures">
        <dl className={styles.measures}>
          {dax_measures.map((m) => (
            <div key={m.name} className={styles.measure}>
              <dt className={styles.measureName}>{m.name}</dt>
              <dd className={styles.measureExpression}>{m.expression}</dd>
              <dd className={styles.measureDescription}>{m.description}</dd>
            </div>
          ))}
        </dl>
      </ChartCard>

      {powerbi_embed_url ? (
        <ChartCard title="Live Power BI report">
          <iframe title="Power BI report" src={powerbi_embed_url} className={styles.embed} allowFullScreen />
        </ChartCard>
      ) : (
        <ChartCard title="Live Power BI report">
          <p className={styles.notes}>
            No live embed is configured for this deployment. Set POWERBI_EMBED_URL on the API to show one here —
            everything above works without it.
          </p>
        </ChartCard>
      )}
    </div>
  );
}
