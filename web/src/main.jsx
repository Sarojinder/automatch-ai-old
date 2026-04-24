import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_URL = '/api/recommend';
const COMMONS_API = 'https://commons.wikimedia.org/w/api.php';

const QUICK_PROMPTS = [
  'american muscle under 45k',
  'tuner car under 30k',
  'JDM manual fun car near Toronto',
  'winter daily under 25k AWD reliable',
  'family hauler with good safety features',
  'luxury cruiser with good speakers',
  'fast but easy to maintain under 50k',
  'old BMW under 25k'
];

const BODY_IMAGES = {
  suv: '/assets/vehicle-suv.svg',
  sedan: '/assets/vehicle-sedan.svg',
  hatchback: '/assets/vehicle-hatchback.svg',
  coupe: '/assets/vehicle-coupe.svg',
  convertible: '/assets/vehicle-coupe.svg',
  roadster: '/assets/vehicle-coupe.svg',
  truck: '/assets/vehicle-suv.svg',
  van: '/assets/vehicle-suv.svg',
  wagon: '/assets/vehicle-hatchback.svg'
};

const imageCache = new Map();

function App() {
  const [query, setQuery] = useState('american muscle under 45k');
  const [limit, setLimit] = useState(5);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function search(nextQuery = query) {
    const cleanQuery = nextQuery.trim();
    if (!cleanQuery) {
      setError('Tell AutoMatch what kind of car you want.');
      return;
    }

    setQuery(cleanQuery);
    setLoading(true);
    setError('');
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: cleanQuery, limit })
      });
      if (!response.ok) {
        throw new Error(`Request failed with ${response.status}`);
      }
      setResult(await response.json());
    } catch (err) {
      setError('Could not reach AutoMatch. Start the Python server and try again.');
    } finally {
      setLoading(false);
    }
  }

  const recommendations = result?.recommendations ?? [];
  const interpreted = result?.interpreted_preferences;
  const modelAvailable = result?.model?.available;
  const dataSource = result?.data_source?.type;

  return (
    <main>
      <section className="search-panel">
        <div className="brand-row">
          <div>
            <p className="eyebrow">AutoMatch AI</p>
            <h1>Tell it the vibe. Get cars that fit.</h1>
          </div>
          <div className={modelAvailable ? 'model-pill online' : 'model-pill'}>
            {dataSource === 'hybrid_marketplace'
              ? 'Hybrid market data'
              : dataSource === 'kaggle_toronto_used_vehicles' || dataSource === 'imported_real_listings'
                ? 'Market data'
                : modelAvailable
                  ? 'ML ranker'
                  : 'Rules mode'}
          </div>
        </div>

        <div className="search-grid">
          <div className="query-box">
            <label htmlFor="query">What are you looking for?</label>
            <textarea
              id="query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
                  search();
                }
              }}
            />
            <div className="controls">
              <label>
                Results
                <select value={limit} onChange={(event) => setLimit(Number(event.target.value))}>
                  {[3, 5, 8, 10].map((value) => (
                    <option key={value} value={value}>
                      {value}
                    </option>
                  ))}
                </select>
              </label>
              <button type="button" onClick={() => search()} disabled={loading}>
                {loading ? 'Searching' : 'Find Matches'}
              </button>
            </div>
          </div>

          <div className="proof-panel">
            <Metric label="Inventory" value={result?.data_source?.type === 'hybrid_marketplace' ? '19.6k' : 'Ready'} />
            <Metric label="Ranker" value={modelAvailable ? 'Active' : 'Rules'} />
            <Metric label="Signals" value="38" />
            <p>
              Budget, mileage, location, seats, doors, body style, fuel, drivetrain, engine, history, features,
              ownership cost, reliability, comfort, winter use, and car-culture intent.
            </p>
          </div>
        </div>

        <div className="quick-prompts">
          {QUICK_PROMPTS.map((prompt) => (
            <button key={prompt} type="button" onClick={() => search(prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="error">{error}</p>}

      {result && (
        <section className="results-shell">
          <div className="summary-row">
            <div>
              <p className="eyebrow">Recommendation</p>
              <h2>{result.summary}</h2>
            </div>
            <PreferenceSummary interpreted={interpreted} />
          </div>

          {recommendations.length === 0 ? (
            <p className="empty-state">No clean matches. Try a wider budget, fewer hard filters, or a nearby city.</p>
          ) : (
            <div className="cards">
              {recommendations.map((recommendation, index) => (
                <VehicleCard key={recommendation.vehicle.id} recommendation={recommendation} rank={index + 1} />
              ))}
            </div>
          )}

          {result.follow_up_questions?.length > 0 && (
            <div className="follow-ups">
              <p className="eyebrow">Good next questions</p>
              {result.follow_up_questions.map((question) => (
                <span key={question}>{question}</span>
              ))}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PreferenceSummary({ interpreted }) {
  const rows = useMemo(() => {
    if (!interpreted) return [];
    return [
      ['Budget', budgetRange(interpreted)],
      ['Location', interpreted.location ?? 'Any'],
      ['Year', yearRange(interpreted)],
      ['Mileage', interpreted.max_mileage_km ? `${number(interpreted.max_mileage_km)} km max` : 'Any'],
      ['Body', interpreted.body_styles?.join(', ') || 'Any'],
      ['Avoids', interpreted.excluded_body_styles?.join(', ') || 'None'],
      ['Fuel', interpreted.fuel_types?.join(', ') || 'Any'],
      ['Engine', interpreted.engine_cylinders?.length ? interpreted.engine_cylinders.map((value) => `${value}-cyl`).join(', ') : 'Any'],
      ['Features', interpreted.required_features?.length ? interpreted.required_features.join(', ') : 'Any'],
      ['Intent', interpreted.archetypes?.length ? interpreted.archetypes.map(labelize).join(', ') : 'General fit']
    ];
  }, [interpreted]);

  return (
    <div className="preference-grid">
      {rows.map(([label, value]) => (
        <div key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function VehicleCard({ recommendation, rank }) {
  const vehicle = recommendation.vehicle;
  const score = Math.min(100, Math.round(recommendation.score));
  const mlScore = recommendation.ml_score ? Math.round(recommendation.ml_score) : null;
  const hasListingLink = vehicle.source_url?.startsWith('http');

  return (
    <article className="vehicle-card">
      <VehicleImage vehicle={vehicle} />
      <div className="card-body">
        <div className="card-top">
          <span className="rank">#{rank}</span>
          <span className="score">{score} match</span>
        </div>
        <h3>{vehicle.display_name}</h3>
        <p className="notes">{vehicle.notes}</p>

        <div className="spec-grid">
          <Spec label="Price" value={money(vehicle.price_cad)} />
          <Spec label="Monthly" value={money(recommendation.finance.monthly_payment)} />
          <Spec label="Mileage" value={`${number(vehicle.mileage_km)} km`} />
          <Spec label="Location" value={vehicle.location} />
          <Spec label="Power" value={`${vehicle.horsepower} hp`} />
          <Spec label="Engine" value={vehicle.engine || (vehicle.cylinders ? `${vehicle.cylinders}-cyl` : 'Unknown')} />
          <Spec label="Fuel" value={`${vehicle.fuel_type} - ${vehicle.l_per_100km} L/100km`} />
          <Spec label="Seats" value={`${vehicle.seats}`} />
        </div>

        <div className="tag-row">
          {vehicle.cpo && <span>CPO</span>}
          <span>{vehicle.drivetrain}</span>
          <span>{vehicle.listing_type}</span>
          <span>{sourceLabel(vehicle.listing_source)}</span>
          {mlScore && <span>ML {mlScore}/100</span>}
          {hasListingLink && (
            <a href={vehicle.source_url} target="_blank" rel="noreferrer">
              Open listing
            </a>
          )}
        </div>

        <ReasonList title="Why it fits" items={recommendation.reasons} />
        {recommendation.cautions.length > 0 && <ReasonList title="Watch-outs" items={recommendation.cautions} caution />}
      </div>
    </article>
  );
}

function VehicleImage({ vehicle }) {
  const fallback = BODY_IMAGES[vehicle.body_style] ?? BODY_IMAGES.sedan;
  const [image, setImage] = useState({ status: 'loading', url: fallback, source: '' });

  useEffect(() => {
    let ignore = false;
    const key = `${vehicle.make}-${vehicle.model}`.toLowerCase();
    const cached = imageCache.get(key);
    if (cached) {
      setImage(cached);
      return () => {
        ignore = true;
      };
    }

    setImage({ status: 'loading', url: fallback, source: '' });
    fetchCommonsImage(vehicle)
      .then((nextImage) => {
        if (ignore) return;
        const finalImage = nextImage ?? { status: 'fallback', url: fallback, source: '' };
        imageCache.set(key, finalImage);
        setImage(finalImage);
      })
      .catch(() => {
        if (ignore) return;
        setImage({ status: 'fallback', url: fallback, source: '' });
      });

    return () => {
      ignore = true;
    };
  }, [vehicle.make, vehicle.model, fallback]);

  return (
    <figure className="vehicle-media">
      <img
        className={image.status === 'loaded' ? 'vehicle-photo loaded' : 'vehicle-photo'}
        src={image.url}
        alt={`${vehicle.year} ${vehicle.make} ${vehicle.model}`}
      />
      <figcaption>
        {image.source ? (
          <a href={image.source} target="_blank" rel="noreferrer">
            Wikimedia Commons
          </a>
        ) : (
          `${vehicle.body_style || 'vehicle'} view`
        )}
      </figcaption>
    </figure>
  );
}

async function fetchCommonsImage(vehicle) {
  const search = `${vehicle.year} ${vehicle.make} ${vehicle.model} automobile`;
  const params = new URLSearchParams({
    action: 'query',
    format: 'json',
    origin: '*',
    generator: 'search',
    gsrnamespace: '6',
    gsrlimit: '4',
    gsrsearch: search,
    prop: 'imageinfo',
    iiprop: 'url|mime',
    iiurlwidth: '900'
  });
  const response = await fetch(`${COMMONS_API}?${params.toString()}`);
  if (!response.ok) return null;
  const data = await response.json();
  const pages = Object.values(data?.query?.pages ?? {});
  const page = pages.find((candidate) => {
    const info = candidate.imageinfo?.[0];
    return info?.thumburl && /^image\/(jpeg|png|webp)$/i.test(info.mime || '');
  });
  const info = page?.imageinfo?.[0];
  if (!info?.thumburl) return null;
  return {
    status: 'loaded',
    url: info.thumburl,
    source: info.descriptionurl || ''
  };
}

function Spec({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ReasonList({ title, items, caution = false }) {
  return (
    <div className={caution ? 'reason-list caution' : 'reason-list'}>
      <p>{title}</p>
      {items.map((item) => (
        <span key={item}>{item}</span>
      ))}
    </div>
  );
}

function money(value) {
  if (value === null || value === undefined) return 'Any';
  return new Intl.NumberFormat('en-CA', {
    style: 'currency',
    currency: 'CAD',
    maximumFractionDigits: 0
  }).format(value);
}

function number(value) {
  return new Intl.NumberFormat('en-CA').format(value);
}

function sourceLabel(source) {
  if (source === 'rebrowser_autotrader') return 'Sample listing';
  if (source === 'kaggle_toronto_used_vehicles') return 'Kaggle Toronto';
  if (source === 'manual_curated') return 'Curated seed';
  if (source === 'simulated_live') return 'Fresh simulation';
  return 'Demo data';
}

function budgetRange(interpreted) {
  if (interpreted.budget_min && interpreted.budget_max) {
    return `${money(interpreted.budget_min)} - ${money(interpreted.budget_max)}`;
  }
  if (interpreted.budget_min) return `${money(interpreted.budget_min)}+`;
  if (interpreted.budget_max) return `Up to ${money(interpreted.budget_max)}`;
  return 'Any';
}

function yearRange(interpreted) {
  if (interpreted.year_min && interpreted.year_max) return `${interpreted.year_min}-${interpreted.year_max}`;
  if (interpreted.year_min) return `${interpreted.year_min}+`;
  if (interpreted.year_max) return `Up to ${interpreted.year_max}`;
  return 'Any';
}

function labelize(value) {
  return value.replaceAll('_', ' ');
}

createRoot(document.getElementById('root')).render(<App />);
