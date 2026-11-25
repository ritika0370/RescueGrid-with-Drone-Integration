"use client";

import { useMemo, useState, useRef } from "react";

type Incident = {
  id: string;
  location: string;
  category: string;
  description: string;
  affected: number;
  trapped: number;
  status: string;
  time: string;
  source: string;
  team: string;
};

const initialIncidents: Incident[] = [
  { id: "RG-001", location: "Sector 15, Sonipat", category: "Fire", description: "Building fire with people trapped on upper floors.", affected: 25, trapped: 5, status: "Pending", time: "09:10 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-002", location: "Murthal, Sonipat", category: "Road accident", description: "Multiple vehicle collision and injured passengers.", affected: 8, trapped: 1, status: "Assigned", time: "09:18 AM", source: "Phone report", team: "Medical Team A" },
  { id: "RG-003", location: "Kundli, Sonipat", category: "Flood", description: "Water entering residential streets.", affected: 40, trapped: 3, status: "Monitoring", time: "09:25 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-004", location: "Gohana, Sonipat", category: "Building collapse", description: "Partial building collapse; people may be under debris.", affected: 18, trapped: 8, status: "Drone assessment", time: "09:32 AM", source: "Control room", team: "Rescue Team B" },
  { id: "RG-005", location: "Rai, Sonipat", category: "Medical emergency", description: "Several people require immediate medical assistance.", affected: 4, trapped: 0, status: "Assigned", time: "09:40 AM", source: "Phone report", team: "Medical Team A" },
  { id: "RG-006", location: "Sector 14, Sonipat", category: "Fire", description: "Electrical fire reported near a commercial building.", affected: 12, trapped: 0, status: "Pending", time: "09:47 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-007", location: "Barhi, Sonipat", category: "Flood", description: "Waterlogging affecting homes and roads.", affected: 55, trapped: 6, status: "Assigned", time: "09:55 AM", source: "Control room", team: "Rescue Team C" },
  { id: "RG-008", location: "Kharkhoda, Sonipat", category: "Missing persons", description: "Two people reported missing after heavy rainfall.", affected: 2, trapped: 2, status: "Pending", time: "10:02 AM", source: "Phone report", team: "Unassigned" },
  { id: "RG-009", location: "Sector 23, Sonipat", category: "Road accident", description: "A fallen tree is blocking an emergency access road.", affected: 3, trapped: 0, status: "Monitoring", time: "10:12 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-010", location: "Sonipat Bypass", category: "Road accident", description: "Vehicle collision; injured passengers taken for treatment.", affected: 5, trapped: 0, status: "Resolved", time: "10:20 AM", source: "Control room", team: "Medical Team B" },
  { id: "RG-011", location: "Bahalgarh, Sonipat", category: "Smoke alert", description: "Smoke visible near a storage facility; verification needed.", affected: 0, trapped: 0, status: "Verification", time: "10:28 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-012", location: "Sector 12, Sonipat", category: "Water disruption", description: "Water supply interruption affecting residential area.", affected: 100, trapped: 0, status: "Monitoring", time: "10:35 AM", source: "Citizen portal", team: "Unassigned" },
  { id: "RG-013", location: "Sector 15, Sonipat", category: "Fire", description: "Another caller reports the same building fire and trapped residents.", affected: 20, trapped: 4, status: "Pending", time: "10:42 AM", source: "Phone report", team: "Unassigned" }
];

const teams = [
  { name: "Rescue Team A", skills: "Fire and evacuation", available: true },
  { name: "Rescue Team B", skills: "Building collapse and search", available: true },
  { name: "Rescue Team C", skills: "Flood and water rescue", available: true },
  { name: "Medical Team A", skills: "First aid and ambulance", available: true },
  { name: "Medical Team B", skills: "Medical support", available: false }
];

const initialResources = [
  { name: "Ambulances", count: 5, icon: "🚑" },
  { name: "Rescue boats", count: 4, icon: "🛶" },
  { name: "Medical kits", count: 35, icon: "🩺" },
  { name: "Food packages", count: 120, icon: "🍱" },
  { name: "Water supplies", count: 200, icon: "💧" },
  { name: "Rescue drones", count: 3, icon: "🚁" }
];

function getScore(incident: Incident) {
  let score = 0;

  score += Math.min(incident.trapped * 10, 50);
  score += Math.min(incident.affected * 0.5, 20);

  if (["Building collapse", "Fire"].includes(incident.category)) score += 20;
  if (incident.category === "Flood") score += 12;
  if (incident.category === "Medical emergency") score += 15;
  if (incident.status === "Resolved") score = 0;

  return Math.round(Math.min(score, 100));
}

