import { useEffect, useRef } from "react";
import type { MutableRefObject } from "react";

type LatLng = { lat: number; lon: number };

interface RoutePlannerMapProps {
  origin: LatLng | null;
  destination: LatLng | null;
  onRouteReady(distanceKm: number | null): void;
  className?: string;
}

declare global {
  interface Window {
    ymaps?: any;
  }
}

const DEFAULT_CENTER: [number, number] = [55.751244, 37.618423];
const YANDEX_API_KEY = import.meta.env.VITE_YANDEX_MAP_API_KEY;

let yandexMapsPromise: Promise<any> | null = null;

function loadYandexMaps(): Promise<any> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Yandex Maps API is only available in the browser."));
  }

  if (window.ymaps) {
    return new Promise((resolve) => {
      window.ymaps.ready(() => resolve(window.ymaps));
    });
  }

  if (!yandexMapsPromise) {
    if (!YANDEX_API_KEY) {
      return Promise.reject(new Error("Yandex Maps API key is not configured."));
    }

    yandexMapsPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = `https://api-maps.yandex.ru/2.1/?apikey=${YANDEX_API_KEY}&lang=ru_RU&load=package.full`;
      script.async = true;
      script.onload = () => {
        if (!window.ymaps) {
          reject(new Error("Yandex Maps API loaded but global object is unavailable."));
          return;
        }
        window.ymaps.ready(() => resolve(window.ymaps));
      };
      script.onerror = () => {
        yandexMapsPromise = null;
        reject(new Error("Failed to load Yandex Maps API script."));
      };
      document.head.appendChild(script);
    });
  }

  return yandexMapsPromise;
}

export default function RoutePlannerMap({
  origin,
  destination,
  onRouteReady,
  className,
}: RoutePlannerMapProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<any>(null);
  const ymapsRef = useRef<any>(null);
  const originPlacemarkRef = useRef<any>(null);
  const destinationPlacemarkRef = useRef<any>(null);
  const multiRouteRef = useRef<any>(null);
  const routeEventCleanupRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    let cancelled = false;

    loadYandexMaps()
      .then((ymapsInstance) => {
        if (cancelled || !containerRef.current) {
          return;
        }
        ymapsRef.current = ymapsInstance;
        mapRef.current = new ymapsInstance.Map(
          containerRef.current,
          {
            center: DEFAULT_CENTER,
            zoom: 11,
            controls: ["zoomControl", "fullscreenControl"],
          },
          {
            suppressObsoleteBrowserNotifier: true,
          },
        );
      })
      .catch((error) => {
        console.error("Failed to initialise Yandex Map", error);
      });

    return () => {
      cancelled = true;
      const map = mapRef.current;
      if (routeEventCleanupRef.current) {
        routeEventCleanupRef.current();
        routeEventCleanupRef.current = null;
      }
      if (multiRouteRef.current && map) {
        map.geoObjects.remove(multiRouteRef.current);
        multiRouteRef.current = null;
      }
      if (originPlacemarkRef.current && map) {
        map.geoObjects.remove(originPlacemarkRef.current);
        originPlacemarkRef.current = null;
      }
      if (destinationPlacemarkRef.current && map) {
        map.geoObjects.remove(destinationPlacemarkRef.current);
        destinationPlacemarkRef.current = null;
      }
      if (map) {
        map.destroy();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const ymaps = ymapsRef.current;
    if (!map || !ymaps) {
      return;
    }

    const removePlacemark = (ref: MutableRefObject<any>) => {
      if (ref.current) {
        map.geoObjects.remove(ref.current);
        ref.current = null;
      }
    };

    const ensurePlacemark = (ref: MutableRefObject<any>, point: LatLng, color: string) => {
      const coordinates: [number, number] = [point.lat, point.lon];
      if (!ref.current) {
        ref.current = new ymaps.Placemark(
          coordinates,
          {},
          {
            preset: "islands#circleDotIcon",
            iconColor: color,
          },
        );
        map.geoObjects.add(ref.current);
      } else {
        ref.current.geometry?.setCoordinates(coordinates);
      }
    };

    const removeRoute = () => {
      if (routeEventCleanupRef.current) {
        routeEventCleanupRef.current();
        routeEventCleanupRef.current = null;
      }
      if (multiRouteRef.current) {
        map.geoObjects.remove(multiRouteRef.current);
        multiRouteRef.current = null;
      }
    };

    removeRoute();

    if (!origin && !destination) {
      removePlacemark(originPlacemarkRef);
      removePlacemark(destinationPlacemarkRef);
      map.setCenter(DEFAULT_CENTER, 11);
      onRouteReady(null);
      return () => removeRoute();
    }

    if (origin && !destination) {
      ensurePlacemark(originPlacemarkRef, origin, "#2563eb");
      removePlacemark(destinationPlacemarkRef);
      map.setCenter([origin.lat, origin.lon], Math.max(map.getZoom(), 13));
      onRouteReady(null);
      return () => removeRoute();
    }

    if (!origin && destination) {
      ensurePlacemark(destinationPlacemarkRef, destination, "#ef4444");
      removePlacemark(originPlacemarkRef);
      map.setCenter([destination.lat, destination.lon], Math.max(map.getZoom(), 13));
      onRouteReady(null);
      return () => removeRoute();
    }

    removePlacemark(originPlacemarkRef);
    removePlacemark(destinationPlacemarkRef);

    const originPoint = origin as LatLng;
    const destinationPoint = destination as LatLng;

    const multiRoute = new ymaps.multiRouter.MultiRoute(
      {
        referencePoints: [
          [originPoint.lat, originPoint.lon],
          [destinationPoint.lat, destinationPoint.lon],
        ],
        params: {
          routingMode: "auto",
        },
      },
      {
        boundsAutoApply: true,
        routeActiveStrokeColor: "#2563eb",
        routeStrokeColor: "#60a5fa",
        routeStrokeWidth: 4,
      },
    );

    const notifyDistance = () => {
      const activeRoute = multiRoute.getActiveRoute();
      if (!activeRoute) {
        onRouteReady(null);
        return;
      }
      const distance = activeRoute.properties.get("distance");
      if (!distance || typeof distance.value !== "number") {
        onRouteReady(null);
        return;
      }
      const distanceKm = distance.value / 1000;
      onRouteReady(Number.isFinite(distanceKm) ? Number(distanceKm.toFixed(2)) : null);
    };

    const handleSuccess = () => {
      notifyDistance();
    };

    const handleFail = () => {
      onRouteReady(null);
    };

    multiRoute.model.events.add("requestsuccess", handleSuccess);
    multiRoute.model.events.add("requestfail", handleFail);

    routeEventCleanupRef.current = () => {
      multiRoute.model.events.remove("requestsuccess", handleSuccess);
      multiRoute.model.events.remove("requestfail", handleFail);
    };

    multiRouteRef.current = multiRoute;
    map.geoObjects.add(multiRoute);
    notifyDistance();

    return () => {
      removeRoute();
    };
  }, [origin, destination, onRouteReady]);

  return <div ref={containerRef} className={className} />;
}
