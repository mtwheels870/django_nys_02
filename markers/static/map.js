const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });
// map.fitWorld();
const initial_position = [43, -76.2];
map.setView(initial_position, 10)
const layerGroup = L.layerGroup().addTo(map);
// …
async function load_markers() {
  const markers_url = `/api/markers/?in_bbox=${map
    .getBounds()
    .toBBoxString()}`;
  console.log("map.js:load_markers, url: " + markers_url)
  const response = await fetch(
    markers_url
  );
  const geojson = await response.json();
  return geojson;
}

async function render_markers() {
  console.log("map.js:render_markers")
  const markers = await load_markers();
  layerGroup.clearLayers();
  L.geoJSON(markers)
    .bindPopup(
      (layer) =>
        layer.feature.properties.name
    )
    .addTo(layerGroup);
}

map.on("moveend", render_markers)