function getPriority(score: number) {
  if (score >= 65) return "Critical";
  if (score >= 40) return "High";
  if (score >= 20) return "Medium";
  return "Low";
}

export default function CommandCenter() {
  const [incidents, setIncidents] = useState(initialIncidents);
  const [resources, setResources] = useState(initialResources);
  const [droneDeployed, setDroneDeployed] = useState(false);
  const [droneBattery, setDroneBattery] = useState(100);
  const [droneMission, setDroneMission] = useState("Standby");
  const [activeTab, setActiveTab] = useState("incidents");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [selectedId, setSelectedId] = useState("RG-001");

  // DRONE CAMERA STATES
  const videoRef = useRef<HTMLVideoElement>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const [cameraOn, setCameraOn] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
  const [cameraMessage, setCameraMessage] = useState(
    "Camera is currently off."
  );

  // START CAMERA
  async function startCamera() {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraMessage("Camera access is not supported by this browser.");
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: true,
      });

      cameraStreamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      setCameraOn(true);
      setCameraMessage("Camera connected successfully.");
    } catch (error) {
      console.error(error);
      setCameraMessage(
        "Camera access denied or camera is unavailable. Please allow camera permission."
      );
    }
  }

  // STOP CAMERA
  function stopCamera() {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }

    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOn(false);
    setCameraMessage("Camera turned off.");
  }

  // START VIDEO RECORDING
  function startRecording() {
    const stream = cameraStreamRef.current;

    if (!stream) {
      setCameraMessage("Please turn on the camera first.");
      return;
    }

    if (!window.MediaRecorder) {
      setCameraMessage("Video recording is not supported by this browser.");
      return;
    }

    try {
      const mimeType = [
        "video/webm;codecs=vp9,opus",
        "video/webm;codecs=vp8,opus",
        "video/webm",
      ].find((type) => MediaRecorder.isTypeSupported(type));

      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "video/webm",
        });

        const url = URL.createObjectURL(blob);

        setRecordedUrl((oldUrl) => {
          if (oldUrl) URL.revokeObjectURL(oldUrl);
          return url;
        });

        setRecording(false);
        setCameraMessage("Recording completed. Your video is ready.");
      };

      recorderRef.current = recorder;
      recorder.start();

      setRecording(true);
      setCameraMessage("Recording in progress...");
    } catch (error) {
      console.error(error);
      setCameraMessage("Unable to start recording.");
    }
  }

  // STOP VIDEO RECORDING
  function stopRecording() {
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.stop();
    }
  }

  // CAPTURE PHOTO
  function capturePhoto() {
    const video = videoRef.current;

    if (!video || !video.videoWidth) {
      setCameraMessage("Turn on the camera before capturing a photo.");
      return;
    }

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    if (!context) return;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const link = document.createElement("a");
    link.href = canvas.toDataURL("image/png");
    link.download = `RescueGrid-Photo-${Date.now()}.png`;
    link.click();

    setCameraMessage("Photo captured and downloaded.");
  }

  // DOWNLOAD RECORDED VIDEO
  function downloadRecording() {
    if (!recordedUrl) return;

    const link = document.createElement("a");
    link.href = recordedUrl;
    link.download = `RescueGrid-Recording-${Date.now()}.webm`;
    link.click();
  }

  const enriched = useMemo(() =>
    incidents.map(item => ({
      ...item,
      score: getScore(item),
      priority: getPriority(getScore(item))
    })).sort((a, b) => b.score - a.score),
    [incidents]
  );

  const selected = enriched.find(i => i.id === selectedId) || enriched[0];

  const criticalCount = enriched.filter(i => i.priority === "Critical" && i.status !== "Resolved").length;
  const resolvedCount = incidents.filter(i => i.status === "Resolved").length;
  const pendingCount = incidents.filter(i => i.status === "Pending").length;

  const duplicates = enriched.filter((incident, index) =>
    enriched.some((other, otherIndex) =>
      otherIndex !== index &&
      other.location === incident.location &&
      other.category === incident.category
    )
  );

  const filtered = enriched.filter(i => {
    const matchesSearch =
      i.location.toLowerCase().includes(search.toLowerCase()) ||
      i.category.toLowerCase().includes(search.toLowerCase()) ||
      i.id.toLowerCase().includes(search.toLowerCase());

    const matchesFilter = filter === "All" || i.priority === filter;
    return matchesSearch && matchesFilter;
  });

  function assignTeam(id: string) {
    const incident = incidents.find(i => i.id === id);
    if (!incident) return;

    const team = teams.find(t =>
      t.available &&
      ((incident.category === "Fire" && t.name === "Rescue Team A") ||
       (incident.category === "Flood" && t.name === "Rescue Team C") ||
       (incident.category === "Building collapse" && t.name === "Rescue Team B") ||
       (incident.category === "Medical emergency" && t.name === "Medical Team A") ||
       (t.name === "Rescue Team A"))
    );

    if (!team) {
      alert("No suitable available team found.");
      return;
    }

    setIncidents(current => current.map(i =>
      i.id === id ? { ...i, team: team.name, status: "Assigned" } : i
    ));
    alert(`${team.name} recommended and assigned in this demo.`);
  }

  function resolveIncident(id: string) {
    setIncidents(current => current.map(i =>
      i.id === id ? { ...i, status: "Resolved" } : i
    ));
  }

  function deployDrone() {
    if (droneBattery < 15) {
      alert("Drone battery is too low. Recharge before another mission.");
      return;
    }

    setDroneDeployed(true);
    setDroneMission("Mission in progress");
    setDroneBattery(current => Math.max(0, current - 15));
  }

  function completeDroneMission() {
    setDroneDeployed(false);
    setDroneMission("Mission completed – 2 possible persons detected");
  }

  function rechargeDrone() {
    setDroneBattery(100);
    setDroneMission("Standby");
    setDroneDeployed(false);
  }

  function useResource(index: number) {
    setResources(current => current.map((r, i) =>
      i === index ? { ...r, count: Math.max(0, r.count - 1) } : r
    ));
  }

  function addDemoIncident() {
    const id = `RG-${String(incidents.length + 1).padStart(3, "0")}`;
    const newIncident: Incident = {
      id,
      location: "Demo location, Sonipat",
      category: "Fire",
      description: "New simulated emergency created for demonstration.",
      affected: 10,
      trapped: 2,
      status: "Pending",
      time: "11:00 AM",
      source: "Simulation",
      team: "Unassigned"
    };

    setIncidents(current => [...current, newIncident]);
    setSelectedId(id);
  }

  return (<>
  <main className="rc-dashboard">
      <header className="rc-header">
        <div>
          <h1>🚨 RESCUEGRID</h1>
          <p>Emergency Command Center | AI-assisted disaster response</p>
        </div>
        <span className="rc-online">● SYSTEM ONLINE</span>
      </header>

      <nav className="rc-nav">
        <button onClick={() => setActiveTab("incidents")}>Incidents</button>
        <button onClick={() => setActiveTab("drone")}>Drone Operations</button>
        <button onClick={() => setActiveTab("resources")}>Resources</button>
        <button onClick={() => setActiveTab("analytics")}>Analytics</button>
      </nav>

      <section className="rc-stats">
        <div className="rc-card">
          <span>Total Incidents</span>
          <strong>{incidents.length}</strong>
        </div>
        <div className="rc-card">
          <span>Critical Incidents</span>
          <strong className="red">{criticalCount}</strong>
        </div>
        <div className="rc-card">
          <span>Pending Incidents</span>
          <strong className="orange">{pendingCount}</strong>
        </div>
        <div className="rc-card">
          <span>Resolved Incidents</span>
          <strong className="green">{resolvedCount}</strong>
        </div>
      </section>

      {activeTab === "incidents" && (
        <section className="rc-section">
          <div className="rc-heading">
            <div>
              <h2>Emergency Incident Management</h2>
              <p>Monitor and manage reported emergencies.</p>
            </div>
            <button className="rc-button" onClick={addDemoIncident}>
              + Add Demo Incident
            </button>
          </div>

          <div className="rc-toolbar">
            <input
              className="rc-input"
              placeholder="Search incidents..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="rc-input"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="All">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div className="rc-columns">
            <div className="rc-panel">
              <h3>Incident Reports</h3>
              {filtered.map((incident) => (
                <button
                  key={incident.id}
                  className="rc-incident"
                  onClick={() => setSelectedId(incident.id)}
                >
                  <strong>{incident.id} — {incident.category}</strong>
                  <span>{incident.location}</span>
                  <span>Priority: {incident.priority}</span>
                  <span>Status: {incident.status}</span>
                </button>
              ))}
              {filtered.length === 0 && <p>No incidents found.</p>}
            </div>

            <div className="rc-panel">
              <h3>Selected Incident Details</h3>
              {selected && (
                <>
                  <h2>{selected.category}</h2>
                  <p>{selected.description}</p>

                  <div className="rc-details">
                    <p><strong>ID:</strong> {selected.id}</p>
                    <p><strong>Location:</strong> {selected.location}</p>
                    <p><strong>People affected:</strong> {selected.affected}</p>
                    <p><strong>People trapped:</strong> {selected.trapped}</p>
                    <p><strong>Reported:</strong> {selected.time}</p>
                    <p><strong>Source:</strong> {selected.source}</p>
                    <p><strong>Team:</strong> {selected.team}</p>
                    <p><strong>Status:</strong> {selected.status}</p>
                    <p><strong>Priority:</strong> {selected.priority}</p>
                    <p><strong>Priority score:</strong> {selected.score}/100</p>
                  </div>

                  <h4>AI-Assisted Priority Score</h4>
                  <div className="rc-progress">
                    <div
                      className="rc-progress-fill"
                      style={{ width: `${selected.score}%` }}
                    />
                  </div>
                  <p className="rc-note">
                    Demonstration score based on people affected, trapped persons,
                    incident type and status. This is rule-based, not a trained AI model.
                  </p>

                  <div className="rc-actions">
                    <button
                      className="rc-button"
                      onClick={() => assignTeam(selected.id)}
                      disabled={selected.status === "Resolved"}
                    >
                      Assign Team
                    </button>
                    <button
                      className="rc-button green-button"
                      onClick={() => resolveIncident(selected.id)}
                      disabled={selected.status === "Resolved"}
                    >
                      Mark Resolved
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>

          <div className="rc-panel rc-bottom">
            <h3>Duplicate Incident Detection</h3>
            {duplicates.length > 0 ? (
              duplicates.map((incident) => (
                <p key={incident.id}>
                  ⚠ {incident.id} — {incident.category} at {incident.location}
                </p>
              ))
            ) : (
              <p>No possible duplicate reports found.</p>
            )}
          </div>
        </section>
      )}

      {activeTab === "drone" && (
        <>
          <section className="rc-section">
            <h2>Drone Operations Center</h2>
            <p>Simulated drone deployment and mission management.</p>

            <div className="rc-panel">
              <div className="rc-drone-icon">🚁</div>
              <h2>Rescue Drone RG-D01</h2>
              <p>Battery: {droneBattery}%</p>
              <div className="rc-progress">
                <div
                  className="rc-progress-fill"
                  style={{ width: `${droneBattery}%` }}
                />
              </div>
              <p>Mission: {droneMission}</p>
              <p>Status: {droneDeployed ? "Deployed" : "Standby"}</p>

              <div className="rc-actions">
                <button
                  className="rc-button"
                  onClick={deployDrone}
                  disabled={droneDeployed}
                >
                  Deploy Drone
                </button>
                <button
                  className="rc-button"
                  onClick={completeDroneMission}
                  disabled={!droneDeployed}
                >
                  Complete Mission
                </button>
                <button className="rc-button" onClick={rechargeDrone}>
                  Recharge Drone
                </button>
              </div>
              <p className="rc-note">
                This is a software simulation. It does not control a physical drone.
              </p>
            </div>
          </section>

          <section className="rc-section">
            <h2>Drone Camera & Recording</h2>
            <p>Live preview and recording using your laptop webcam.</p>

            <div className="rc-columns">
              <div className="rc-panel">
                <div className="rc-camera-screen">
                  <video
                    ref={videoRef}
                    autoPlay
                    muted
                    playsInline
                    className="rc-camera-video"
                  />
                  {!cameraOn && (
                    <div className="rc-camera-placeholder">
                      <span>📹</span>
                      <strong>Camera is off</strong>
                      <small>Turn on your camera to see the live feed.</small>
                    </div>
                  )}
                  {recording && (
                    <div className="rc-recording">● REC</div>
                  )}
                </div>

                <p className="rc-note">{cameraMessage}</p>

                <div className="rc-actions">
                  <button
                    className="rc-button"
                    onClick={startCamera}
                    disabled={cameraOn}
                  >
                    Turn Camera On
                  </button>
                  <button
                    className="rc-button"
                    onClick={stopCamera}
                    disabled={!cameraOn}
                  >
                    Turn Camera Off
                  </button>
                </div>

                <div className="rc-actions">
                  <button
                    className="rc-button green-button"
                    onClick={startRecording}
                    disabled={!cameraOn || recording}
                  >
                    Start Recording
                  </button>
                  <button
                    className="rc-button"
                    onClick={stopRecording}
                    disabled={!recording}
                  >
                    Stop Recording
                  </button>
                  <button
                    className="rc-button"
                    onClick={capturePhoto}
                    disabled={!cameraOn}
                  >
                    Capture Photo
                  </button>
                </div>
              </div>

              <div className="rc-panel">
                <h3>Recording Storage</h3>
                {recordedUrl ? (
                  <>
                    <video
                      src={recordedUrl}
                      controls
                      className="rc-recorded-video"
                    />
                    <button className="rc-button" onClick={downloadRecording}>
                      Download Recording
                    </button>
                  </>
                ) : (
                  <p>No recording available yet.</p>
                )}

                <div className="rc-note">
                  <p>Camera: Laptop webcam</p>
                  <p>Recording: {recording ? "In progress" : "Not recording"}</p>
                  <p>Video format: WebM</p>
                  <p>Photo format: PNG</p>
                </div>
              </div>
            </div>
          </section>
        </>
      )}

      {activeTab === "resources" && (
        <section className="rc-section">
          <h2>Emergency Resource Management</h2>
          <p>Monitor and manage available emergency resources.</p>

          <div className="rc-resource-grid">
            {resources.map((resource, index) => (
              <div className="rc-panel" key={resource.name}>
                <div className="rc-resource-icon">{resource.icon}</div>
                <h3>{resource.name}</h3>
                <strong className="rc-resource-count">{resource.count}</strong>
                <p>Available units</p>
                <button
                  className="rc-button"
                  onClick={() => useResource(index)}
                  disabled={resource.count === 0}
                >
                  Use One Unit
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {activeTab === "analytics" && (
        <section className="rc-section">
          <h2>Incident Analytics</h2>
          <p>Overview of reported emergencies and response progress.</p>

          <div className="rc-stats">
            <div className="rc-card">
              <span>Total Reports</span>
              <strong>{incidents.length}</strong>
            </div>
            <div className="rc-card">
              <span>Resolved</span>
              <strong>{resolvedCount}</strong>
            </div>
            <div className="rc-card">
              <span>Unresolved</span>
              <strong>{incidents.length - resolvedCount}</strong>
            </div>
            <div className="rc-card">
              <span>Possible Duplicates</span>
              <strong>{duplicates.length}</strong>
            </div>
          </div>

          <div className="rc-panel">
            <h3>Incident Category Breakdown</h3>
            {Array.from(new Set(incidents.map((i) => i.category))).map((category) => {
              const count = incidents.filter((i) => i.category === category).length;
              const percentage = incidents.length
                ? (count / incidents.length) * 100
                : 0;

              return (
                <div key={category} className="rc-analytics-row">
                  <span>{category} — {count}</span>
                  <div className="rc-progress">
                    <div
                      className="rc-progress-fill"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <button className="rc-button" onClick={() => window.print()}>
            Print Analytics Report
          </button>
        </section>
      )}

      <footer className="rc-footer">
        <h3>RESCUEGRID</h3>
        <p>AI-Assisted Emergency Response and Drone Integration Platform</p>
        <p>Hackathon Demonstration | Sonipat, Haryana</p>
        <small>Demonstration data is simulated. Verify emergencies through official channels.</small>
      </footer>
    </main>

    <style jsx global>{`
      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        background: #061411;
        color: #e4f3eb;
        font-family: Arial, Helvetica, sans-serif;
      }

      .rc-dashboard {
        max-width: 1450px;
        margin: auto;
        min-height: 100vh;
        padding: 25px;
        background: #061411;
      }

      .rc-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
        padding: 25px;
        border-radius: 12px;
        background: #12352b;
        border: 1px solid #315c49;
      }

      .rc-header h1 {
        margin: 0 0 10px;
        color: #76e3a8;
      }

      .rc-header p,
      .rc-section > p {
        color: #a5c2b2;
      }

      .rc-online {
        color: #75e3a4;
        font-size: 12px;
        font-weight: bold;
      }

      .rc-nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin: 20px 0;
      }

      .rc-nav button,
      .rc-button {
        padding: 11px 15px;
        border: 1px solid #39845e;
        border-radius: 7px;
        background: #1c6948;
        color: white;
        cursor: pointer;
        font-weight: bold;
      }

      .rc-nav button {
        background: #10251f;
        border-color: #315344;
      }

      .rc-nav button:hover,
      .rc-button:hover:not(:disabled) {
        filter: brightness(1.2);
      }

      .rc-button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .rc-stats {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 20px;
      }

      .rc-card,
      .rc-panel {
        padding: 20px;
        background: #0c211b;
        border: 1px solid #294c3d;
        border-radius: 10px;
        margin-bottom: 15px;
      }

      .rc-card span {
        display: block;
        color: #a5bcae;
        font-size: 13px;
        margin-bottom: 10px;
      }

      .rc-card strong {
        font-size: 27px;
      }

      .red { color: #ff7777; }
      .orange { color: #ffbd72; }
      .green { color: #6ee2a1; }

      .rc-section {
        margin: 22px 0;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #254538;
        background: #091c17;
      }

      .rc-heading {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
      }

      .rc-toolbar {
        display: flex;
        gap: 12px;
        margin: 20px 0;
      }

      .rc-input {
        width: 100%;
        padding: 12px;
        border-radius: 7px;
        border: 1px solid #315344;
        background: #071713;
        color: white;
      }

      .rc-columns {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 15px;
      }

      .rc-incident {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
        width: 100%;
        padding: 13px;
        margin: 8px 0;
        border: 1px solid #315344;
        border-radius: 7px;
        background: #10251f;
        color: white;
        text-align: left;
        cursor: pointer;
      }

      .rc-incident span,
      .rc-note {
        color: #a5bcae;
        font-size: 12px;
        line-height: 1.6;
      }

      .rc-details {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        font-size: 13px;
      }

      .rc-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 15px;
      }

      .green-button {
        background: #176b42;
      }

      .rc-progress {
        width: 100%;
        height: 9px;
        overflow: hidden;
        border-radius: 10px;
        background: #20382d;
        margin: 10px 0;
      }

      .rc-progress-fill {
        height: 100%;
        background: #66d99a;
        border-radius: 10px;
      }

      .rc-bottom {
        margin-top: 20px;
      }

      .rc-drone-icon {
        font-size: 65px;
        text-align: center;
        margin: 20px;
      }

      .rc-camera-screen {
        position: relative;
        width: 100%;
        aspect-ratio: 16 / 9;
        background: #020b0a;
        border: 1px solid #34534a;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .rc-camera-video {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .rc-camera-placeholder {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        gap: 10px;
        background: #071b1a;
        color: #a8c4b8;
        text-align: center;
      }

      .rc-camera-placeholder span {
        font-size: 38px;
      }

      .rc-camera-placeholder small {
        color: #819b90;
      }

      .rc-recording {
        position: absolute;
        top: 12px;
        left: 12px;
        padding: 7px 12px;
        background: #721f1f;
        color: white;
        border-radius: 5px;
      }

      .rc-recorded-video {
        display: block;
        width: 100%;
        max-height: 250px;
        margin: 15px 0;
        background: black;
      }

      .rc-note {
        margin: 12px 0;
      }

      .rc-camera-note {
        padding: 12px;
        margin-top: 15px;
        background: #10251f;
        border-radius: 8px;
      }

      .rc-resource-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 15px;
      }

      .rc-resource-grid .rc-panel {
        text-align: center;
      }

      .rc-resource-icon {
        font-size: 32px;
      }

      .rc-resource-count {
        display: block;
        font-size: 28px;
        color: #76e3a8;
      }

      .rc-analytics-row {
        margin: 18px 0;
      }

      .rc-footer {
        padding: 25px;
        text-align: center;
        color: #a5cae;
        font-size: 12px;
      }

      .rc-footer h3 {
        color: #76e3a8;
        letter-spacing: 2px;
      }

      @media (max-width: 800px) {
        .rc-dashboard {
          padding: 12px;
        }

        .rc-stats {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .rc-columns {
          grid-template-columns: 1fr;
        }

        .rc-resource-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }

      @media (max-width: 500px) {
        .rc-toolbar {
          flex-direction: column;
        }

        .rc-details {
          grid-template-columns: 1fr;
        }
        .rc-resource-grid {
          grid-template-columns: 1fr;
        }
      }

      @media print {
        body,
        .rc-dashboard {
          background: white !important;
          color: black !important;
        }

        .rc-nav,
        .rc-button {
          display: none !important;
        }
      }
    `}</style>
    </>
  );
}