import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001";
const MAP_WIDTH = 1120;
const MAP_HEIGHT = 720;

const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
const trackKey = (source, target) => [source, target].sort().join("--");

function projectStation(station, bounds) {
  return {
    x: 90 + ((station.x - bounds.minX) / (bounds.maxX - bounds.minX)) * 930,
    y: 75 + ((bounds.maxY - station.y) / (bounds.maxY - bounds.minY)) * 560,
  };
}

function Icon({ name }) {
  const paths = {
    rail: "M4 5h16M6 5l3 14m9-14-3 14M7 9h10M8 13h8M9 17h6M5 21l4-4m10 4-4-4",
    play: "M8 5v14l11-7z",
    pause: "M8 5h3v14H8zm5 0h3v14h-3z",
    step: "M7 5v14l9-7zm10 0h2v14h-2z",
    reset: "M4 4v6h6M5.5 15a7 7 0 1 0 1.5-7",
    layers: "m12 3-9 5 9 5 9-5zm-9 9 9 5 9-5m-18 4 9 5 9-5",
    alert: "M12 3 2.8 20h18.4zm0 6v5m0 3v.1",
    close: "m6 6 12 12M18 6 6 18",
    zoomIn: "M12 8v8m-4-4h8m3 7-4-4m2-4a6 6 0 1 1-12 0 6 6 0 0 1 12 0",
    zoomOut: "M8 12h8m3 7-4-4m2-4a6 6 0 1 1-12 0 6 6 0 0 1 12 0",
    plus: "M12 5v14M5 12h14",
    clock: "M12 7v5l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  };

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}

function MetricCard({ label, value, detail, tone = "blue" }) {
  return (
    <div className={`metric-card metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

export default function App() {
  const [network, setNetwork] = useState(null);
  const [running, setRunning] = useState(true);
  const [selectedStation, setSelectedStation] = useState(null);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [selectedTrain, setSelectedTrain] = useState(null);
  const [showStress, setShowStress] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [cityChoice, setCityChoice] = useState("");
  const [trainForm, setTrainForm] = useState({
    train_id: "",
    source: "",
    destination: "",
    departure_in: 0,
    passengers: 120,
  });
  const [view, setView] = useState({ x: 0, y: 0, scale: 1 });
  const dragRef = useRef(null);
  const tickingRef = useRef(false);

  const request = useCallback(async (path, options) => {
    const response = await fetch(`${API_URL}${path}`, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `Server returned ${response.status}`);
    return data;
  }, []);

  const loadState = useCallback(async () => {
    try {
      setNetwork(await request("/state"));
      setError("");
    } catch {
      setError("Simulation server is offline. Start the FastAPI backend on port 8001.");
    }
  }, [request]);

  const tick = useCallback(async () => {
    if (tickingRef.current) return;
    tickingRef.current = true;
    try {
      const result = await request("/tick", { method: "POST" });
      setNetwork(result.state);
      setError("");
    } catch {
      setRunning(false);
      setError("Lost connection to the simulation server.");
    } finally {
      tickingRef.current = false;
    }
  }, [request]);

  useEffect(() => {
    // Initial synchronization with the external simulation service.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadState();
  }, [loadState]);

  useEffect(() => {
    if (!running) return undefined;
    const timer = window.setInterval(tick, 850);
    return () => window.clearInterval(timer);
  }, [running, tick]);

  const stationMap = useMemo(() => {
    if (!network) return new Map();
    const xs = network.stations.map((station) => station.x);
    const ys = network.stations.map((station) => station.y);
    const bounds = {
      minX: Math.min(...xs) - 1,
      maxX: Math.max(...xs) + 1,
      minY: Math.min(...ys) - 1,
      maxY: Math.max(...ys) + 1,
    };
    return new Map(
      network.stations.map((station) => [
        station.id,
        { ...station, ...projectStation(station, bounds) },
      ]),
    );
  }, [network]);

  const mapBounds = useMemo(() => {
    if (!network) return null;
    const xs = network.stations.map((station) => station.x);
    const ys = network.stations.map((station) => station.y);
    return {
      minX: Math.min(...xs) - 1,
      maxX: Math.max(...xs) + 1,
      minY: Math.min(...ys) - 1,
      maxY: Math.max(...ys) + 1,
    };
  }, [network]);

  const highlightedTracks = useMemo(() => {
    const train = network?.trains.find((item) => item.id === selectedTrain);
    if (!train) return new Set();
    return new Set(
      train.route.slice(0, -1).map((station, index) =>
        trackKey(station, train.route[index + 1]),
      ),
    );
  }, [network, selectedTrain]);

  const actOnTrack = async () => {
    if (!selectedTrack) return;
    const failing = selectedTrack.status !== "failed";
    setBusy(true);
    try {
      await request(failing ? "/fail-track" : "/repair-track", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source: selectedTrack.source,
          target: selectedTrack.target,
        }),
      });
      await loadState();
      setSelectedTrack((current) => current && {
        ...current,
        status: failing ? "failed" : "healthy",
      });
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const resetSimulation = async () => {
    setBusy(true);
    try {
      setNetwork(await request("/reset", { method: "POST" }));
      setSelectedTrack(null);
      setSelectedStation(null);
      setSelectedTrain(null);
      setRunning(false);
      setView({ x: 0, y: 0, scale: 1 });
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const addCity = async (randomCity = false) => {
    setBusy(true);
    try {
      const data = await request("/cities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: randomCity ? null : cityChoice || null }),
      });
      setNetwork(data);
      setCityChoice("");
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const addTrain = async (event) => {
    event.preventDefault();
    setBusy(true);
    try {
      const data = await request("/trains", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...trainForm,
          departure_in: Number(trainForm.departure_in),
          passengers: Number(trainForm.passengers),
        }),
      });
      setNetwork(data);
      setTrainForm((current) => ({ ...current, train_id: "" }));
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const zoom = (amount) => {
    setView((current) => ({
      ...current,
      scale: clamp(current.scale + amount, 0.8, 2.8),
    }));
  };

  const onWheel = (event) => {
    event.preventDefault();
    zoom(event.deltaY > 0 ? -0.12 : 0.12);
  };

  const onPointerDown = (event) => {
    if (event.target.closest("[data-interactive]")) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    dragRef.current = {
      pointerX: event.clientX,
      pointerY: event.clientY,
      viewX: view.x,
      viewY: view.y,
    };
  };

  const onPointerMove = (event) => {
    if (!dragRef.current) return;
    setView((current) => ({
      ...current,
      x: dragRef.current.viewX + event.clientX - dragRef.current.pointerX,
      y: dragRef.current.viewY + event.clientY - dragRef.current.pointerY,
    }));
  };

  if (!network) {
    return (
      <main className="loading-screen">
        <div className="loading-mark"><Icon name="rail" /></div>
        <h1>RailTwin is connecting</h1>
        <p>{error || "Loading the live railway graph..."}</p>
        {error && <button onClick={loadState}>Retry connection</button>}
      </main>
    );
  }

  const metrics = network.metrics;
  const critical = network.critical_stations[0];
  const activeStation = selectedStation && stationMap.get(selectedStation);
  const recommendation = metrics.failed_tracks
    ? `${metrics.failed_tracks} corridor incident detected. Services have been rerouted across healthy links.`
    : metrics.average_stress > 0.65
      ? "Elevated network load. Prioritize capacity around critical interchange stations."
      : "Network is stable. Predictive routing is balancing load across available corridors.";

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Icon name="rail" /></span>
          <div>
            <strong>RailTwin</strong>
            <span>Self-healing railway digital twin</span>
          </div>
        </div>
        <div className="topbar-status">
          <span className={`live-dot ${running ? "is-live" : ""}`} />
          {running ? "Simulation live" : "Simulation paused"}
          <span className="time-chip">{network.clock} · T+{network.time.toString().padStart(3, "0")}</span>
        </div>
      </header>

      <section className="dashboard">
        <aside className="sidebar">
          <div className="sidebar-heading">
            <span>Network overview</span>
            <small>Western-Central Zone</small>
          </div>

          <div className="metric-grid">
            <MetricCard
              label="Health score"
              value={`${Math.round(metrics.health_score)}%`}
              detail={metrics.health_score > 75 ? "Nominal" : "Needs attention"}
              tone={metrics.health_score > 75 ? "green" : "amber"}
            />
            <MetricCard
              label="Active trains"
              value={metrics.active_trains}
              detail={`${metrics.scheduled_trains} scheduled · ${network.trains.length} total`}
            />
            <MetricCard
              label="Avg. stress"
              value={`${Math.round(metrics.average_stress * 100)}%`}
              detail="Across all stations"
              tone="violet"
            />
            <MetricCard
              label="Track alerts"
              value={metrics.failed_tracks}
              detail={metrics.failed_tracks ? "Action required" : "All corridors clear"}
              tone={metrics.failed_tracks ? "red" : "green"}
            />
          </div>

          <section className="panel builder-panel">
            <div className="panel-title">
              <span>Network builder</span>
              <span className="ai-chip">{network.stations.length} cities</span>
            </div>
            <div className="builder-block">
              <label>Add a real city</label>
              <div className="inline-form">
                <select
                  value={cityChoice}
                  onChange={(event) => setCityChoice(event.target.value)}
                  disabled={!network.available_cities.length}
                >
                  <option value="">Select city</option>
                  {network.available_cities.map((city) => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
                <button
                  onClick={() => addCity(false)}
                  disabled={busy || !cityChoice}
                  title="Add selected city"
                ><Icon name="plus" /></button>
              </div>
              <button
                className="random-button"
                onClick={() => addCity(true)}
                disabled={busy || !network.available_cities.length}
              >
                Add random catalog city
              </button>
            </div>

            <form className="train-form" onSubmit={addTrain}>
              <label>Create train service</label>
              <input
                required
                placeholder="Train ID, e.g. RT108"
                value={trainForm.train_id}
                onChange={(event) => setTrainForm({ ...trainForm, train_id: event.target.value })}
              />
              <div className="form-pair">
                <select
                  required
                  value={trainForm.source}
                  onChange={(event) => setTrainForm({ ...trainForm, source: event.target.value })}
                >
                  <option value="">Origin</option>
                  {network.stations.map((station) => (
                    <option key={station.id} value={station.id}>{station.id}</option>
                  ))}
                </select>
                <select
                  required
                  value={trainForm.destination}
                  onChange={(event) => setTrainForm({ ...trainForm, destination: event.target.value })}
                >
                  <option value="">Destination</option>
                  {network.stations.map((station) => (
                    <option key={station.id} value={station.id}>{station.id}</option>
                  ))}
                </select>
              </div>
              <div className="form-pair">
                <label className="field-label">
                  Depart in ticks
                  <input
                    type="number"
                    min="0"
                    max="288"
                    value={trainForm.departure_in}
                    onChange={(event) => setTrainForm({ ...trainForm, departure_in: event.target.value })}
                  />
                </label>
                <label className="field-label">
                  Passengers
                  <input
                    type="number"
                    min="10"
                    max="2000"
                    value={trainForm.passengers}
                    onChange={(event) => setTrainForm({ ...trainForm, passengers: event.target.value })}
                  />
                </label>
              </div>
              <button className="create-service" disabled={busy}>
                <Icon name="rail" /> Create service
              </button>
            </form>
          </section>

          <section className="panel">
            <div className="panel-title">
              <span>Service timetable</span>
              <small>{network.trains.length}</small>
            </div>
            <div className="service-list">
              {network.trains.map((train) => (
                <button
                  className={`service-row ${selectedTrain === train.id ? "selected" : ""}`}
                  key={train.id}
                  onClick={() => setSelectedTrain(
                    selectedTrain === train.id ? null : train.id,
                  )}
                >
                  <span className={`train-badge train-${train.status}`} />
                  <span>
                    <strong>{train.id}</strong>
                    <small>{train.source} → {train.destination}</small>
                    <small className="schedule-line">
                      <Icon name="clock" /> {train.departure_time} → {train.arrival_time}
                    </small>
                  </span>
                  <em>{train.status.replace("_", " ")}</em>
                </button>
              ))}
            </div>
          </section>

          <section className="panel insight-panel">
            <div className="panel-title">
              <span>Self-healing insight</span>
              <span className="ai-chip">AI</span>
            </div>
            <p>{recommendation}</p>
            <div className="critical-row">
              <span>Critical interchange</span>
              <strong>{critical?.station || "None"}</strong>
            </div>
          </section>
        </aside>

        <section className="map-panel">
          <div
            className="map-canvas"
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={() => { dragRef.current = null; }}
            onPointerCancel={() => { dragRef.current = null; }}
          >
            <svg viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} role="img" aria-label="Interactive railway network map">
              <defs>
                <pattern id="minorGrid" width="32" height="32" patternUnits="userSpaceOnUse">
                  <path d="M32 0H0V32" fill="none" stroke="#d8e2e0" strokeWidth="0.6" />
                </pattern>
                <filter id="trackGlow" x="-40%" y="-40%" width="180%" height="180%">
                  <feGaussianBlur stdDeviation="5" result="blur" />
                  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                </filter>
                <filter id="stationShadow" x="-80%" y="-80%" width="260%" height="260%">
                  <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="#153e46" floodOpacity=".22" />
                </filter>
                <radialGradient id="stressHalo">
                  <stop offset="0" stopColor="#f45b69" stopOpacity=".34" />
                  <stop offset="1" stopColor="#f45b69" stopOpacity="0" />
                </radialGradient>
              </defs>

              <rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="#eef3ef" />
              <rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="url(#minorGrid)" opacity=".55" />
              <g className="terrain">
                <path d="M-40 600C130 480 180 560 320 470S560 420 710 510s230 80 450-20v250H-40z" />
                <path d="M-30 160C120 70 230 140 350 80s260-40 390 20 250 5 430-75" />
                <path d="M40 680C170 520 280 510 410 370S650 250 790 190s220-80 360-220" />
                <path d="M-20 360C180 330 250 210 430 250s250 25 380-80 210-90 340-40" />
              </g>

              <g transform={`translate(${view.x} ${view.y}) scale(${view.scale})`}>
                <g className="region-labels">
                  <text x="425" y="105">INDIA RAIL NETWORK</text>
                </g>

                <g className="roads">
                  <path d="M40 390Q240 280 430 300T780 205T1080 230" />
                  <path d="M200 680Q280 500 410 430T710 300" />
                  <path d="M110 120Q300 210 510 170T960 80" />
                </g>

                <g className="tracks">
                  {network.tracks.map((track) => {
                    const source = stationMap.get(track.source);
                    const target = stationMap.get(track.target);
                    const key = trackKey(track.source, track.target);
                    const selected = selectedTrack && trackKey(
                      selectedTrack.source,
                      selectedTrack.target,
                    ) === key;
                    const highlighted = highlightedTracks.has(key);
                    return (
                      <g
                        key={key}
                        data-interactive
                        className={`track ${track.status} ${selected ? "selected" : ""} ${highlighted ? "route-highlight" : ""}`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedTrack(track);
                          setSelectedStation(null);
                        }}
                      >
                        <line className="track-hitbox" x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
                        <line className="track-bed" x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
                        <line className="track-line" x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
                        {track.status === "failed" && (
                          <g transform={`translate(${(source.x + target.x) / 2} ${(source.y + target.y) / 2})`}>
                            <circle r="13" className="failure-pin" />
                            <path d="M-5-5 5 5M5-5-5 5" className="failure-x" />
                          </g>
                        )}
                      </g>
                    );
                  })}
                </g>

                {showStress && network.stations.map((station) => {
                  const point = stationMap.get(station.id);
                  return (
                    <circle
                      key={`stress-${station.id}`}
                      cx={point.x}
                      cy={point.y}
                      r={28 + station.stress * 34}
                      fill="url(#stressHalo)"
                      opacity={station.stress}
                      className="stress-halo"
                    />
                  );
                })}

                <g className="stations">
                  {network.stations.map((station) => {
                    const point = stationMap.get(station.id);
                    const selected = selectedStation === station.id;
                    const criticalStation = station.criticality > 0.2;
                    return (
                      <g
                        key={station.id}
                        data-interactive
                        className={`station ${selected ? "selected" : ""}`}
                        transform={`translate(${point.x} ${point.y})`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedStation(station.id);
                          setSelectedTrack(null);
                        }}
                      >
                        {criticalStation && <circle r="18" className="critical-ring" />}
                        <circle r={selected ? 11 : 8} className="station-node" />
                        <circle r="3" className="station-core" />
                        {showLabels && (
                          <g className="station-label" transform="translate(15 -13)">
                            <text>{station.id}</text>
                            <text y="14" className="station-meta">
                              {Math.round(station.stress * 100)}% stress
                            </text>
                          </g>
                        )}
                      </g>
                    );
                  })}
                </g>

                <g className="trains">
                  {network.trains.map((train) => {
                    const point = projectStation(train, mapBounds);
                    return (
                      <g
                        key={train.id}
                        data-interactive
                        className={`train-marker ${selectedTrain === train.id ? "selected" : ""} ${train.status}`}
                        transform={`translate(${point.x} ${point.y})`}
                        onClick={(event) => {
                          event.stopPropagation();
                          setSelectedTrain(train.id);
                        }}
                      >
                        <circle r="15" className="train-pulse" />
                        <circle r="10" className="train-circle" />
                        <path d="M-4-5h8v7l-2 3h-4l-2-3zm1 2h2v3h-2zm4 0h2v3H1z" />
                        <text x="15" y="4">{train.id}</text>
                      </g>
                    );
                  })}
                </g>
              </g>
            </svg>

            <div className="map-tools">
              <button onClick={() => zoom(0.2)} aria-label="Zoom in"><Icon name="zoomIn" /></button>
              <button onClick={() => zoom(-0.2)} aria-label="Zoom out"><Icon name="zoomOut" /></button>
              <button onClick={() => setView({ x: 0, y: 0, scale: 1 })} aria-label="Reset map view">1:1</button>
            </div>

            <div className="layer-control">
              <span><Icon name="layers" /> Map layers</span>
              <label>
                <input type="checkbox" checked={showStress} onChange={(event) => setShowStress(event.target.checked)} />
                Stress field
              </label>
              <label>
                <input type="checkbox" checked={showLabels} onChange={(event) => setShowLabels(event.target.checked)} />
                Station labels
              </label>
            </div>

            <div className="map-legend">
              <span><i className="legend-line healthy" /> Healthy</span>
              <span><i className="legend-line failed" /> Failed</span>
              <span><i className="legend-dot critical" /> Critical</span>
              <span><i className="legend-dot train" /> Train</span>
            </div>

            {(activeStation || selectedTrack) && (
              <div className="selection-card" data-interactive>
                <button className="close-button" onClick={() => {
                  setSelectedStation(null);
                  setSelectedTrack(null);
                }} aria-label="Close details"><Icon name="close" /></button>
                {activeStation ? (
                  <>
                    <span className="eyebrow">Station telemetry</span>
                    <h2>{activeStation.id}</h2>
                    <div className="detail-grid">
                      <span>Load<strong>{Math.round(activeStation.load)} / {activeStation.capacity}</strong></span>
                      <span>Stress<strong>{Math.round(activeStation.stress * 100)}%</strong></span>
                      <span>Risk<strong>{Math.round(activeStation.risk * 100)}%</strong></span>
                      <span>Criticality<strong>{activeStation.criticality.toFixed(2)}</strong></span>
                    </div>
                    <div className="bar"><i style={{ width: `${activeStation.stress * 100}%` }} /></div>
                  </>
                ) : (
                  <>
                    <span className="eyebrow">Track control</span>
                    <h2>{selectedTrack.source} - {selectedTrack.target}</h2>
                    <div className="track-facts">
                      <span>{selectedTrack.distance} km · {selectedTrack.travel_ticks * network.minutes_per_tick} min</span>
                      <span className={`status-pill ${selectedTrack.status}`}>{selectedTrack.status}</span>
                    </div>
                    <button
                      className={`incident-button ${selectedTrack.status === "failed" ? "repair" : ""}`}
                      onClick={actOnTrack}
                      disabled={busy}
                    >
                      <Icon name={selectedTrack.status === "failed" ? "reset" : "alert"} />
                      {selectedTrack.status === "failed" ? "Repair corridor" : "Inject track failure"}
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          <footer className="simulation-bar">
            <div className="playback">
              <button className="primary-control" onClick={() => setRunning(!running)}>
                <Icon name={running ? "pause" : "play"} />
                {running ? "Pause" : "Run"}
              </button>
              <button onClick={tick} disabled={running} title="Advance one simulation tick">
                <Icon name="step" /> Step
              </button>
              <button onClick={resetSimulation} disabled={busy}>
                <Icon name="reset" /> Reset
              </button>
            </div>
            <div className="timeline">
              <span>{network.clock}</span>
              <div className="timeline-track">
                <i style={{ width: `${(network.time % 100)}%` }} />
                <b style={{ left: `${(network.time % 100)}%` }} />
              </div>
              <span>+{100 * network.minutes_per_tick} min</span>
            </div>
            <div className="tick-rate">1 tick / 0.85 sec</div>
          </footer>
        </section>
      </section>

      {error && <div className="error-toast">{error}</div>}
    </main>
  );
}
