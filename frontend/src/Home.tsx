import { useCallback, useEffect, useMemo, useState } from "react";
import type { FormEvent, KeyboardEvent } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { createApiError, parseResponse } from "./api";
import RoutePlannerMap from "./components/RoutePlannerMap";

export interface VehicleType {
  id: number;
  name: string;
  description: string;
  max_weight: string;
  base_price: string;
  per_km_rate: string;
}

interface CoordPoint {
  lat: number;
  lon: number;
  label: string;
}

interface PriceQuote {
  price: string;
  currency: string;
  breakdown: Record<string, unknown>;
}

interface WeatherInfo {
  provider?: string | null;
  condition?: string | null;
  temperature?: number | null;
  feels_like?: number | null;
  wind_speed?: number | null;
  pressure_mm?: number | null;
}

const COORDINATE_REGEX = /^(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)$/;
const DEFAULT_COUNTRY = "Russia";
const YANDEX_API_KEY = import.meta.env.VITE_YANDEX_MAP_API_KEY;

function ensureYandexApiKey(): string {
  if (!YANDEX_API_KEY) {
    throw new Error("Yandex Maps API key is not configured.");
  }
  return YANDEX_API_KEY;
}

async function geocode(query: string): Promise<CoordPoint> {
  const trimmed = query.trim();
  const coordinateMatch = trimmed.match(COORDINATE_REGEX);
  if (coordinateMatch) {
    const lat = Number(coordinateMatch[1]);
    const lon = Number(coordinateMatch[2]);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      return { lat, lon, label: `${lat.toFixed(5)}, ${lon.toFixed(5)}` };
    }
  }

  const queryWithCountry = trimmed.toLowerCase().includes(DEFAULT_COUNTRY.toLowerCase())
    ? trimmed
    : `${trimmed}, ${DEFAULT_COUNTRY}`;

  const apiKey = ensureYandexApiKey();
  const url = new URL("https://geocode-maps.yandex.ru/1.x/");
  url.searchParams.set("apikey", apiKey);
  url.searchParams.set("geocode", queryWithCountry);
  url.searchParams.set("format", "json");
  url.searchParams.set("lang", "ru_RU");
  url.searchParams.set("results", "1");

  const response = await fetch(url.toString());
  if (!response.ok) {
    throw new Error("Failed to contact Yandex geocoder.");
  }

  const payload = (await response.json()) as {
    response?: {
      GeoObjectCollection?: {
        featureMember?: Array<{
          GeoObject?: {
            Point?: { pos?: string };
            name?: string;
            description?: string;
            metaDataProperty?: {
              GeocoderMetaData?: {
                text?: string;
              };
            };
          };
        }>;
      };
    };
  };

  const featureMember = payload.response?.GeoObjectCollection?.featureMember?.[0]?.GeoObject;
  const point = featureMember?.Point?.pos;
  if (!point) {
    throw new Error("Unable to resolve coordinates for the specified address.");
  }

  const [lonStr, latStr] = point.split(" ");
  const lat = Number(latStr);
  const lon = Number(lonStr);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    throw new Error("Received invalid coordinates from geocoder.");
  }

  const label =
    featureMember?.metaDataProperty?.GeocoderMetaData?.text ??
    featureMember?.name ??
    featureMember?.description ??
    `${lat.toFixed(5)}, ${lon.toFixed(5)}`;

  return {
    lat,
    lon,
    label,
  };
}


async function reverseGeocode(lat: number, lon: number): Promise<string | null> {
  try {
    const apiKey = ensureYandexApiKey();
    const url = new URL("https://geocode-maps.yandex.ru/1.x/");
    url.searchParams.set("apikey", apiKey);
    url.searchParams.set("format", "json");
    url.searchParams.set("geocode", `${lon},${lat}`);
    url.searchParams.set("lang", "ru_RU");
    url.searchParams.set("kind", "house");
    url.searchParams.set("results", "1");

    const response = await fetch(url.toString());
    if (!response.ok) {
      return null;
    }
    const data = (await response.json()) as {
      response?: {
        GeoObjectCollection?: {
          featureMember?: Array<{
            GeoObject?: {
              metaDataProperty?: {
                GeocoderMetaData?: {
                  text?: string;
                };
              };
              name?: string;
              description?: string;
            };
          }>;
        };
      };
    };
    const featureMember = data.response?.GeoObjectCollection?.featureMember?.[0]?.GeoObject;
    return (
      featureMember?.metaDataProperty?.GeocoderMetaData?.text ??
      featureMember?.name ??
      featureMember?.description ??
      null
    );
  } catch {
    return null;
  }
}

