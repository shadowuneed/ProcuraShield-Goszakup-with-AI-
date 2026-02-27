'use client';

import dynamic from 'next/dynamic';

// Динамический импорт Leaflet (SSR не поддерживается)
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
);
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
);
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
);
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
);

interface RiskMapProps {
  data?: Array<{
    region: string;
    lat: number;
    lng: number;
    count: number;
    high_risk: number;
  }>;
}

// Данные регионов Казахстана по умолчанию
const defaultRegions = [
  { region: 'Астана', lat: 51.16, lng: 71.43, count: 234, high_risk: 12 },
  { region: 'Алматы', lat: 43.24, lng: 76.95, count: 456, high_risk: 23 },
  { region: 'Шымкент', lat: 42.32, lng: 69.60, count: 178, high_risk: 8 },
  { region: 'Караганда', lat: 49.80, lng: 73.10, count: 145, high_risk: 15 },
  { region: 'Актобе', lat: 50.28, lng: 57.21, count: 98, high_risk: 5 },
  { region: 'Атырау', lat: 47.10, lng: 51.92, count: 167, high_risk: 18 },
  { region: 'Туркестан', lat: 43.30, lng: 68.25, count: 134, high_risk: 7 },
  { region: 'Павлодар', lat: 52.28, lng: 76.95, count: 89, high_risk: 4 },
  { region: 'Костанай', lat: 53.21, lng: 63.63, count: 76, high_risk: 3 },
  { region: 'Мангистау', lat: 43.35, lng: 52.06, count: 112, high_risk: 11 },
];

function getRiskColor(highRisk: number, total: number): string {
  const ratio = total > 0 ? highRisk / total : 0;
  if (ratio > 0.15) return '#ef4444';
  if (ratio > 0.1) return '#f97316';
  if (ratio > 0.05) return '#eab308';
  return '#22c55e';
}

export function RiskMap({ data }: RiskMapProps) {
  const regions = data || defaultRegions;

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
        Карта рисков по регионам
      </h3>
      <div className="rounded-lg overflow-hidden" style={{ height: 400 }}>
        <MapContainer
          center={[48.0, 67.0]}
          zoom={5}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://osm.org">OSM</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {regions.map((region, idx) => (
            <CircleMarker
              key={idx}
              center={[region.lat, region.lng]}
              radius={Math.max(8, Math.sqrt(region.count) * 2)}
              fillColor={getRiskColor(region.high_risk, region.count)}
              fillOpacity={0.7}
              stroke={true}
              color="#1e293b"
              weight={1}
            >
              <Popup>
                <div className="text-sm">
                  <strong>{region.region}</strong>
                  <br />
                  Закупок: {region.count}
                  <br />
                  Высокий риск: {region.high_risk}
                  <br />
                  Доля риска: {((region.high_risk / region.count) * 100).toFixed(1)}%
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
