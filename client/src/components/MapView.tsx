import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { Alert, getAlertCoordinates, formatAffectedAreas } from '../types';

interface MapViewProps {
  alerts: Alert[];
  onSelectAlert: (alert: Alert) => void;
  selectedAreaName?: string;
  highlightAlertId?: number | null;
  height?: string;
}

export const MapView: React.FC<MapViewProps> = ({ 
  alerts, 
  onSelectAlert, 
  highlightAlertId,
  height = '600px'
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersGroupRef = useRef<L.LayerGroup | null>(null);
  const markersMapRef = useRef<Map<number, L.Marker>>(new Map());

  // Initialize Leaflet map once
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Default center: Hyderabad, India
    const map = L.map(mapContainerRef.current).setView([17.43, 78.41], 12);
    mapInstanceRef.current = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map);

    const markersGroup = L.layerGroup().addTo(map);
    markersGroupRef.current = markersGroup;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update markers when alerts change
  useEffect(() => {
    if (!mapInstanceRef.current || !markersGroupRef.current) return;

    const markersGroup = markersGroupRef.current;
    markersGroup.clearLayers();
    markersMapRef.current.clear();

    const bounds: [number, number][] = [];

    alerts.forEach((alert) => {
      const coords = getAlertCoordinates(alert);
      if (!coords) return;

      const colorMap: Record<string, string> = {
        critical: '#ef4444',
        warning: '#f97316',
        advisory: '#eab308',
        info: '#3b82f6',
      };
      const markerColor = colorMap[alert.severity] || '#3b82f6';
      const isHighlighted = highlightAlertId === alert.id;

      // Custom circular marker with pulse ring
      const markerIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div style="
            position: relative;
            width: ${isHighlighted ? '32px' : '26px'};
            height: ${isHighlighted ? '32px' : '26px'};
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
          ">
            <span style="
              position: absolute;
              width: 100%;
              height: 100%;
              border-radius: 9999px;
              background-color: ${markerColor};
              opacity: ${isHighlighted ? '0.6' : '0.35'};
              animation: ping ${isHighlighted ? '1s' : '2s'} cubic-bezier(0, 0, 0.2, 1) infinite;
            "></span>
            <span style="
              position: relative;
              width: ${isHighlighted ? '18px' : '14px'};
              height: ${isHighlighted ? '18px' : '14px'};
              border-radius: 9999px;
              background-color: ${markerColor};
              border: ${isHighlighted ? '3px solid #ffffff' : '2px solid #ffffff'};
              box-shadow: 0 2px 6px rgba(0,0,0,0.35);
            "></span>
          </div>
        `,
        iconSize: isHighlighted ? [32, 32] : [26, 26],
        iconAnchor: isHighlighted ? [16, 16] : [13, 13],
      });

      const marker = L.marker([coords.lat, coords.lng], { icon: markerIcon });

      const tierBadge = alert.source_tier === 'official' 
        ? '<span style="background:#ecfdf5; color:#047857; font-size:9px; font-weight:700; padding:1px 5px; border-radius:4px; border:1px solid #a7f3d0;">OFFICIAL</span>'
        : alert.source_tier === 'news'
        ? '<span style="background:#eef2ff; color:#4338ca; font-size:9px; font-weight:700; padding:1px 5px; border-radius:4px; border:1px solid #c7d2fe;">NEWS</span>'
        : '<span style="background:#fffbeb; color:#b45309; font-size:9px; font-weight:700; padding:1px 5px; border-radius:4px; border:1px solid #fde68a;">UNVERIFIED</span>';

      // Leaflet Popup
      const popupHtml = `
        <div style="font-family: system-ui, sans-serif; padding: 2px; min-width: 220px; max-width: 280px;">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; gap: 4px;">
            <div style="display: flex; align-items: center; gap: 4px;">
              <span style="
                font-size: 10px; 
                font-weight: 700; 
                text-transform: uppercase; 
                color: ${markerColor};
              ">${alert.severity}</span>
              ${tierBadge}
            </div>
            <span style="font-size: 10px; color: #64748b; text-transform: uppercase; font-weight: 600;">
              ${alert.category.replace('_', ' ')}
            </span>
          </div>
          <h4 style="font-size: 13px; font-weight: 700; margin: 0 0 6px 0; color: #0f172a; line-height: 1.25;">
            ${alert.title}
          </h4>
          <p style="font-size: 11px; color: #475569; margin: 0 0 8px 0; line-height: 1.35;">
            ${alert.expected_impact ? alert.expected_impact.slice(0, 110) + '...' : ''}
          </p>
          <div style="font-size: 10px; color: #64748b; margin-bottom: 8px;">
            <strong>Areas:</strong> ${formatAffectedAreas(alert.affected_areas)}
          </div>
          <button id="alert-btn-${alert.id}" style="
            width: 100%;
            background-color: #2563eb;
            color: white;
            border: none;
            padding: 6px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
          ">
            View Action Checklist →
          </button>
        </div>
      `;

      marker.bindPopup(popupHtml);

      marker.on('popupopen', () => {
        const btn = document.getElementById(`alert-btn-${alert.id}`);
        if (btn) {
          btn.onclick = () => onSelectAlert(alert);
        }
      });

      marker.addTo(markersGroup);
      markersMapRef.current.set(alert.id, marker);
      bounds.push([coords.lat, coords.lng]);
    });

    if (bounds.length > 0 && !highlightAlertId) {
      mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  }, [alerts, onSelectAlert, highlightAlertId]);

  // Pan to highlighted alert
  useEffect(() => {
    if (!highlightAlertId || !mapInstanceRef.current) return;
    const marker = markersMapRef.current.get(highlightAlertId);
    if (marker) {
      const latlng = marker.getLatLng();
      mapInstanceRef.current.setView(latlng, 14, { animate: true });
      marker.openPopup();
    }
  }, [highlightAlertId]);

  return (
    <div 
      style={{ height }}
      className="relative w-full rounded-2xl overflow-hidden shadow-sm border border-slate-200 dark:border-slate-700"
    >
      <div ref={mapContainerRef} className="w-full h-full z-10" />

      {/* Floating Map Legend & Pin Count */}
      <div className="absolute top-4 right-4 z-20 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md p-3 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 text-xs space-y-1.5">
        <div className="flex items-center justify-between gap-3 mb-1">
          <span className="font-bold text-slate-800 dark:text-slate-200 text-[11px] uppercase tracking-wider">
            Live Incident Pins
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 font-bold">
            {alerts.length} Geotagged
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-red-500 shadow-sm" />
          <span className="text-slate-600 dark:text-slate-300 font-medium">Critical</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shadow-sm" />
          <span className="text-slate-600 dark:text-slate-300 font-medium">Warning</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-yellow-500 shadow-sm" />
          <span className="text-slate-600 dark:text-slate-300 font-medium">Advisory</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-sm" />
          <span className="text-slate-600 dark:text-slate-300 font-medium">Info</span>
        </div>
      </div>
    </div>
  );
};