function formatCurrency(value: string | number, currency: string) {
  const number = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(number)) {
    return value.toString();
  }
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(number);
}

export default function Home() {
  const { user, logout, apiFetch } = useAuth();

  const [vehicleTypes, setVehicleTypes] = useState<VehicleType[]>([]);
  const [vehicleTypesLoading, setVehicleTypesLoading] = useState(false);
  const [vehicleTypesError, setVehicleTypesError] = useState<string | null>(null);

  const [originQuery, setOriginQuery] = useState("");
  const [destinationQuery, setDestinationQuery] = useState("");
  const [origin, setOrigin] = useState<CoordPoint | null>(null);
  const [destination, setDestination] = useState<CoordPoint | null>(null);
  const [routeError, setRouteError] = useState<string | null>(null);
  const [distanceKm, setDistanceKm] = useState<number | null>(null);

  const [selectedVehicleTypeId, setSelectedVehicleTypeId] = useState<number | null>(null);
  const [priceByVehicle, setPriceByVehicle] = useState<Record<number, PriceQuote | null>>({});
  const [priceLoading, setPriceLoading] = useState(false);
  const [priceError, setPriceError] = useState<string | null>(null);

  const [weather, setWeather] = useState<WeatherInfo | null>(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState<string | null>(null);

  useEffect(() => {
    const loadTypes = async () => {
      try {
        setVehicleTypesLoading(true);
        const response = await apiFetch("vehicle-types/");
        const data = await parseResponse(response);
        if (!response.ok) {
          throw createApiError("Failed to load tariff list", response.status, data);
        }
        const items = Array.isArray(data)
          ? data
          : Array.isArray((data as any)?.results)
            ? (data as any).results
            : [];
        setVehicleTypes(items as VehicleType[]);
        setVehicleTypesError(null);
      } catch (error) {
        if (error instanceof Error) {
          setVehicleTypesError(error.message);
        } else {
          setVehicleTypesError("Failed to load tariff list");
        }
      } finally {
        setVehicleTypesLoading(false);
      }
    };

    loadTypes();
  }, [apiFetch]);


  const fetchWeather = useCallback(
    async (point: CoordPoint | null) => {
      if (!point) {
        setWeather(null);
        return;
      }
      setWeatherLoading(true);
      setWeatherError(null);

      try {
        const response = await apiFetch("weather/", {
          method: "POST",
          body: JSON.stringify({
            latitude: point.lat,
            longitude: point.lon,
          }),
        });
        const data = await parseResponse(response);
        if (!response.ok) {
          throw createApiError("Failed to fetch weather", response.status, data);
        }
        setWeather((data ?? null) as WeatherInfo | null);
      } catch (error) {
        setWeather(null);
        if (error instanceof Error) {
          setWeatherError(error.message);
        } else {
          setWeatherError("Failed to fetch weather");
        }
      } finally {
        setWeatherLoading(false);
      }
    },
    [apiFetch],
  );

  const fetchQuote = useCallback(
    async (vehicleTypeId: number, distance: number) => {
      if (!destination || !Number.isFinite(distance) || distance <= 0) {
        return;
      }
      setPriceLoading(true);
      setPriceError(null);
      setPriceByVehicle((prev) => ({ ...prev, [vehicleTypeId]: null }));

      try {
        const response = await apiFetch("pricing/estimate/", {
          method: "POST",
          body: JSON.stringify({
            vehicle_type: vehicleTypeId,
            distance_km: distance,
            latitude: destination.lat,
            longitude: destination.lon,
          }),
        });
        const data = await parseResponse(response);
        if (!response.ok) {
          throw createApiError("Failed to calculate price", response.status, data);
        }
        setPriceByVehicle((prev) => ({ ...prev, [vehicleTypeId]: data as PriceQuote }));
      } catch (error) {
        if (error instanceof Error) {
          setPriceError(error.message);
        } else {
          setPriceError("Failed to calculate price");
        }
      } finally {
        setPriceLoading(false);
      }
    },
    [apiFetch, destination],
  );

  useEffect(() => {
    if (!origin && typeof navigator !== "undefined" && "geolocation" in navigator) {
      let cancelled = false;

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          if (cancelled) {
            return;
          }
          const { latitude, longitude } = position.coords;
          const point: CoordPoint = {
            lat: latitude,
            lon: longitude,
            label: `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`,
          };

          setOrigin(point);
          setOriginQuery(`${DEFAULT_COUNTRY}, ${latitude.toFixed(6)}, ${longitude.toFixed(6)}`);

          const pretty = await reverseGeocode(latitude, longitude);
          if (!cancelled && pretty) {
            setOrigin({ lat: latitude, lon: longitude, label: pretty });
            setOriginQuery(pretty);
          }

          if (!cancelled) {
            fetchWeather(point);
          }
        },
        () => {
          /* user denied access */
        },
        { enableHighAccuracy: true, maximumAge: 30000, timeout: 15000 },
      );

      return () => {
        cancelled = true;
      };
    }
    return undefined;
  }, [origin, fetchWeather]);

  useEffect(() => {
    if (origin) {
      fetchWeather(origin);
    }
  }, [origin, fetchWeather]);


  const handleRouteSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (!originQuery.trim() || !destinationQuery.trim()) {
        setRouteError("Specify pick-up and drop-off addresses.");
        return;
      }
      setRouteError(null);
      setDistanceKm(null);
      setPriceByVehicle({});
      setPriceError(null);

      try {
        const [resolvedOrigin, resolvedDestination] = await Promise.all([
          geocode(originQuery),
          geocode(destinationQuery),
        ]);
        setOrigin(resolvedOrigin);
        setDestination(resolvedDestination);
        fetchWeather(resolvedOrigin);
      } catch (error) {
        if (error instanceof Error) {
          setRouteError(error.message);
        } else {
          setRouteError("Unable to build a route for the specified addresses.");
        }
      }
    },
    [originQuery, destinationQuery, fetchWeather],
  );

  const handleRouteReady = useCallback(
    (distance: number | null) => {
      const normalized =
        typeof distance === "number" && Number.isFinite(distance)
          ? Number(distance.toFixed(2))
          : null;
      setDistanceKm(normalized);

      if (normalized && normalized > 0 && selectedVehicleTypeId) {
        fetchQuote(selectedVehicleTypeId, normalized);
      }
    },
    [fetchQuote, selectedVehicleTypeId],
  );

  const handleTariffSelect = useCallback(
    (vehicleTypeId: number) => {
      setSelectedVehicleTypeId(vehicleTypeId);
      if (distanceKm && distanceKm > 0) {
        fetchQuote(vehicleTypeId, distanceKm);
      }
    },
    [distanceKm, fetchQuote],
  );

  const handleTariffKeyDown = useCallback(
    (event: KeyboardEvent<HTMLElement>, vehicleTypeId: number) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        handleTariffSelect(vehicleTypeId);
      }
    },
    [handleTariffSelect],
  );

  const currency = useMemo(() => {
    const quote = Object.values(priceByVehicle).find(Boolean);
    return quote?.currency ?? "RUB";
  }, [priceByVehicle]);

  const instructionMessage = useMemo(() => {
    if (!origin || !destination) {
      return "Specify pick-up and drop-off addresses.";
    }
    if (!distanceKm) {
      return "Build the route to calculate the distance.";
    }
    if (!selectedVehicleTypeId) {
      return "Choose a tariff to calculate the price.";
    }
    return null;
  }, [origin, destination, distanceKm, selectedVehicleTypeId]);

  const weatherSummary = useMemo(() => {
    if (weatherLoading) {
      return "Fetching weather...";
    }
    if (weatherError) {
      return weatherError;
    }
    if (!weather) {
      return null;
    }
    const parts: string[] = [];
    if (weather.condition) parts.push(`Condition: ${weather.condition}`);
    if (weather.temperature !== null && weather.temperature !== undefined) {
      parts.push(`Temperature: ${weather.temperature}°C`);
    }
    if (weather.feels_like !== null && weather.feels_like !== undefined) {
      parts.push(`Feels like: ${weather.feels_like}°C`);
    }
    if (weather.wind_speed !== null && weather.wind_speed !== undefined) {
      parts.push(`Wind: ${weather.wind_speed} m/s`);
    }
    if (weather.pressure_mm !== null && weather.pressure_mm !== undefined) {
      parts.push(`Pressure: ${weather.pressure_mm} mmHg`);
    }
    return parts.join("; ");
  }, [weather, weatherLoading, weatherError]);


  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="top-bar__brand">
          <h1>Tow Service</h1>
          <p>Hello, {user?.first_name || user?.phone || "client"}!</p>
        </div>
        <nav className="top-bar__actions">
          {user?.user_type === "OPERATOR" && (
            <Link to="/admin" className="nav-link">
              Admin panel
            </Link>
          )}
          <Link to="/playground" className="nav-link">
            Playground
          </Link>
          <button onClick={logout} className="nav-button">
            Logout
          </button>
        </nav>
      </header>

      <main className="home-layout">
        <section className="tariffs">
          <h2>Tariffs</h2>
          {vehicleTypesLoading && <p>Loading tariffs...</p>}
          {vehicleTypesError && <p className="error-message">{vehicleTypesError}</p>}
          {!vehicleTypesLoading && !vehicleTypesError && (
            <div className="tariff-grid">
              {vehicleTypes.map((type) => {
                const isSelected = selectedVehicleTypeId === type.id;
                const quote = priceByVehicle[type.id];
                const showPrice =
                  isSelected && !!distanceKm && !priceLoading && !!quote;

                return (
                  <article
                    key={type.id}
                    className={`tariff-card${isSelected ? " tariff-card--selected" : ""}`}
                    role="button"
                    tabIndex={0}
                    aria-pressed={isSelected}
                    onClick={() => handleTariffSelect(type.id)}
                    onKeyDown={(event) => handleTariffKeyDown(event, type.id)}
                  >
                    <h3>{type.name}</h3>
                    {type.description && <p>{type.description}</p>}
                    <p className="tariff-meta">
                      Base price: {formatCurrency(type.base_price, currency)}
                      <br />
                      + {formatCurrency(type.per_km_rate, currency)} per km
                    </p>
                    {isSelected && priceLoading && (
                      <p className="tariff-price">Calculating...</p>
                    )}
                    {showPrice && quote && (
                      <p className="tariff-price">
                        {formatCurrency(quote.price, quote.currency)}
                        <small> for {distanceKm} km</small>
                      </p>
                    )}
                  </article>
                );
              })}
              {vehicleTypes.length === 0 && !vehicleTypesLoading && (
                <p>No tariffs configured yet.</p>
              )}
            </div>
          )}
          {priceError && <p className="error-message">{priceError}</p>}
          {instructionMessage && <p className="info-message">{instructionMessage}</p>}
        </section>

        <section className="route-planner">
          <h2>Route</h2>
          <form className="route-form" onSubmit={handleRouteSubmit}>
            <label>
              Pick-up address
              <input
                type="text"
                value={originQuery}
                onChange={(event) => setOriginQuery(event.target.value)}
                placeholder="Moscow, Tverskaya 1"
              />
            </label>
            <label>
              Destination address
              <input
                type="text"
                value={destinationQuery}
                onChange={(event) => setDestinationQuery(event.target.value)}
                placeholder="Russia, Moscow, Varshavskoye highway 170"
              />
            </label>
            <button type="submit">Build route</button>
          </form>
          {routeError && <p className="error-message">{routeError}</p>}

          {origin && destination && (
            <div className="route-summary">
              <p>
                Start: <strong>{origin.label}</strong>
              </p>
              <p>
                Finish: <strong>{destination.label}</strong>
              </p>
              {distanceKm && (
                <p>
                  Distance: <strong>{distanceKm} km</strong>
                </p>
              )}
            </div>
          )}

          <div className="map-wrapper">
            <RoutePlannerMap
              origin={origin}
              destination={destination}
              onRouteReady={handleRouteReady}
              className="map-canvas"
            />
          </div>

          <div className="weather-panel">
            <h3>Weather at pick-up point</h3>
            {weatherSummary ? (
              <p>{weatherSummary}</p>
            ) : (
              <p>Weather data will appear after the pick-up point is determined.</p>
            )}
            {weatherError && <p className="error-message">{weatherError}</p>}
            {weatherLoading && <p>Fetching weather...</p>}
          </div>
        </section>
      </main>
    </div>
  );
}
